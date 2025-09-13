-- Initialize TLDRify Database
-- This script runs automatically when PostgreSQL container starts

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";  -- For text search

-- Create indexes for better performance (after tables are created by Alembic)
-- Note: These are suggestions, actual indexes will be created by SQLAlchemy

-- Grant permissions
GRANT ALL PRIVILEGES ON DATABASE tldrify_db TO tldrify_user;
GRANT ALL ON SCHEMA public TO tldrify_user;

-- Set default search path
ALTER DATABASE tldrify_db SET search_path TO public;

-- Performance tuning for development
ALTER SYSTEM SET shared_buffers = '256MB';
ALTER SYSTEM SET effective_cache_size = '1GB';
ALTER SYSTEM SET maintenance_work_mem = '64MB';
ALTER SYSTEM SET checkpoint_completion_target = 0.9;
ALTER SYSTEM SET wal_buffers = '16MB';
ALTER SYSTEM SET default_statistics_target = 100;
ALTER SYSTEM SET random_page_cost = 1.1;

-- Log slow queries for debugging (development only)
ALTER SYSTEM SET log_min_duration_statement = '1000';  -- Log queries slower than 1 second

SELECT pg_reload_conf();