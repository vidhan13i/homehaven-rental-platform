#!/bin/bash
echo "Listings Query:"
docker exec db psql -U postgres -d listings -c "EXPLAIN ANALYZE SELECT * FROM listings_unit WHERE \"id\" = '123e4567-e89b-12d3-a456-426614174000';"

echo ""
echo "Profile Query:"
docker exec db psql -U postgres -d profiles_app -c "EXPLAIN ANALYZE SELECT * FROM profiles_app_profile WHERE email = 'test@example.com';"

echo ""
echo "Notification Query:"
docker exec db psql -U postgres -d notification_db -c "EXPLAIN ANALYZE SELECT * FROM notification_preferences;"
