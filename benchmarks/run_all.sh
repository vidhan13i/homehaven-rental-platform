#!/bin/bash

echo "Starting all benchmarks..."

echo "================================"
echo "      API BENCHMARKS (WRK)      "
echo "================================"
./benchmarks/run_api_benchmarks.sh > benchmarks/api_results.txt

echo "================================"
echo "    KAFKA THROUGHPUT (NATIVE)   "
echo "================================"
# Use the native kafka performance test tool inside the container
docker exec haven_kafka kafka-producer-perf-test --topic benchmark_events --num-records 10000 --record-size 100 --throughput -1 --producer-props bootstrap.servers=kafka:9092 > benchmarks/kafka_results.txt || echo "Kafka Producer Test Failed"

echo "================================"
echo "    DATABASE EXPLAIN ANALYZE    "
echo "================================"
# Run inside the postgres container
docker exec haven_db psql -U postgres -d rental_db -f /benchmarks/db_profiler.sql > benchmarks/db_results.txt || echo "DB Profile Skipped (volume missing?)"

echo "================================"
echo "    LOCUST WEBSOCKET / HTTP     "
echo "================================"
pip install locust > /dev/null 2>&1
locust -f benchmarks/locustfile.py --headless -u 100 -r 20 --run-time 10s --host=http://localhost:8000 > benchmarks/locust_results.txt 2>&1

echo "================================"
echo "         DOCKER STATS           "
echo "================================"
docker stats --no-stream > benchmarks/docker_stats.txt

echo "All benchmarks completed!"
