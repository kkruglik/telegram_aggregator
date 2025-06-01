-- Migration: initial_schema
-- Version: 20250518204330
-- Created: 2025-05-18 20:43:30

-- Write your SQL migration here

-- Example operations:
-- CREATE TABLE new_table (...)
-- ALTER TABLE existing_table ADD COLUMN new_column VARCHAR(100)
-- ALTER TABLE existing_table DROP COLUMN old_column

CREATE TABLE IF NOT EXISTS users
(
    id BIGINT PRIMARY KEY UNIQUE,
    notification_time TIME,
    timezone VARCHAR(100) DEFAULT 'EET',
    is_premium BOOLEAN DEFAULT FALSE
);

-- Create feeds table
CREATE TABLE IF NOT EXISTS feeds
(
    id BIGINT PRIMARY KEY UNIQUE,
    channel_name VARCHAR(100)
);

-- Create content table
CREATE TABLE IF NOT EXISTS content
(
    post_id BIGINT PRIMARY KEY,
    text TEXT,
    summary TEXT,
    channel_id BIGINT REFERENCES feeds (id) ON DELETE CASCADE
);

-- Create users_feeds association table
CREATE TABLE IF NOT EXISTS users_feeds
(
    user_id BIGINT REFERENCES users (id) ON DELETE CASCADE,
    feed_id BIGINT REFERENCES feeds (id) ON DELETE CASCADE,
    CONSTRAINT user_feed_pk PRIMARY KEY (user_id, feed_id)
);
