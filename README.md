# AI Uzumchi Bot 🍇

A Telegram bot for grape growers ("uzumchi"). Users send a photo of a
grape leaf and the bot predicts whether it's diseased (and which
disease), predicts the vine variety, and lets the user chat with an LLM
(by text or voice) about the diagnosis and how to treat it.

This is currently an **MVP** — see [`docs/PLAN.md`](docs/PLAN.md) for the
full product plan and what's built vs. still to come. The underlying
bot infrastructure (admin panel, database layer, channel-subscription
gate, broadcast system, activity tracking) is already in place; see
[`CLAUDE.md`](CLAUDE.md) for the technical architecture.

## 🛠 Tech Stack

- **Framework:** `aiogram 3.x`
- **ORM:** `SQLAlchemy 2.0` (Async)
- **Database Engine:** PostgreSQL (`asyncpg`)
- **Migrations:** `alembic`
- **Language:** Python 3.11+

## 🚀 Running the project

### 1. Clone the repository
```bash
git clone <your-repository-url>
cd ai-uzumchi-bot
```

### 2. Set up a virtual environment
```bash
python -m venv .venv
source .venv/bin/activate      # Linux/macOS
# .\.venv\Scripts\activate     # Windows (PowerShell)
```

### 3. Install dependencies
```bash
pip install -r requairments.txt
```

### 4. Configure environment variables
Copy `.env.example` to `.env` and fill in the values:
```bash
cp .env.example .env
```
```env
BOT_TOKEN=your_bot_token_here          # from @BotFather
DB_URL=postgresql+asyncpg://user:password@localhost:5432/ai_uzumchi_bot
DEV_ID=your_telegram_user_id           # numeric, used by developer-only handlers
DEBUG=                                 # "1" to enable, otherwise leave empty
```
You'll need a running PostgreSQL instance reachable at `DB_URL`.

### 5. Run database migrations
```bash
alembic upgrade head
```
(If you've changed models and need a new migration:
`alembic revision --autogenerate -m "description"`.)

### 6. Start the bot
```bash
python app.py
```

## 📁 Project Structure Overview

- `app.py` — Main entry point to run the bot.
- `loader.py` — Initializes global singletons (`bot`, `dp`, `db`).
- `config.py` — Environment variable loader.
- `db/` — Database core, models, repositories, and Alembic migrations.
- `handlers/` — Route handlers grouped by feature (`register`, `admin`,
  `dev`, `channels`).
- `middlewares/` — Session injection, user lookup/registration, activity
  tracking, mandatory-channel-subscription gate.
- `buttons/` — Inline/reply keyboard builders.
- `utils/` — Shared helpers (broadcast sending, bot command menus, etc.).
- `docs/` — Product plan and other project docs.

## 📝 License
This project is open-source. Feel free to use and modify it for your own projects.
