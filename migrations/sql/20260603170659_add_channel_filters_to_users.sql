-- Migration: add keywords to users feeds
-- Version: 20260603170659
-- Created: 2026-06-03 17:06:59

ALTER TABLE users
ADD COLUMN IF NOT EXISTS channel_filters JSONB NOT NULL DEFAULT '{}';
