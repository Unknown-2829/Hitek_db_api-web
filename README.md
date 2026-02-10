# ⚡ HiTek DB Telegram Bot

High-performance Telegram bot built with **aiogram 3.x** for querying a **1.78 Billion row** SQLite database instantly.

## ✨ Features

| Feature | Description |
|---------|-------------|
| 🔍 **Instant Mobile Search** | O(log n) indexed lookup — sub-second on 1.78B rows |
| 👤 **Multi-field Search** | Search by name, email, address, or father's name |
| 🎨 **OSINT-Style Output** | Clean monospace formatting, easy to copy |
| ⚡ **Async Non-blocking** | `aiosqlite` + async I/O — bot never freezes |
| 🔒 **Access Control** | Private/Public mode, admin-only commands |
| 🛡️ **Anti-Flood** | Rate limiting (1 search / 2 seconds per user) |
| 📝 **Search Logging** | Every query logged to `search_history.log` |
| 📊 **Statistics** | Real-time search count, user tracking, uptime |
| 📡 **Broadcast** | Send alerts to all tracked users |
| 🚫 **Ban System** | Ban/unban users with persistent storage |
| 🔄 **Auto-Retry** | Retries on DB lock with exponential backoff |

## 🚀 Quick Setup

### 1. Clone & Install

```bash
git clone https://github.com/yourusername/hitek-db-tg-bot.git
cd hitek-db-tg-bot
pip install -r requirements.txt
```

### 2. Configure

```bash
cp .env.example .env
nano .env
```

Edit `.env`:
```env
BOT_TOKEN=your_telegram_bot_token
ADMIN_IDS=123456789,987654321
DB_PATH=/data/users.db
RATE_LIMIT=2
BOT_MODE=private
```

### 3. Run

```bash
python main.py
```

## 📖 User Commands

| Command | Description |
|---------|-------------|
| `/start` | Welcome message with usage guide |
| `/help` | List all user commands |
| `/search <query>` | Search by mobile or name (auto-detect) |
| `/email <query>` | Search by email |
| `/addr <query>` | Search by address |
| `/fname <query>` | Search by father's name |
| `/stats` | Bot statistics |
| *direct text* | Send a number → mobile search, text → name search |

## 🔐 Admin Commands

| Command | Description |
|---------|-------------|
| `/admin` | Show admin command list |
| `/logs` | Download search history log |
| `/dbstats` | Database row count and file size |
| `/alert <msg>` | Broadcast message to all users |
| `/clearlog` | Clear search log file |
| `/setmode <mode>` | Set bot to `public` or `private` |
| `/getmode` | Show current bot mode |
| `/users` | Show tracked user count |
| `/ban <id>` | Ban a user by ID |
| `/unban <id>` | Unban a user |
| `/banlist` | List all banned users |

## 🏗️ Project Structure

```
hitek-db-tg-bot/
├── main.py              # Entry point
├── requirements.txt     # Dependencies
├── .env.example         # Environment template
├── .gitignore
├── README.md
└── bot/
    ├── __init__.py
    ├── config.py        # Settings loader
    ├── database.py      # Async SQLite manager
    ├── formatters.py    # OSINT-style output
    ├── middlewares.py   # Rate limit + access control
    ├── state.py         # Bot mode persistence
    ├── user_store.py    # User/ban list persistence
    └── handlers/
        ├── __init__.py
        ├── user.py      # User commands
        └── admin.py     # Admin commands
```

## ⚡ Performance Notes

- **Mobile search**: Uses `idx_mobile` index → ~100ms on 1.78B rows
- **Name/Email/Address**: Full-table `LIKE` scan → slower, limited to 25 results
- **WAL mode**: Allows concurrent reads without blocking
- **64MB cache + 2GB mmap**: Optimized for large dataset
- **Async**: All DB queries run in a thread pool via `aiosqlite`

## 📜 License

MIT
