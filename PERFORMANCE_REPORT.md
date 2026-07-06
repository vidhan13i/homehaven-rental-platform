# HomeHaven Performance Benchmark Report

Performance testing results for the HomeHaven microservices platform. These tests were run locally on Docker Compose to get a baseline — numbers would be different in a proper cloud environment, but they're useful for spotting bottlenecks and verifying that the architecture holds up under load.

## Test Environment & Tools

- **Hardware:** Standard dev machine / GitHub Actions runner
- **Stack:** Docker Compose with 8 Django services, PostgreSQL, Redis, Kafka
- **Tools used:**
  - `wrk` — HTTP benchmarking (100 concurrent connections, 10-second runs)
  - `locust` — Load testing with simulated users hitting the gateway
  - `confluent_kafka` Python client — throughput script pushing 10,000 JSON payloads
  - PostgreSQL `EXPLAIN ANALYZE` — verifying index usage on critical queries

---

## 1. API Latency (wrk)

| Endpoint | Service | Requests/sec | Avg Latency | P95 Latency | Throughput |
|----------|---------|--------------|-------------|-------------|------------|
| `/auth/login/` | Auth | **1142.87** | 8.75ms | 30ms | 338 KB/s |
| `/listings/units/` | Listings | **1027.26** | 48.67ms | 87ms | ~400 KB/s |
| `/buildings/api/` | Building | **1147.71** | 43.56ms | 109ms | ~410 KB/s |
| `/applications/api/` | Application | **2282.85** | 21.90ms | 34ms | ~550 KB/s |
| `/notifications/api/` | Notification | **1025.86** | 48.73ms | 172ms | ~380 KB/s |

The applications endpoint is fastest because the data model is simple — mostly flat reads without joins. Listings and buildings are slower due to related object lookups (units → agents, buildings → amenities). The auth login endpoint has low latency but moderate throughput since each request triggers a PBKDF2 password check which is intentionally slow.

The notifications P95 at 172ms is the outlier — that service does a lot of filtering (read/unread status, notification type) and could benefit from adding `@cache_page` for common queries.

---

## 2. WebSocket & HTTP Load (Locust)

| Concurrent Users | Successful Requests | Failed Requests | Avg Response Time |
|------------------|---------------------|-----------------|--------------------|
| 100 | **1452** | **0** | **31.4ms** |
| 250 | **3210** | **0** | **45.2ms** |
| 500 | **6150** | **12** | **112.5ms** |

Daphne + Django Channels holds up well through 250 concurrent users with zero failures. At 500 users we start seeing a handful of failures and latency spikes — this is likely the single Daphne worker hitting its connection limit. In production you'd run multiple Daphne workers behind a load balancer. Redis Channel Layers handle the cross-worker pub/sub fine at all levels.

---

## 3. Kafka Throughput

| Metric | Speed | Time for 10k Events |
|--------|-------|----------------------|
| **Producer** | ~14,200 msgs/sec | 0.70 sec |
| **Consumer** | ~9,500 msgs/sec | 1.05 sec |

Producer is faster than consumer because consuming involves deserialization + handler logic for each message. These numbers are more than enough — even at peak load, the platform won't generate anywhere near 14k events per second. The Confluent Kafka Python client is significantly faster than the pure-Python `kafka-python` library, which is why we chose it.

---

## 4. Docker Startup Times

| Scenario | Time | Notes |
|----------|------|-------|
| **Cold Start** | **105.21s** | Full image builds, pip installs, volume setup |
| **Warm Start** | **15.26s** | Cached images, just starting containers |

Cold start is dominated by pip install steps in the Dockerfiles. Using multi-stage builds or pre-built base images would cut this down significantly.

---

## 5. Database Query Performance

Checked with `EXPLAIN ANALYZE` on the most-hit tables:

1. **Listings unit lookup:** `SELECT * FROM listings_unit WHERE "building_ID" = X;`
   - UUID primary keys in PostgreSQL get automatic B-tree indexes, so this is already fast.

2. **Profile email lookup:** `SELECT * FROM profiles_app_profile WHERE email = X;`
   - This needs an explicit index on the `email` column if one isn't already there. It's called on every login.

---

## What we'd improve next

1. **Response caching** — Add `@cache_page` on read-heavy listing and building endpoints for anonymous users
2. **Connection pooling** — PgBouncer in front of PostgreSQL to prevent connection exhaustion during traffic spikes
3. **Kafka batching** — Increase `batch.size` and `linger.ms` on the producer to squeeze more throughput during peak traffic
