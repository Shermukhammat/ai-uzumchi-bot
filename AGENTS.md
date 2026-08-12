# AGENTS.md — Project Reference for AI Agents

This file gives a fast overview of the project so an AI agent can understand the architecture, conventions, and key patterns without reading every file.

---

## Stack

| Component | Library / Version |
|-----------|------------------|
| Bot framework | `aiogram 3.28.2` |
| ORM | `SQLAlchemy 2.0` (async) |
| DB driver | `asyncpg 0.31.0` (PostgreSQL) |
| Migrations | `alembic 1.18.4` |
| Config | `python-dotenv 1.2.2` |
| Python | 3.11+ (async/await throughout) |

---

## Environment Variables (`.env`)

```
BOT_TOKEN=   # Telegram bot token from @BotFather
DB_URL=      # SQLAlchemy async DSN, e.g. postgresql+asyncpg://user:pass@host:5432/db
```

Loaded in [`config.py`](config.py) via `python-dotenv`. Both values are required — the app crashes without them.

---

## Entry Points

| File | Purpose |
|------|---------|
| [`app.py`](app.py) | Main entry point. Starts `dp.start_polling(bot)`. Importing `middlewares` and `handlers` registers everything as a side-effect. |
| [`loader.py`](loader.py) | Creates the three global singletons: `bot` (`Bot`), `dp` (`Dispatcher`), `db` (`DataBase`). Import from here — never recreate these objects. |
| [`config.py`](config.py) | Reads `BOT_TOKEN` and `DB_URL` from environment. Import constants from here. |

---

## Project Layout

```
aiogram-bot-template/
├── app.py                  # Entry point
├── loader.py               # Global singletons: bot, dp, db
├── config.py               # Env vars: BOT_TOKEN, DB_URL
│
├── db/                     # Database layer
│   ├── __init__.py         # re-exports DataBase
│   ├── base.py             # SQLAlchemy DeclarativeBase
│   ├── main.py             # DataBase class (engine + session_maker + repos)
│   ├── models/
│   │   └── user.py         # User ORM model
│   ├── repositories/
│   │   ├── __init__.py     # re-exports all repositories
│   │   └── user.py         # UserRepository (query methods)
│   └── migrations/         # Alembic migration scripts
│
├── middlewares/
│   ├── __init__.py         # Registers all middlewares onto dp
│   ├── db_sessions.py      # DbSessionMiddleware — injects AsyncSession into handlers
│   └── user.py             # UserMiddleware (planned) — injects User model into handlers
│
├── handlers/
│   ├── __init__.py         # Includes all routers into dp
│   ├── register/           # Handlers for new/unregistered users
│   │   ├── __init__.py     # Creates Router r = Router(name=__name__)
│   │   └── start.py        # /start command handler
│   └── admin/              # Admin-only handlers
│       └── __init__.py     # Creates Router r = Router(name=__name__)
│
└── utils/                  # Shared helpers (currently empty, add here)
    └── __init__.py
```

---

## Database Layer (`db/`)

### `DataBase` class — `db/main.py`

The single façade for all DB access. Instantiated once in `loader.py` as `db`.

```python
class DataBase:
    engine        # AsyncEngine (asyncpg)
    session_maker # async_sessionmaker — call as context manager: async with db.session_maker() as session
    users         # UserRepository instance
```

**Adding a new repository**: create `db/repositories/foo.py` with a `FooRepository` class, export it from `db/repositories/__init__.py`, then add `self.foos = FooRepository()` in `DataBase.__init__`.

### `Base` — `db/base.py`

`DeclarativeBase` subclass. All ORM models must inherit from it so Alembic can detect them.

### Models — `db/models/`

Each model file defines one SQLAlchemy ORM class. Current models:

#### `User` (`db/models/user.py`)

| Column | Type | Notes |
|--------|------|-------|
| `id` | `BigInteger` PK | Telegram user ID |
| `username` | `String(255)` nullable | `@username` |
| `first_name` | `String(255)` | Required |
| `last_name` | `String(255)` nullable | |
| `is_active` | `Boolean` | Default `True` |
| `registered_at` | `DateTime` | Set on insert via `func.now()` |
| `last_used_at` | `DateTime` | Should be updated on each interaction |

### Repositories — `db/repositories/`

Stateless query classes. Each method receives an `AsyncSession` as its first argument — **they do not create sessions themselves**.

#### `UserRepository`

| Method | Signature | Returns |
|--------|-----------|---------|
| `get` | `(session, id: int)` | `User \| None` |
| `get_all` | `(session)` | `Sequence[User]` |

**Pattern for new methods**: follow the same pattern — accept `session: AsyncSession`, use `select()` / `insert()` / `update()`, return typed results.

### Migrations — `db/migrations/`

Managed by Alembic (`alembic.ini` in project root).

```bash
# Generate a new migration after changing models
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head
```

> **Important**: import all models in `db/models/__init__.py` (or the Alembic `env.py`) so autogenerate can detect them.

---

## Middlewares (`middlewares/`)

Registered globally in `middlewares/__init__.py` on `dp.update.middleware` (runs before every update).

### `DbSessionMiddleware` — `middlewares/db_sessions.py`

**What it does**: opens an `AsyncSession` for **every** update and injects it as `data["session"]`. The session is kept open for the full handler call and closed (connection returned to the asyncpg pool) when the handler returns, even on error.

**Why no lazy inspection**: at the `dp.update` middleware level, `data["handler"].callback` is aiogram's internal routing handler — not the user-defined handler. Inspecting its signature would never find `session`, so all handlers would be skipped. Always injecting is the correct approach here.

**Usage in a handler**:
```python
async def my_handler(message: types.Message, session: AsyncSession):
    user = await db.users.get(session, message.from_user.id)
```

Handlers that don't declare `session` simply ignore the injected value — no harm done.

### `UserMiddleware` — `middlewares/user.py`

**What it does**: for every update that has a sender (`event_from_user`), looks up the `User` row and injects it as `data["user"]`. If the user is not found it calls `register_user()` to create and persist a new row, then injects the freshly created instance. Anonymous updates (channel posts with no sender) are skipped silently.

**Session dependency**: reads `data["session"]` set by `DbSessionMiddleware` — does not open its own session. `DbSessionMiddleware` must be registered first.

**Why no lazy inspection**: same reason as `DbSessionMiddleware` — at the `dp.update` middleware level the callable in `data["handler"]` is aiogram-internal, not the user-defined handler.

**`register_user(session, tg_user, db)`**: a thin helper that inserts the user row and immediately sends a welcome message via `bot.send_message`. Expand it in the future to:
- Set an FSM state for a multi-step registration form.
- Send a richer onboarding message or show a reply keyboard.
- Grant default roles/permissions.

**Usage in a handler**:
```python
async def my_handler(message: types.Message, session: AsyncSession, user: User):
    await message.answer(f"Hello again, {user.first_name}!")
```

Handlers that don't declare `user` simply ignore the injected value.


---

## Handlers (`handlers/`)

### Router convention

Each sub-package creates its own `Router` in `__init__.py`:

```python
from aiogram import Router
r = Router(name=__name__)
```

Handler modules inside the package import `r` from the package init and decorate functions with `@r.message(...)`, `@r.callback_query(...)`, etc.

The top-level `handlers/__init__.py` includes all routers into `dp`.

### Adding a new handler group

1. Create a new directory under `handlers/` (e.g. `handlers/payments/`).
2. Add `__init__.py` that creates `r = Router(name=__name__)`.
3. Add handler modules that import `r` from the package and register routes.
4. In `handlers/__init__.py`, import and include the new router: `dp.include_router(payments_router)`.

### Current routers

| Router | Module | Registered handlers |
|--------|--------|---------------------|
| `register_router` | `handlers/register/` | `/start` command |
| `admin_router` | `handlers/admin/` | *(empty — add admin commands here)* |

---

## Globals (`loader.py`)

```python
from loader import bot, dp, db
```

| Symbol | Type | Description |
|--------|------|-------------|
| `bot` | `aiogram.Bot` | Telegram bot instance |
| `dp` | `aiogram.Dispatcher` | Central dispatcher, holds all routers and middleware |
| `db` | `DataBase` | Database façade with `session_maker` and all repositories |

**Never** instantiate these again elsewhere — always import from `loader`.

---

## Conventions & Patterns

- **Async everywhere** — all handlers, repository methods, and middleware are `async def`.
- **Session lifetime = one update** — `DbSessionMiddleware` opens and closes a session per update, so handlers never manage sessions manually (no `session.commit()` or `session.close()` in handlers).
- **Repository pattern** — DB queries live exclusively in `db/repositories/`. Handlers never call SQLAlchemy directly.
- **Side-effect imports** — importing `middlewares` and `handlers` in `app.py` registers everything. The order matters: middlewares first, then handlers.
- **`utils/`** — place shared pure helpers (formatters, validators, keyboards, etc.) here. Keep it dependency-light.
