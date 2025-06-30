-- Migration: update_content_constaints
-- Version: 20250629213228
-- Created: 2025-06-29 21:32:28

-- Write your SQL migration here

-- Example operations:
-- CREATE TABLE new_table (...)
-- ALTER TABLE existing_table ADD COLUMN new_column VARCHAR(100)
-- ALTER TABLE existing_table DROP COLUMN old_column

-- Step 1: Drop the existing primary key constraint
ALTER TABLE content DROP CONSTRAINT content_pkey;

-- Step 2: Make sure both columns are NOT NULL (required for primary key)
ALTER TABLE content ALTER COLUMN post_id SET NOT NULL;
ALTER TABLE content ALTER COLUMN channel_id SET NOT NULL;

-- Step 3: Add the new composite primary key
ALTER TABLE content ADD CONSTRAINT content_pkey PRIMARY KEY (post_id, channel_id);
