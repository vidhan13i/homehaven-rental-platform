#!/bin/bash

# Configuration
CONCURRENCY=100
DURATION="10s"
THREADS=4
GATEWAY_URL="http://host.docker.internal:8000"

echo "=========================================="
echo "      HomeHaven API Benchmarks (WRK)      "
echo "=========================================="
echo "Concurrency: $CONCURRENCY | Duration: $DURATION | Threads: $THREADS"
echo ""

# Helper function
run_wrk() {
    ENDPOINT=$1
    NAME=$2
    echo "------------------------------------------"
    echo "Benchmarking: $NAME ($ENDPOINT)"
    echo "------------------------------------------"
    # Using williamyeh/wrk since it's reliable for docker-based wrk
    docker run --rm williamyeh/wrk -t$THREADS -c$CONCURRENCY -d$DURATION "$GATEWAY_URL$ENDPOINT"
    echo ""
}

# Endpoints to benchmark
run_wrk "/auth/register/" "Auth - Register"
run_wrk "/auth/login/" "Auth - Login"
run_wrk "/listings/units/" "Listings - Get Units"
run_wrk "/buildings/api/" "Buildings - Get Buildings"
run_wrk "/applications/api/" "Applications - Get Applications"
run_wrk "/notifications/api/" "Notifications - Get Alerts"

echo "Benchmarks complete!"
