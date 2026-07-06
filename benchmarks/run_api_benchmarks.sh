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
    
    # Auto-detect the rental_network name
    NETWORK=$(docker network ls --format '{{.Name}}' | grep "rental_network" | head -n 1)
    
    if [ -n "$NETWORK" ]; then
        # Run wrk inside the docker network, pointing directly to the gateway container
        docker run --rm --network "$NETWORK" alpine sh -c "apk add --no-cache wrk > /dev/null && wrk -t$THREADS -c$CONCURRENCY -d$DURATION http://gateway:80$ENDPOINT" 2>&1
    else
        # Fallback if network not found
        docker run --rm alpine sh -c "apk add --no-cache wrk > /dev/null && wrk -t$THREADS -c$CONCURRENCY -d$DURATION $GATEWAY_URL$ENDPOINT" 2>&1
    fi
    echo ""
}

# Endpoints to benchmark
run_wrk "/api/auth/register/" "Auth - Register"
run_wrk "/api/auth/login/" "Auth - Login"
run_wrk "/api/listings/units/" "Listings - Get Units"
run_wrk "/api/buildings/api/" "Buildings - Get Buildings"
run_wrk "/api/applications/api/" "Applications - Get Applications"
run_wrk "/api/notifications/api/" "Notifications - Get Alerts"

echo "Benchmarks complete!"
