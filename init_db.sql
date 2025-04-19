CREATE TABLE IF NOT EXISTS users
(
    id                BIGINT PRIMARY KEY UNIQUE,
    lat               REAL,
    lon               REAL,
    notification_time TIME,
    timezone VARCHAR(100) DEFAULT 'EET'
);

CREATE TABLE IF NOT EXISTS feeds
(
    id           BIGINT PRIMARY KEY UNIQUE,
    channel_name VARCHAR(100)
);

CREATE TABLE IF NOT EXISTS content
(
    post_id    BIGINT PRIMARY KEY,
    text       TEXT,
    summary    TEXT,
    channel_id BIGINT REFERENCES feeds (id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS users_feeds
(
    user_id BIGINT REFERENCES users (id) ON DELETE CASCADE,
    feed_id BIGINT REFERENCES feeds (id) ON DELETE CASCADE,
    CONSTRAINT user_feed_pk PRIMARY KEY (user_id, feed_id)
);

INSERT INTO users(id, lat, lon, notification_time)
VALUES (1, 100.1, 100.2, '14:00'::TIME);

INSERT INTO feeds(id, channel_name)
VALUES (1, 'bbc'),
       (2, 'rfe');

INSERT INTO users_feeds(user_id, feed_id)
VALUES (1, 1),
       (1, 2);


DELETE FROM users_feeds WHERE user_id = 1 and feed_id = 1;

INSERT INTO users_feeds (user_id, feed_id)
VALUES (1, 1);
