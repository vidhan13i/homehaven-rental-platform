-- ─── init_db.sql ─────────────────────────────────────────────────────────────
-- This script runs ONCE when the PostgreSQL container starts for the first time.
-- It creates a separate database for each microservice.
-- 
-- Think of it like: one PostgreSQL SERVER hosting 5 separate databases.
-- Each Django service only connects to and reads/writes its own database.

CREATE DATABASE listings;
CREATE DATABASE profiles_app;
CREATE DATABASE application;
CREATE DATABASE building;
CREATE DATABASE reviews;
CREATE DATABASE auth_db;
CREATE DATABASE chat_db;
CREATE DATABASE notification_db;
