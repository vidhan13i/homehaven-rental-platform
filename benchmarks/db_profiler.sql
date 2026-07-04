-- Database Profiling with EXPLAIN ANALYZE

-- 1. Benchmark fetching units for a specific building
EXPLAIN ANALYZE
SELECT * FROM listings_unit WHERE "building_ID" = '123e4567-e89b-12d3-a456-426614174000';

-- 2. Benchmark fetching user profiles by email
EXPLAIN ANALYZE
SELECT * FROM profiles_app_profile WHERE email = 'test@example.com';

-- 3. Benchmark fetching unread notifications for a user
EXPLAIN ANALYZE
SELECT * FROM notification_notification WHERE user_id = 'user123' AND is_read = false ORDER BY created_at DESC;

-- Note: The exact table names depend on Django's default app_model naming convention.
