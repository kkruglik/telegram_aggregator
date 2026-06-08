-- Migration: add_timestamp_to_users_feeds_table
-- Version: 20250521205920
-- Created: 2025-05-21 20:59:20

-- Write your SQL migration here

-- Example operations:
-- CREATE TABLE new_table (...)
-- ALTER TABLE existing_table ADD COLUMN new_column VARCHAR(100)
-- ALTER TABLE existing_table DROP COLUMN old_column

ALTER TABLE users_feeds
ADD COLUMN created_at TIMESTAMP WITH TIME ZONE DEFAULT (CURRENT_TIMESTAMP AT TIME ZONE 'EET');