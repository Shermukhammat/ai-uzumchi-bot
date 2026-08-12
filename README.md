# Aiogram Bot Template 🚀

A professional and ready-to-use template for quickly developing Telegram bots using `aiogram 3.x` and `SQLAlchemy`. 

This template is designed to save you time by providing pre-built foundational features so you don't have to build a database or write standard bot features from scratch. It's fully open-source and perfect for building scalable, database-driven Telegram bots out of the box.

## ✨ Features Included

- **Database Architecture Pre-configured:** Built with `SQLAlchemy 2.0` (async) and `asyncpg` (PostgreSQL), along with `Alembic` for migrations.
- **Admin Panel:** A dedicated admin interface to manage the bot directly from Telegram.
- **Ads / Broadcasting System:** Built-in tools for admins to send broadcast messages and advertisements to all users.
- **Mandatory Channel Subscription:** Force users to subscribe to specific channels/groups before they can use the bot.
- **Bot Statistics:** Live statistics for admins showing total users, new joins, and active users (filtered by today, this week, and this month).
- **Middleware Integration:** Ready-to-use middlewares for session handling and user tracking (automatically tracking users' `last_used_at` fields).

## 🛠 Tech Stack

- **Framework:** `aiogram 3.x`
- **ORM:** `SQLAlchemy 2.0` (Async)
- **Database Engine:** PostgreSQL (`asyncpg`)
- **Migrations:** `alembic`
- **Language:** Python 3.11+

## 🚀 Quick Start

### 1. Clone the repository
```bash
git clone <your-repository-url>
cd aiogram-bot-template
```

### 2. Set up the virtual environment
We recommend using `.venv` for this project.
```powershell
python -m venv .venv
.\.venv\Scripts\activate  # Windows (PowerShell)
# source .venv/bin/activate  # Linux/macOS
```

### 3. Install dependencies
```bash
pip install -r requairments.txt
```

### 4. Configure Environment Variables
Copy `.env.example` to `.env` (or create a `.env` file) in the root directory and add your bot token and database credentials:
```env
BOT_TOKEN=your_bot_token_here
DB_URL=postgresql+asyncpg://user:password@localhost:5432/your_db_name
```

### 5. Run Database Migrations
Generate and apply the initial database schemas:
```bash
alembic revision --autogenerate -m "init"
alembic upgrade head
```

### 6. Start the Bot
```bash
python app.py
```

## 📁 Project Structure Overview

- `app.py`: Main entry point to run the bot.
- `loader.py`: Initializes global singletons (`bot`, `dp`, `db`).
- `config.py`: Environment variables loader.
- `db/`: Database core, models, repositories, and Alembic migrations.
- `handlers/`: Route handlers grouped by features (e.g., `admin`, `register`).
- `middlewares/`: Middleware components for injecting database sessions and user validation.

## 🤝 Contributing
Contributions, issues, and feature requests are always welcome! Feel free to fork the repository and submit your pull requests.

## 📝 License
This project is open-source. Feel free to use and modify it for your own projects!