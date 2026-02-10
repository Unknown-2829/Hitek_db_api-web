"""
Phantom OSINT DB API — FastAPI Server
Public REST API for mobile number lookup against 1.78B record database.
"""

import re
import time
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from api.config import API_HOST, API_PORT, CORS_ORIGINS
from api.database import db

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
)
logger = logging.getLogger(__name__)


# ── Lifespan ───────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup/shutdown: connect and close the database."""
    await db.connect()
    logger.info("⚡ Phantom OSINT DB API is ready!")
    yield
    await db.close()
    logger.info("API shut down.")


# ── App ────────────────────────────────────────────────────────────
app = FastAPI(
    title="Phantom OSINT DB API",
    description="Public API for mobile number lookup — 1.78B records, deep-link search.",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET"],
    allow_headers=["*"],
)


# ── Helpers ────────────────────────────────────────────────────────
def clean_mobile(raw: str) -> str | None:
    """Extract clean 10-digit Indian mobile from any format."""
    digits = re.sub(r"[^\d]", "", raw)
    if not digits:
        return None
    if len(digits) == 12 and digits.startswith("91"):
        digits = digits[2:]
    elif len(digits) == 11 and digits.startswith("0"):
        digits = digits[1:]
    elif len(digits) == 13 and digits.startswith("091"):
        digits = digits[3:]
    if len(digits) == 10 and digits[0] in "6789":
        return digits
    return None


# ── Endpoints ──────────────────────────────────────────────────────

@app.get("/")
async def root():
    """API status."""
    return {
        "status": "online",
        "name": "Phantom OSINT DB API",
        "version": "1.0.0",
        "records": "1.78B",
        "endpoints": {
            "lookup": "/api/lookup?number=9876543210",
            "docs": "/docs",
        },
    }


@app.get("/api/lookup")
async def lookup(number: str = Query(..., description="10-digit Indian mobile number")):
    """
    Look up a mobile number in the database.
    
    - Accepts 10-digit number (auto-cleans +91, 0 prefixes)
    - Performs deep-link search following alt_mobile chains
    - Returns consolidated profile with all linked data
    """
    mobile = clean_mobile(number)

    if mobile is None:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "Invalid number",
                "message": "Please provide a valid 10-digit Indian mobile number.",
                "example": "9876543210",
            },
        )

    t_start = time.perf_counter()
    profile = await db.deep_search(mobile)
    elapsed_ms = int((time.perf_counter() - t_start) * 1000)

    profile["response_time_ms"] = elapsed_ms

    logger.info(f"[LOOKUP] {mobile} → {profile['total_records']} records in {elapsed_ms}ms")

    return JSONResponse(content=profile)


@app.get("/api/stats")
async def stats():
    """Database statistics."""
    row_count = await db.get_row_count()
    db_size = await db.get_db_size()

    units = ["B", "KB", "MB", "GB", "TB"]
    size = float(db_size)
    for unit in units:
        if size < 1024:
            size_str = f"{size:.1f} {unit}"
            break
        size /= 1024
    else:
        size_str = f"{size:.1f} PB"

    return {
        "total_records": row_count,
        "database_size": size_str,
        "engine": "SQLite WAL",
        "cache": "64MB",
        "mmap": "2GB",
    }


# ── Run ────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api.main:app", host=API_HOST, port=API_PORT, reload=False)
