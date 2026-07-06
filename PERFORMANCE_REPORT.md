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

### Test 1: High Concurrency Read Operations

| Endpoint | Method | Expected Latency | Target Throughput | Actual Latency (Avg) | Actual Throughput (Req/Sec) | Pass/Fail |
|----------|--------|-----------------|-------------------|----------------------|-----------------------------|-----------|
| `/api/listings/units/` | GET | < 500ms | > 500 req/s | 752.45ms | 83.61 req/s | ⚠️ Failed |
| `/api/buildings/buildings/` | GET | < 500ms | > 500 req/s | 695.47ms | 127.33 req/s | ⚠️ Failed |
| `/api/applications/applications/` | GET | < 500ms | > 500 req/s | 343.59ms | 271.69 req/s | ⚠️ Failed |
| `/api/notifications/list/` | GET | < 500ms | > 500 req/s | 456.68ms | 217.95 req/s | ⚠️ Failed |

> **Note:** The actual latency and throughput values above reflect the unoptimized state of the application. The goal is to bring these closer to the target values using caching and database optimization techniques in future work.

## System Metrics During Test

| Metric | Average | Peak |
|--------|---------|------|
| CPU Usage | 45% | 85% |
| Memory Usage | 2.1 GB | 3.5 GB |
| DB Connections | 45 | 98 |

---

## 2. Simulated User Load (Locust)

| Concurrent Users | Successful Requests | Failed Requests | Avg Response Time |
|------------------|---------------------|-----------------|--------------------|
| 100 | **500** | **0 (0.00%)** | **186ms** |

*Note: Locust successfully simulated 100 concurrent users logging in and performing read operations (viewing applications, buildings, listings, and notifications). The API proved completely stable without any throttling or 502 Bad Gateway errors.*

---

## 3. Kafka Throughput

| Metric | Speed | Time for 10k Events |
|--------|-------|----------------------|
| **Producer** | ~27,548 msgs/sec | ~0.36 sec |
| **Consumer** | N/A | N/A |

Producer throughput on the internal Docker network is incredibly fast, pushing 27.5k messages per second (2.63 MB/sec) with an average latency of just 45ms. 

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

1. **Listings unit lookup:** `SELECT * FROM listings_unit WHERE id = X;`
   - Execution Time: **0.220 ms**
   - UUID primary keys in PostgreSQL get automatic B-tree indexes, making this look-up instantaneous via Index Scan.

2. **Profile email lookup:** `SELECT * FROM profiles_app_profile WHERE email = X;`
   - Execution Time: **0.061 ms**
   - The table uses a Seq Scan right now, which is fast given the small current dataset but needs an index as the table grows.
   
3. **Notification preferences lookup:** `SELECT * FROM notification_preferences;`
   - Execution Time: **0.028 ms**
   - Incredibly fast Seq Scan across the table.

---

## What we'd improve next

1. **Response caching** — Add `@cache_page` on read-heavy listing and building endpoints for anonymous users
2. **Connection pooling** — PgBouncer in front of PostgreSQL to prevent connection exhaustion during traffic spikes
3. **Kafka batching** — Increase `batch.size` and `linger.ms` on the producer to squeeze more throughput during peak traffic
