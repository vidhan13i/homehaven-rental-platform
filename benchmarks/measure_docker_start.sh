#!/bin/bash

echo "=========================================="
echo "    HomeHaven Docker Startup Benchmark    "
echo "=========================================="
echo ""

echo "Taking down any existing containers..."
docker compose down -v > /dev/null 2>&1

echo "Measuring COLD START (with build)..."
TIMEFORMAT="Cold Start Time: %R seconds"
time {
    docker compose up --build -d > /dev/null 2>&1
}

echo ""
echo "Taking down containers..."
docker compose down > /dev/null 2>&1

echo "Measuring WARM START (without build)..."
TIMEFORMAT="Warm Start Time: %R seconds"
time {
    docker compose up -d > /dev/null 2>&1
}

echo ""
echo "Benchmarks complete!"
