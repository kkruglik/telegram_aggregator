-- Migration: alter_users_tz_type
-- Version: 20250518204330
-- Created: 2025-05-21 20:20:30

-- Write your SQL migration here

-- Example operations:
-- CREATE TABLE new_table (...)
-- ALTER TABLE existing_table ADD COLUMN new_column VARCHAR(100)
-- ALTER TABLE existing_table DROP COLUMN old_column

ALTER TABLE users
ALTER COLUMN timezone TYPE VARCHAR(50);