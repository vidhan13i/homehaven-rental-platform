# shared_lib

Shared Python modules mounted into every microservice container via Docker volumes. This avoids duplicating common logic (Kafka, resilience, test fixtures) across 8+ services.

## Why a shared library instead of a pip package?

Publishing an internal pip package adds overhead — versioning, a package registry, rebuild cycles. Since all services run in Docker Compose on the same machine, we just mount this directory as a volume into each container. Changes are picked up immediately on restart. If we ever move to separate repos per service, we'd publish this as a proper package.

## Modules

### `resilience.py`

Wraps `requests` HTTP calls with Tenacity retry logic. Every inter-service call goes through `make_resilient_request()` which handles:

- **Exponential backoff** — wait time increases between retries so we don't hammer a recovering service
- **Selective retries** — only retries on transient failures (ConnectionError, Timeout, HTTP 429/500/502/503/504). Client errors like 400/404 fail immediately
- **Timeouts** — configurable per-call, defaults are tight (2s timeout, 2 max attempts) for user-facing requests
- **Logging** — logs each attempt with duration, status code, and service name

### `kafka/`

Centralized Kafka producer, consumer, event builder, and topic definitions.

| File | What it does |
|------|-------------|
| `producer.py` | Thread-safe singleton Kafka producer with idempotent delivery, compression, and batching |
| `consumer.py` | Base consumer class with manual offset commits (at-least-once delivery), dead letter queue routing, and graceful SIGTERM shutdown |
| `events.py` | `build_event()` helper that creates standardized event payloads with UUID, timestamp, and source service |
| `topics.py` | `Topics` enum — single source of truth for all topic names across services |

The producer uses `enable.idempotence=True` and `acks=all` for exactly-once delivery semantics per partition. Messages are compressed with snappy and batched (16KB batches, 5ms linger) for throughput.

The consumer disables auto-commit and only commits after successful processing — this gives at-least-once delivery. Failed messages are retried 3 times with backoff before being sent to the dead letter queue.

### `testing/`

Shared pytest fixtures used across all service test suites.

| Fixture | What it mocks |
|---------|--------------|
| `mock_kafka_producer` | Patches KafkaEventProducer so tests don't need a running Kafka broker |
| `mock_redis_cache` | Stubs Redis so tests run without a Redis instance |
| `mock_celery_task` | Intercepts `.delay()` calls to verify task dispatch without running workers |

These are `autouse` fixtures — they apply to every test automatically unless overridden.

## Directory Structure

```
shared_lib/
├── __init__.py
├── resilience.py          # HTTP retry wrapper (Tenacity)
├── kafka/
│   ├── __init__.py
│   ├── producer.py        # Kafka producer singleton
│   ├── consumer.py        # Base consumer with DLQ
│   ├── events.py          # Event payload builder
│   └── topics.py          # Topic name enum
└── testing/
    ├── __init__.py
    └── fixtures.py         # Shared pytest mocks
```

## How it's mounted

In `docker-compose.yml`, each service has:
```yaml
volumes:
  - ./shared_lib:/app/shared_lib
```

And the service's Python path includes the parent directory so `from shared_lib.resilience import make_resilient_request` works.
