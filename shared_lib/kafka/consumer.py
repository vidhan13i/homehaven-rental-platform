"""
Base Kafka Consumer
===================
Reusable base class for all Kafka consumers across the platform.

Design:
  - Each consumer runs in its own thread (or process via management command)
  - Automatic retry with configurable max attempts
  - Dead Letter Queue: failed messages after max retries → dlq.events topic
  - Idempotency: consumers must check event_id to avoid double-processing
  - Structured logging with event_id and correlation_id for tracing
  - Graceful shutdown via SIGTERM / KeyboardInterrupt
  - Commit offsets only AFTER successful processing (at-least-once semantics)

Usage:
    class MyConsumer(BaseKafkaConsumer):
        def handle(self, event: Dict) -> None:
            # Process the event
            pass

    consumer = MyConsumer(
        topics=["applications.application.approved"],
        group_id="notification-service-consumers",
    )
    consumer.start()  # blocks; runs forever until stop() is called
"""

import json
import logging
import os
import signal
import time
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

logger = logging.getLogger("kafka.consumer")

try:
    from confluent_kafka import Consumer, KafkaException, KafkaError, Message

    KAFKA_AVAILABLE = True
except ImportError:
    KAFKA_AVAILABLE = False


class BaseKafkaConsumer(ABC):
    """
    Abstract base consumer. Subclass and implement handle(event).
    """

    #: Max times to retry processing a single message before DLQ
    MAX_RETRIES: int = 3
    #: Seconds to wait between retry attempts
    RETRY_BACKOFF_SECONDS: float = 2.0
    #: Seconds to wait between poll calls when no messages available
    POLL_TIMEOUT_SECONDS: float = 1.0

    def __init__(
        self,
        topics: List[str],
        group_id: str,
        bootstrap_servers: Optional[str] = None,
    ):
        self.topics = topics
        self.group_id = group_id
        self.bootstrap_servers = bootstrap_servers or os.environ.get(
            "KAFKA_BOOTSTRAP_SERVERS", "kafka:9092"
        )
        self._enabled = os.environ.get("KAFKA_ENABLED", "true").lower() == "true"
        self._running = False
        self._consumer: Optional[Any] = None
        self._dlq_producer = None

        if self._enabled and KAFKA_AVAILABLE:
            self._init_consumer()
            self._init_dlq_producer()

    def _init_consumer(self) -> None:
        """Initialize the confluent-kafka Consumer."""
        config = {
            "bootstrap.servers": self.bootstrap_servers,
            "group.id": self.group_id,
            # Earliest: start from beginning if no committed offset exists.
            # Ensures no events are missed when a consumer starts fresh.
            "auto.offset.reset": "earliest",
            # Disable auto-commit: we commit only AFTER successful processing
            # This gives us at-least-once delivery semantics
            "enable.auto.commit": False,
            "auto.commit.interval.ms": 0,
            # Session timeout: broker marks consumer dead if no heartbeat
            "session.timeout.ms": 30000,
            "heartbeat.interval.ms": 10000,
            # Max messages fetched per poll
            "max.poll.interval.ms": 300000,
            "fetch.max.bytes": 52428800,  # 50MB
            "socket.timeout.ms": 10000,
        }
        try:
            self._consumer = Consumer(config)
            logger.info(
                "Kafka consumer initialized | group=%s | topics=%s",
                self.group_id,
                self.topics,
            )
        except KafkaException as exc:
            logger.error("Failed to initialize Kafka consumer: %s", exc)
            self._consumer = None

    def _init_dlq_producer(self) -> None:
        """Initialize a lightweight producer for Dead Letter Queue."""
        try:
            from confluent_kafka import Producer

            self._dlq_producer = Producer(
                {
                    "bootstrap.servers": self.bootstrap_servers,
                    "acks": "1",
                }
            )
        except Exception:
            self._dlq_producer = None

    def _send_to_dlq(self, raw_message: bytes, error_reason: str) -> None:
        """Send a failed message to the Dead Letter Queue topic."""
        from shared_lib.kafka.topics import Topics

        if not self._dlq_producer:
            logger.error(
                "DLQ producer unavailable. Failed message lost: %s", error_reason
            )
            return

        dlq_payload = json.dumps(
            {
                "original_message": raw_message.decode("utf-8", errors="replace"),
                "consumer_group": self.group_id,
                "error": error_reason,
                "timestamp": time.time(),
            }
        ).encode("utf-8")

        try:
            self._dlq_producer.produce(Topics.DLQ, value=dlq_payload)
            self._dlq_producer.flush(5)
            logger.warning(
                "Message sent to DLQ | group=%s | reason=%s",
                self.group_id,
                error_reason,
            )
        except Exception as exc:
            logger.error("Failed to send message to DLQ: %s", exc)

    def _process_message(self, msg: Any) -> None:
        """Parse, validate, and process a single Kafka message with retries."""
        raw_value = msg.value()

        # Step 1: Parse JSON
        try:
            event = json.loads(raw_value.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError) as exc:
            logger.error("Failed to deserialize message: %s", exc)
            self._send_to_dlq(raw_value, f"JSONDecodeError: {exc}")
            return

        # Step 2: Validate event envelope
        from shared_lib.kafka.events import validate_event

        if not validate_event(event):
            logger.error(
                "Invalid event envelope: missing required fields | event=%s", event
            )
            self._send_to_dlq(raw_value, "Invalid event envelope")
            return

        event_id = event.get("event_id", "unknown")
        event_type = event.get("event_type", "unknown")
        correlation_id = event.get("correlation_id", "unknown")

        logger.info(
            "Processing event | event_id=%s | type=%s | correlation_id=%s | group=%s",
            event_id,
            event_type,
            correlation_id,
            self.group_id,
        )

        # Step 3: Process with retry
        last_error = None
        for attempt in range(1, self.MAX_RETRIES + 1):
            try:
                self.handle(event)
                logger.info(
                    "Event processed successfully | event_id=%s | type=%s | attempt=%d",
                    event_id,
                    event_type,
                    attempt,
                )
                return  # Success — exit retry loop
            except Exception as exc:
                last_error = exc
                logger.warning(
                    "Event processing failed (attempt %d/%d) | event_id=%s | error=%s",
                    attempt,
                    self.MAX_RETRIES,
                    event_id,
                    exc,
                )
                if attempt < self.MAX_RETRIES:
                    time.sleep(self.RETRY_BACKOFF_SECONDS * attempt)

        # Step 4: All retries exhausted — send to DLQ
        logger.error(
            "Max retries exceeded | event_id=%s | type=%s | final_error=%s | sending to DLQ",
            event_id,
            event_type,
            last_error,
        )
        self._send_to_dlq(raw_value, f"MaxRetriesExceeded: {last_error}")

    def start(self) -> None:
        """
        Start the consumer loop. Blocks until stop() is called or SIGTERM received.
        Register signal handlers for graceful shutdown.
        """
        if not self._consumer:
            logger.error(
                "Consumer not initialized (Kafka unavailable?). Skipping start."
            )
            return

        # Register signal handlers for graceful Docker shutdown (SIGTERM)
        signal.signal(signal.SIGTERM, self._handle_shutdown_signal)
        signal.signal(signal.SIGINT, self._handle_shutdown_signal)

        self._consumer.subscribe(self.topics)
        self._running = True

        logger.info(
            "Consumer started | group=%s | topics=%s", self.group_id, self.topics
        )

        try:
            while self._running:
                msg = self._consumer.poll(timeout=self.POLL_TIMEOUT_SECONDS)

                if msg is None:
                    continue  # No message — poll again

                if msg.error():
                    if msg.error().code() == KafkaError._PARTITION_EOF:
                        # End of partition — not an error, just end of current data
                        continue
                    logger.error("Kafka consumer error: %s", msg.error())
                    continue

                try:
                    self._process_message(msg)
                    # Commit offset only after successful processing
                    self._consumer.commit(message=msg, asynchronous=False)
                except Exception as exc:
                    logger.error(
                        "Unhandled exception during message processing: %s", exc
                    )

        finally:
            self._shutdown()

    def stop(self) -> None:
        """Signal the consumer loop to stop gracefully."""
        logger.info("Stop requested for consumer group=%s", self.group_id)
        self._running = False

    def _handle_shutdown_signal(self, signum, frame) -> None:
        """Handle SIGTERM / SIGINT for graceful shutdown."""
        logger.info("Shutdown signal %d received. Stopping consumer...", signum)
        self.stop()

    def _shutdown(self) -> None:
        """Clean up resources on shutdown."""
        if self._consumer:
            logger.info("Closing Kafka consumer | group=%s", self.group_id)
            self._consumer.close()
        if self._dlq_producer:
            self._dlq_producer.flush(5)

    @abstractmethod
    def handle(self, event: Dict[str, Any]) -> None:
        """
        Process a single validated domain event.

        Implementations MUST be idempotent — the same event may be delivered
        more than once (at-least-once semantics). Use event['event_id'] as
        an idempotency key to detect and skip duplicates.

        Raises an exception to trigger retry logic.
        """
        raise NotImplementedError
