# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this project is

A Telegram bot built on `aiogram 3` + `SQLAlchemy 2.0` (async). It started
from a generic aiogram bot template (admin panel, channel-subscription
gate, broadcast/ads system, activity tracking) and is being turned into
"AI Uzumchi Bot" — a bot that classifies grape leaf diseases and vine
types from user-submitted photos and lets users discuss the diagnosis
with an LLM via text or voice. See [`docs/PLAN.md`](docs/PLAN.md) for the
product plan and what's still to be built; this file only covers
technical architecture. [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md)
covers the same architecture in more detail (table-heavy, agent-facing
reference) and should be kept in sync with this file.

## Commands

```bash
# install deps (note the misspelled filename — do not rename without checking CI/docs)
pip install -r requairments.txt

# run the bot (long-polling)
python app.py

# create a migration after changing models in db/models/
alembic revision --autogenerate -m "description"

# apply migrations
alembic upgrade head
```

There is no configured lint/test/build tooling in this repo currently —
don't assume `pytest`, `ruff`, etc. exist unless you add them yourself.

## Required environment variables (`.env`)

```
BOT_TOKEN=   # Telegram bot token from @BotFather
DB_URL=      # SQLAlchemy async DSN, e.g. postgresql+asyncpg://user:pass@host:5432/db
DEV_ID=      # numeric Telegram user id, used by handlers/dev
DEBUG=       # "1" to enable debug behavior, anything else = off
```

Loaded in `config.py` via `python-dotenv`. `BOT_TOKEN`/`DB_URL` are
required — the app throws at import time without them (`DEV_ID` is
`int()`-cast unconditionally too, so it must be set and numeric).

## Architecture

### Global singletons — `loader.py`

`bot`, `dp`, `db` are created once here. **Always import them from
`loader`** — never construct a second `Bot`/`Dispatcher`/`DataBase`.

### Entry point — `app.py`

Imports `middlewares` then `handlers` purely for their side effects
(registering middleware/routers onto `dp`). **Import order matters**:
middlewares must be registered before handlers are included, since
handlers rely on data (`session`, `user`) injected by middleware.

### Database layer — `db/`

- `db/base.py` — `Base(DeclarativeBase)`. Every ORM model must inherit
  from it so Alembic autogenerate can see it.
- `db/main.py` — `DataBase` class: owns the async `engine`,
  `session_maker`, and one repository instance per aggregate
  (`db.users`, `db.channels`, `db.stats`). This is the single façade for
  DB access, instantiated once as `db` in `loader.py`.
- `db/models/` — one file per ORM model (`user.py`, `channel.py`).
- `db/repositories/` — stateless query classes. Every method takes
  `session: AsyncSession` as the first argument and manages its own
  `commit()` — **repositories do not open/close sessions**, that's the
  middleware's job. Handlers must never issue SQLAlchemy queries
  directly; always go through a repository.
- `db/migrations/` — Alembic scripts. Import new models somewhere
  reachable from `env.py`'s metadata so autogenerate detects them.

**Adding a repository**: create `db/repositories/foo.py` with a
`FooRepository`, export it from `db/repositories/__init__.py`, then wire
it up as `self.foos = FooRepository()` in `DataBase.__init__`.

### Middleware pipeline — `middlewares/__init__.py`

Registered in this order, and the order is load-bearing:

1. `DbSessionMiddleware` (`dp.update`) — opens an `AsyncSession` for
   every update, injects it as `data["session"]`, closes it when the
   handler returns (success or error). Handlers never call
   `session.commit()`/`close()` themselves.
2. `UserMiddleware` (`dp.update`) — looks up `data["session"]`'s
   corresponding `User` row for `event_from_user`; if missing, creates
   one via `register_user()` and injects it as `data["user"]`. Depends on
   (1) already having set `data["session"]`.
3. `ActivityMiddleware` (`dp.update`) — throttled (60s in-memory cache)
   `last_used_at` bump per user.
4. `CheckSubscriptionMiddleware` (`dp.message` and `dp.callback_query`
   only, not all updates) — blocks interaction until the user has joined
   all channels in `db.channels`, with a 60s in-memory pass/fail cache
   per user/channel. Auto-deletes channels the bot can no longer see.

All four are registered at the `dp.update` (or `dp.message`/
`dp.callback_query`) level, not per-router — at that level
`data["handler"]` is aiogram's internal routing callable, not your
handler function, so **signature inspection to lazily skip work doesn't
work here**; middleware must unconditionally do its job (see comments in
`middlewares/db_sessions.py`/`user.py` if extending this pattern).

A handler opts into injected data purely by declaring matching
parameter names:
```python
async def my_handler(message: types.Message, session: AsyncSession, user: User):
    ...
```
Unused injected values are simply ignored — no need to declare them.

### Handlers — `handlers/`

Each subpackage owns one `Router`:
```python
# handlers/foo/__init__.py
from aiogram import Router
r = Router(name=__name__)
from . import some_module  # modules register handlers onto r via @r.message/@r.callback_query
```
`handlers/__init__.py` imports every subpackage's `r` and
`dp.include_router()`s it. Current routers: `register` (new/unregistered
users, `/start`), `admin` (admin panel + settings + ads + stats, FSM via
`states.py`), `dev` (developer-only), `channels` (subscription
gate/join-request handling).

**New handler group checklist**: create dir → `__init__.py` with
`r = Router(name=__name__)` → handler modules importing `r` from the
package → wire into `handlers/__init__.py`.

### FSM states — `states.py`

`StatesGroup` subclasses (`AdminPanel`, `AdsSending`) used with aiogram's
FSM (`state: FSMContext` param) for multi-step admin flows
(add/edit/remove channel, compose+confirm a broadcast).

### `buttons/`

`InlineButtons`/`InlineKeyboards` (`buttons/inline.py`) and `Keyboards`
(`buttons/keyboard.py`) — keyboard builders, imported by handlers/
middlewares that need to render a markup (e.g. the subscribe-to-channels
prompt in `CheckSubscriptionMiddleware`).

### `utils/`

Shared, dependency-light helpers: `broadcast.py` (ads sending),
`command.py` (per-scope bot command menus for admins vs. regular users),
`phone_router.py`. Put new pure helpers here unless they clearly belong
to a more specific package (e.g. future ML/LLM code, per
`docs/PLAN.md`).

## Conventions

- Async everywhere — handlers, repository methods, middleware are all
  `async def`.
- One DB session per update, owned by middleware — never manage
  sessions manually in a handler.
- All DB access goes through `db.<repo>` from `loader`, never raw
  SQLAlchemy in a handler.
- Side-effect imports wire up the app (`app.py` → `middlewares`,
  `handlers`) — don't move handler/middleware registration into
  explicit function calls without updating both entry points.
