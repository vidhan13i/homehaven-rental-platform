# HomeHaven Test Coverage Report

Overview of the automated testing setup across all services. Coverage percentages are approximate — measured locally with `pytest-cov`.

## Coverage by Service

| Service | Coverage | What's Tested |
|---------|----------|---------------|
| `auth_service` | ~85% | Models, serializers, registration/login API flows |
| `profile_service` | ~80% | Celery email tasks, models, OTP and profile API endpoints |
| `listings_service` | ~75% | Models, DRF viewset CRUD, JWT auth mocking |
| `application_service` | ~78% | API endpoints, Kafka producer mocking for events |
| `building_service` | ~70% | Models, API endpoints, filter logic |
| `reviews_service` | ~82% | API endpoints, Kafka event verification |
| `notification_service` | ~72% | Notification models, API alert endpoints |
| `chat_service` | ~88% | WebSocket consumers, auth middleware, REST views |
| **Overall** | **~78%** | Estimated average across all services |

## Test Infrastructure

We set up a shared test utilities package at `shared_lib/testing/` to avoid duplicating mock setup across services:

- **`mock_kafka_producer`** — Patches the Kafka producer so tests don't need a running broker. Lets us `assert_called_once()` on publish calls.
- **`mock_redis_cache`** — Stubs out Redis so tests run without a Redis instance. Important since the OTP flow and presence tracking both depend on Redis.
- **`mock_celery_task`** — Intercepts `.delay()` calls on Celery tasks so we can verify they were triggered without actually executing async workers.

These are implemented as pytest `autouse` fixtures, so every test gets them automatically unless explicitly overridden.

A shared `pytest.ini` standardizes the test runner config across services (test discovery paths, Django settings module, etc.).

## Gaps

A few areas that still need work:

- **No end-to-end tests** — We only have unit tests and single-service API tests. There's no test that hits the gateway and verifies the full flow across multiple services.
- **Kafka consumers aren't fully tested** — The `run_kafka_consumers.py` scripts in chat and notification services handle message ingestion, but the test coverage there is thin. The consumer logic (deserialization, handler dispatch, DLQ routing) is hard to test without an actual Kafka broker or a more sophisticated mock.
- **Edge cases in aggregations** — The Django ORM aggregation for building average ratings has minimal edge-case coverage (e.g., what happens when there are zero reviews, or when a review is deleted).

## Ideas for future tests

1. **WebSocket end-to-end** — Use `channels.testing.WebsocketCommunicator` to simulate a full send/receive loop between two users
2. **Contract tests** — Use Pact or a similar tool to verify the API contracts between services (e.g., what application_service expects from notification_service)
3. **Load tests** — Locust scripts to stress-test the chat WebSocket connections at scale
