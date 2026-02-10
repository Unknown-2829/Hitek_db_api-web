#!/bin/bash

# Configuration
export DB_PATH="/data/users.db"
export API_PORT=8000
export API_HOST="0.0.0.0"

# Check for database
if [ ! -f "$DB_PATH" ]; then
    echo "⚠️  WARNING: Database not found at $DB_PATH"
    echo "Please upload your users.db file to $DB_PATH"
fi

# Activate venv if exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Install dependencies if needed
# pip install -r requirements.txt

# Run
echo "🚀 Starting HiTek API on port $API_PORT..."
python3 -m api.main
