# Registry DI Refactoring Plan

## Context

`FeedsRegistry` and `UserRegistry` are classmethod-based singletons that import `scraper_client` and `summarizer_client` as module-level globals. This made the scraper refactor painful and makes the code hard to test. The goal is to convert both registries to proper instantiable classes, wire everything in `main.py`, and inject them into aiogram handlers via `dp.start_polling()`.

`TelegramFeed` already follows the right pattern (injected constructor). `DatabaseRepository` stays as a classmethod singleton — justified, it wraps a shared connection pool.

---

## Changes

### 1. `core/user.py`
- Remove `_bot = None` class variable and `User.initialize(cls, bot)` classmethod
- Add `"_bot"` to `__slots__`
- Add `bot: Bot` as second positional arg in `__init__` (after `user_id`)
- Assign `self._bot = bot`

New signature:
```python
def __init__(self, user_id: int, bot: Bot, notification_time=None, timezone="EET", is_premium=False, channel_filters=None):
```

### 2. `core/registry.py`
Remove module-level singleton imports (`scraper_client`, `summarizer_client`). Convert both classes to instantiable.

**`FeedsRegistry.__init__`:**
```python
def __init__(self, scraper_client: TelegramScraperQueue, summarizer_client: SummarizeProtocol):
    self.feeds: dict[int, TelegramFeed] = {}
    self.feeds_users_count: dict[int, int] = {}
    self._scraper_client = scraper_client
    self._summarizer_client = summarizer_client
```
- All `@classmethod` → instance methods (`cls` → `self`)
- `normalize_channel_name` stays `@staticmethod`

**`UserRegistry.__init__`:**
```python
def __init__(self, bot: Bot, feeds_registry: FeedsRegistry):
    self._users: dict[int, User] = {}
    self._scheduler = TasksScheduler()
    self._bot = bot
    self._feeds_registry = feeds_registry
```
- All `@classmethod` → instance methods
- `FeedsRegistry.feeds` → `self._feeds_registry.feeds`
- Every `User(user_id, ...)` call → `User(user_id, self._bot, ...)`

### 3. `main.py`
```python
async def main():
    await DatabaseRepository.initialize(config.database.url)

    bot, dp = init_bot(config.bot.token)
    await set_bot_commands(bot)

    feeds_registry = FeedsRegistry(scraper_client, summarizer_client)
    await feeds_registry.initialize()

    user_registry = UserRegistry(bot=bot, feeds_registry=feeds_registry)
    await user_registry.initialize()

    await dp.start_polling(bot, user_registry=user_registry, feeds_registry=feeds_registry)
```
- Remove `User.initialize(bot=bot)`
- Add imports: `scraper_client` from `services.scraper`, `summarizer_client` from `services.summarizer`
- Remove import of `User`

### 4. Handler files (5 files)

Aiogram 3 resolves handler parameters **by name** from `start_polling` kwargs. Add registry params to each handler function that uses them. Remove classmethod-style calls.

**Pattern:**
```python
# Before
async def some_handler(message: Message, state: FSMContext):
    user = await UserRegistry.get_or_create_user(message.from_user.id)

# After
async def some_handler(message: Message, state: FSMContext, user_registry: UserRegistry):
    user = await user_registry.get_or_create_user(message.from_user.id)
```

Files and affected handlers:
- `registration.py` — `start`, `process_timezone`, `process_notification_time` → add `user_registry`
- `general.py` — `cmd_list`, `cmd_upgrade_premium` → add `user_registry`
- `debug.py` — `debug_trigger_feed_update` → add `user_registry`
- `keywords.py` — `cmd_keywords`, `process_keywords_feed`, `process_keywords_clear_callback`, `process_keywords_input` → add `user_registry`
- `subscription.py` — `process_feed_name`, `process_unsubscribe_callback` → add both; `cmd_unsubscribe` → add `user_registry`

Imports in handler files: keep `from ...core.registry import UserRegistry, FeedsRegistry` for type annotations — just stop calling classmethods on them.

---

## What NOT to change
- `DatabaseRepository` — stays classmethod singleton
- `TelegramFeed` — already correct, no changes
- `scraper_client` / `summarizer_client` module-level instances in their service files — kept, passed into `FeedsRegistry` from `main.py`
- `TasksScheduler` — no interface changes, `UserRegistry.__init__` creates it internally
- `bot.py`, handler routers — no structural changes

---

## Commit order
1. **Commit A**: `user.py` + `registry.py` together (tightly coupled — `registry.py` calls `User()`)
2. **Commit B**: `main.py` + all handler files together

---

## Verification
- `make ruff-check` — no import errors or undefined names
- Start the bot with `make dev` — should start, load feeds and users from DB
- Subscribe to a channel — exercises `FeedsRegistry.create_or_get_feed` and `UserRegistry.get_or_create_user`
- Receive a notification — exercises `User.send_feed_update` with injected bot
