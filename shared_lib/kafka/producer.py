"""
Kafka Event Producer
====================
Thread-safe, singleton-pattern Kafka producer shared across all services.

Design decisions:
  - Uses confluent-kafka (librdkafka C binding) — fastest Python Kafka client
  - Idempotent producer enabled (exactly-once delivery semantics for producers)
  - Synchronous flush with configurable timeout ensures delivery confirmation
  - Structured logging with correlation IDs for distributed tracing
  - Graceful shutdown via close() — always called in finally blocks
  - publish_async() for fire-and-forget (chat messages, logs)
  - publish() for synchronous confirmation (critical events like ApplicationApproved)

Usage:
    from shared_lib.kafka.producer import KafkaEventProducer
    from shared_lib.kafka.topics import Topics
    from shared_lib.kafka.events import build_event

    producer = KafkaEventProducer()
    event = build_event("UserRegistered", user_id, "auth_service", {"email": email})
    producer.publish(Topics.AUTH_USER_REGISTERED, event, key=str(user_id))
"""
import json
import logging
import os
from typing import Any, Callable, Dict, Optional

logger = logging.getLogger("kafka.producer")

# Lazy import so services that don't use Kafka don't fail on import
try:
    from confluent_kafka import Producer, KafkaException
    KAFKA_AVAILABLE = True
except ImportError:
    KAFKA_AVAILABLE = False
    logger.warning("confluent-kafka not installed. KafkaEventProducer will be a no-op.")


class KafkaEventProducer:
    """
    Thread-safe Kafka producer for publishing domain events.

    Designed as a lightweight wrapper — one instance per service process.
    Can be used as a context manager:

        with KafkaEventProducer() as producer:
            producer.publish(topic, event)
    """

    def __init__(self):
        self._producer: Optional[Any] = None
        self._bootstrap_servers = os.environ.get(
            "KAFKA_BOOTSTRAP_SERVERS", "kafka:9092"
        )
        self._enabled = os.environ.get("KAFKA_ENABLED", "true").lower() == "true"

        if self._enabled and KAFKA_AVAILABLE:
            self._init_producer()
        else:
            logger.info(
                "Kafka producer disabled or confluent-kafka not available. "
                "Events will be logged but not published."
            )

    def _init_producer(self) -> None:
        """Initialize the confluent-kafka Producer with production-grade settings."""
        config = {
            "bootstrap.servers": self._bootstrap_servers,
            # Idempotent producer: Kafka guarantees exactly-once delivery per partition
            "enable.idempotence": True,
            # Require acknowledgment from all in-sync replicas before confirming delivery
            "acks": "all",
            # Retry up to 5 times on transient failures (network blips, leader elections)
            "retries": 5,
            "retry.backoff.ms": 500,
            # Message compression reduces network I/O by ~70% for JSON payloads
            "compression.type": "snappy",
            # Batch up to 16KB of messages per partition for throughput
            "batch.size": 16384,
            # Wait up to 5ms to accumulate batch (reduces per-message overhead)
            "linger.ms": 5,
            # 32MB buffer before backpressure kicks in
            "queue.buffering.max.kbytes": 32768,
            # Socket timeouts
            "socket.timeout.ms": 10000,
            "message.timeout.ms": 30000,
        }
        try:
            self._producer = Producer(config)
            logger.info(
                "Kafka producer initialized. Bootstrap servers: %s",
                self._bootstrap_servers,
            )
        except KafkaException as exc:
            logger.error("Failed to initialize Kafka producer: %s", exc)
            self._producer = None

    def _delivery_callback(
        self,
        err: Optional[Any],
        msg: Any,
        on_success: Optional[Callable] = None,
        on_failure: Optional[Callable] = None,
    ) -> None:
        """Called by librdkafka after delivery confirmation or failure."""
        if err:
            logger.error(
                "Kafka delivery FAILED | topic=%s | partition=%s | error=%s",
                msg.topic(), msg.partition(), err
            )
            if on_failure:
                on_failure(err, msg)
        else:
            logger.debug(
                "Kafka delivery SUCCESS | topic=%s | partition=%s | offset=%s",
                msg.topic(), msg.partition(), msg.offset()
            )
            if on_success:
                on_success(msg)

    def publish(
        self,
        topic: str,
        event: Dict[str, Any],
        key: Optional[str] = None,
        flush_timeout: float = 10.0,
    ) -> bool:
        """
        Publish a domain event to a Kafka topic synchronously.

        Blocks until the message is confirmed delivered or timeout expires.
        Use for critical events (ApplicationApproved, UserRegistered).

        Args:
            topic:         Kafka topic name (use Topics constants)
            event:         Event dict built by build_event()
            key:           Partition key (aggregate_id recommended for ordering)
            flush_timeout: Max seconds to wait for delivery confirmation

        Returns:
            True on success, False on failure (logs error automatically)
        """
        if not self._producer:
            # Log the event even if Kafka is unavailable (dev fallback)
            logger.info(
                "KAFKA_NOOP | topic=%s | event_type=%s | aggregate_id=%s",
                topic,
                event.get("event_type"),
                event.get("aggregate_id"),
            )
            return False

        try:
            value = json.dumps(event, default=str).encode("utf-8")
            key_bytes = key.encode("utf-8") if key else None

            self._producer.produce(
                topic=topic,
                value=value,
                key=key_bytes,
                on_delivery=self._delivery_callback,
            )
            # Flush waits for all outstanding messages to be delivered
            remaining = self._producer.flush(flush_timeout)
            if remaining > 0:
                logger.warning(
                    "Kafka flush timeout: %d messages undelivered for topic=%s",
                    remaining, topic
                )
                return False

            logger.info(
                "Event published | topic=%s | event_type=%s | event_id=%s | aggregate_id=%s",
                topic,
                event.get("event_type"),
                event.get("event_id"),
                event.get("aggregate_id"),
            )
            return True

        except (KafkaException, BufferError) as exc:
            logger.error(
                "Failed to publish event | topic=%s | event_type=%s | error=%s",
                topic, event.get("event_type"), exc
            )
            return False
        except Exception as exc:
            logger.error(
                "Unexpected error publishing event | topic=%s | error=%s",
                topic, exc
            )
            return False

    def publish_async(
        self,
        topic: str,
        event: Dict[str, Any],
        key: Optional[str] = None,
    ) -> None:
        """
        Fire-and-forget: publish without waiting for confirmation.

        Use for high-volume, low-criticality events (MessageSent, heartbeats).
        Delivery is still guaranteed by Kafka's retry mechanism — we just
        don't block the calling thread waiting for confirmation.
        """
        if not self._producer:
            logger.info(
                "KAFKA_NOOP | topic=%s | event_type=%s",
                topic, event.get("event_type")
            )
            return

        try:
            value = json.dumps(event, default=str).encode("utf-8")
            key_bytes = key.encode("utf-8") if key else None
            self._producer.produce(
                topic=topic,
                value=value,
                key=key_bytes,
                on_delivery=self._delivery_callback,
            )
            # Poll for delivery callbacks without blocking
            self._producer.poll(0)
        except (KafkaException, BufferError) as exc:
            logger.error(
                "Async publish failed | topic=%s | error=%s", topic, exc
            )

    def close(self) -> None:
        """Flush all pending messages and close the producer. Call in shutdown hooks."""
        if self._producer:
            logger.info("Flushing Kafka producer before shutdown...")
            self._producer.flush(30)
            logger.info("Kafka producer closed.")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
