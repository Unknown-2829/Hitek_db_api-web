"""
HiTek DB API — Configuration
Loads settings from environment variables or .env file.
"""

import os
from dotenv import load_dotenv

load_dotenv()

# Database
DB_PATH = os.getenv("DB_PATH", "/data/users.db")

# API
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", "8000"))

# Performance
MAX_RESULTS = int(os.getenv("MAX_RESULTS", "25"))
DB_RETRY_ATTEMPTS = int(os.getenv("DB_RETRY_ATTEMPTS", "3"))
DB_RETRY_DELAY = float(os.getenv("DB_RETRY_DELAY", "0.5"))
DEEP_SEARCH_DEPTH = int(os.getenv("DEEP_SEARCH_DEPTH", "3"))

# CORS — comma-separated allowed origins
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*").split(",")
