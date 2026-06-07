# Feature: Per-feed keyword filtering

## Context

Users want to filter posts from a subscribed channel by keywords. When a keyword list is set for a subscription, only posts whose text contains at least one of those keywords reach the user's daily digest. Posts that don't match are silently skipped.

**Filtering happens at delivery time (`send_feed_update`), not before summarization.** Feeds are shared objects across all users — injecting per-user keyword logic into `TelegramFeed.update()` would break the shared cache model. Summarization results are stored in the DB and reused across users, so the waste is minimal. The user's actual goal — "don't receive irrelevant posts" — is fully satisfied at delivery.

---

## Data model

Add a `keywords TEXT[]` column to `users_feeds`. An empty array `'{}'` means no filter (all posts pass).

In-memory: `dict[int, list[str]]` on the `User` object, keyed by `channel_id`. Populated from the DB on startup alongside feed associations.

---

## Files to create

### 1. `services/aggregator/migrations/sql/20260526120000_add_keywords_to_users_feeds.sql`
```sql
ALTER TABLE users_feeds
ADD COLUMN IF NOT EXISTS keywords TEXT[] NOT NULL DEFAULT '{}';
```

### 2. `services/aggregator/src/app/bot/handlers/keywords.py`

New handler module:
- `/keywords` command → inline keyboard of user's subscribed feeds (same pattern as `create_unsubscribe_keyboard`)
- Callback `__kw__<channel_id>` → store `channel_id` in FSM data, ask user to type keywords comma-separated, or send `/clear` to remove them
- Text handler in `KeywordsStates.waiting_for_keywords` state → parse input, call `user.set_feed_keywords(channel_id, keywords)`, confirm

---

## Files to modify

### 3. `services/aggregator/src/app/bot/states.py`
Add:
```python
class KeywordsStates(StatesGroup):
    waiting_for_keywords = State()
```

### 4. `services/aggregator/src/app/bot/utils.py`
Add `create_keywords_feed_keyboard(feeds)` — same shape as `create_unsubscribe_keyboard` but uses `__kw__` prefix.

### 5. `services/aggregator/src/app/core/user.py`
- Add `_feed_keywords` to `__slots__`: `dict[int, list[str]]` (channel_id → keyword list)
- Init to `{}` in `__init__`
- Add `set_feed_keywords_in_memory(channel_id, keywords)` — updates in-memory dict only (used on startup)
- Add `set_feed_keywords(channel_id, keywords)` — updates in-memory dict + calls `DatabaseRepository.update_feed_keywords(user_id, channel_id, keywords)`
- In `send_feed_update()`: before appending each post, skip it if keywords are set and none match:
  ```python
  keywords = self._feed_keywords.get(feed.channel_id, [])
  if keywords and not any(kw.lower() in post_content["text"].lower() for kw in keywords):
      continue
  ```
- In `unsubscribe()`: also pop `self._feed_keywords.pop(channel_id, None)`

### 6. `services/aggregator/src/app/core/registry.py` — `_load_users_from_db()`
`get_user_feed_associations()` already returns all `users_feeds` rows. After adding the column, rows include `keywords`. Extend the loop (lines 47–55):
```python
keywords = list(row["keywords"] or [])
user.set_feed_keywords_in_memory(feed_id, keywords)
```

### 7. `services/aggregator/src/app/db/repository.py`
Add:
```python
@classmethod
async def update_feed_keywords(cls, user_id: int, channel_id: int, keywords: list[str]) -> Response:
    query = """
        UPDATE users_feeds
        SET keywords = $3
        WHERE user_id = $1 AND feed_id = $2
        RETURNING *
    """
    return await cls._execute_fetchrow(query, user_id, channel_id, keywords)
```

### 8. `services/aggregator/src/app/bot/handlers/__init__.py`
Add `from . import keywords` and `main_router.include_router(keywords.router)`.

### 9. `services/aggregator/src/app/utils/utils.py` — `set_bot_commands()`
Add: `BotCommand(command="keywords", description="Set keywords filter for a channel")`

---

## Keyword matching rules
- Case-insensitive substring: `kw.lower() in post_text.lower()`
- Any keyword match is sufficient (OR logic)
- Empty keyword list → no filter, all posts pass

---

## Verification

1. Run migrations: `make dev` spins postgres and runs migration manager on startup
2. Subscribe to a channel, set keywords via `/keywords`
3. Manually trigger `user.send_feed_update()` or wait for scheduled digest
4. Verify only matching posts appear; verify posts without keywords all appear when no filter is set
5. Run existing tests: `make test-agg`
