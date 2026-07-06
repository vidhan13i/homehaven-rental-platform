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

# Get JWT Token for protected endpoints
TOKEN=""
# Try login first
LOGIN_RESP=$(curl -s -X POST http://localhost:8000/api/auth/login/ \
    -H "Content-Type: application/json" \
    -d '{"username":"benchmark_wrk","password":"password123"}')

TOKEN=$(echo $LOGIN_RESP | grep -o '"access":"[^"]*' | grep -o '[^"]*$')

if [ -z "$TOKEN" ]; then
    echo "Login failed, attempting to register..."
    curl -s -X POST http://localhost:8000/api/auth/register/ \
        -H "Content-Type: application/json" \
        -d '{"username":"benchmark_wrk","email":"benchmark_wrk@example.com","password":"password123","first_name":"Bench","last_name":"Mark"}' > /dev/null
    
    # Force verify email in the profile_service database
    echo "Force verifying email for benchmark user..."
    docker exec profile_service python manage.py shell -c "from profiles_app.models import Profile; p=Profile.objects.filter(userID='benchmark_wrk').first(); p.is_email_verified=True; p.save()" > /dev/null 2>&1
    
    # Try login again
    LOGIN_RESP=$(curl -s -X POST http://localhost:8000/api/auth/login/ \
        -H "Content-Type: application/json" \
        -d '{"username":"benchmark_wrk","password":"password123"}')
    TOKEN=$(echo $LOGIN_RESP | grep -o '"access":"[^"]*' | grep -o '[^"]*$')
fi

if [ -z "$TOKEN" ]; then
    echo "Warning: Failed to fetch JWT token. Protected endpoints may return 401. Response was: $LOGIN_RESP"
else
    echo "Successfully fetched JWT token."
fi

# Helper function
run_wrk() {
    ENDPOINT=$1
    NAME=$2
    METHOD=${3:-GET}
    echo "------------------------------------------"
    echo "Benchmarking: $NAME ($ENDPOINT)"
    echo "------------------------------------------"
    
    # Auto-detect the rental_network name
    NETWORK=$(docker network ls --format '{{.Name}}' | grep "rental_network" | head -n 1)
    
    AUTH_HEADER=""
    if [ -n "$TOKEN" ]; then
        AUTH_HEADER="-H \"Authorization: Bearer $TOKEN\""
    fi

    # Using eval to properly expand AUTH_HEADER with quotes
    if [ -n "$NETWORK" ]; then
        docker run --rm --network "$NETWORK" alpine sh -c "apk add --no-cache wrk > /dev/null && wrk -t$THREADS -c$CONCURRENCY -d$DURATION $AUTH_HEADER http://gateway:80$ENDPOINT" 2>&1
    else
        docker run --rm alpine sh -c "apk add --no-cache wrk > /dev/null && wrk -t$THREADS -c$CONCURRENCY -d$DURATION $AUTH_HEADER $GATEWAY_URL$ENDPOINT" 2>&1
    fi
    echo ""
}

# Endpoints to benchmark
run_wrk "/api/auth/register/" "Auth - Register" "POST"
run_wrk "/api/auth/login/" "Auth - Login" "POST"
run_wrk "/api/listings/units/" "Listings - Get Units"
run_wrk "/api/buildings/buildings/" "Buildings - Get Buildings"
run_wrk "/api/applications/applications/" "Applications - Get Applications"
run_wrk "/api/notifications/list/" "Notifications - Get Alerts"

echo "Benchmarks complete!"
