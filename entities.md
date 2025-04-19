Let me provide a clear recommendation for distributing responsibilities between entity classes and registry classes:

### Entity Classes (Feed, User)

**In Feed/TelegramFeed:**
- Individual state (channel_id, last_updated, content)
- Methods that act on a single feed instance:
  - `update()` - Update this feed's content
  - `get_content()` - Retrieve this feed's content
  - `get_new_content_since(timestamp)` - Get content newer than a timestamp
  - `summarize_content()` - Generate a summary for this feed

**In User:**
- Individual state (user_id, subscribed feeds)
- Methods that act on a single user:
  - `get_users_feeds()` - List feeds this user is subscribed to
  - `get_new_content()` - Get new content across all of this user's feeds

### Registry Classes (FeedsRegistry, UserRegistry)

**In FeedsRegistry:**
- Collection management (`_feeds`, `_feeds_users_count`)
- Entity lifecycle methods:
  - `create_or_get_feed()` - Create or retrieve a feed
  - `release_feed()` - Handle reference counting and cleanup
  - `delete_feed()` - Force delete a feed (administrative)
- Bulk operations:
  - `update_all_feeds()` - Update all feeds concurrently
  - `get_feed_stats()` - Get statistics about all feeds

**In UserRegistry:**
- Collection management (`_users`)
- Entity lifecycle methods:
  - `get_or_create_user()` - Create or retrieve a user
  - `delete_user()` - Delete a user and clean up subscriptions
- Bulk operations:
  - `notify_all_users()` - Send notifications to all users
  - `get_user_stats()` - Get statistics about all users

### Subscription Management

This is a relationship between users and feeds, so it could go in either place. For consistency with your current design:

**In User:**
- `subscribe(feed_name)` - Subscribe to a feed (calls FeedsRegistry.create_or_get_feed)
- `unsubscribe(feed_name)` - Unsubscribe from a feed (calls FeedsRegistry.release_feed)

### Update Management

**For individual updates:**
- `Feed.update()` - Update a single feed

**For bulk updates:**
- `FeedsRegistry.update_all_feeds()` - Update all feeds

**For user-specific updates:**
- Remove `User.update_users_feeds()` - This doesn't fit well with the pattern
- Add `UserRegistry.update_feeds_for_user(user_id)` - This aligns better with registry responsibilities

This structure provides a clean separation of responsibilities and follows consistent patterns across your codebase, making it more maintainable and easier to extend in the future.