# Phantom OSINT DB — API & Web

Public REST API and web interface for mobile number intelligence lookup against a **1.78 billion record** database.

![License](https://img.shields.io/badge/license-MIT-green)
![Python](https://img.shields.io/badge/python-3.10+-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-teal)

---

## 🔍 What It Does

- **Mobile number lookup** against 1.78B indexed records
- **Deep-link search** — follows `alt_mobile` chains up to 3 hops
- Returns **consolidated profiles** with all linked phones, names, addresses, regions
- Every query uses indexed lookups — **~100ms per hop**

---

## 🌐 API Endpoints

### `GET /api/lookup?number={mobile}`

Look up a mobile number with deep-link analysis.

**Parameters:**
| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `number` | string | Yes | 10-digit Indian mobile. Auto-cleans +91, 0 prefixes. |

**Example:**
```bash
curl "https://api.unknowns.app/api/lookup?number=9876543210"
```

**Response:**
```json
{
  "query": "9876543210",
  "found": true,
  "total_records": 4,
  "total_phones": 3,
  "phones": ["9876543210", "8817342793", "7000419892"],
  "names": ["Arun Kumar Patel"],
  "father_names": ["Sarita Patel"],
  "emails": [],
  "addresses": ["W/O Arun Kumar, Rewa, MP, 486340"],
  "regions": ["AIRTEL MP", "JIO MP"],
  "response_time_ms": 156
}
```

### `GET /api/stats`

Database statistics.

### `GET /docs`

Interactive Swagger UI documentation.

---

## 🚀 Self-Hosting (API on VPS)

```bash
# Clone
git clone https://github.com/Unknown-2829/Hitek_db_api-web.git
cd Hitek_db_api-web

# Install
pip install -r requirements.txt

# Configure
export DB_PATH="/data/users.db"

# Run
python -m api.main
```

The API will start on `http://0.0.0.0:8000`.

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DB_PATH` | `/data/users.db` | SQLite database path |
| `API_HOST` | `0.0.0.0` | Bind address |
| `API_PORT` | `8000` | Port |
| `CORS_ORIGINS` | `*` | Comma-separated allowed origins |
| `DEEP_SEARCH_DEPTH` | `3` | Max BFS hops |
| `MAX_RESULTS` | `25` | Max rows per query |

---

## 🌍 Website (Static)

The `website/` folder contains a static site you can host on **Cloudflare Pages**, **GitHub Pages**, **Render**, or any static host.

Files:
- `index.html` — Search interface
- `docs.html` — API documentation
- `style.css` — Dark OSINT theme
- `app.js` — Frontend logic

**To configure:** Edit `API_BASE` in `app.js` to point to your VPS API URL.

---

## 📁 Project Structure

```
├── api/
│   ├── __init__.py
│   ├── config.py      # Environment config
│   ├── database.py    # SQLite + deep-link search
│   └── main.py        # FastAPI server
├── website/
│   ├── index.html     # Search page
│   ├── docs.html      # API docs page
│   ├── style.css      # Styling
│   └── app.js         # Frontend JS
├── requirements.txt
└── README.md
```

---

## 🔧 Tech Stack

| Component | Technology |
|-----------|-----------|
| API | FastAPI + Uvicorn |
| Database | SQLite (WAL mode, 64MB cache, 2GB mmap) |
| Search | BFS deep-link on indexed `mobile` column |
| Frontend | Vanilla HTML/CSS/JS |
| Fonts | Inter + JetBrains Mono |

---

## 📜 License

MIT — Use freely for OSINT research.
