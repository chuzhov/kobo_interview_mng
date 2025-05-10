import os

# This file contains configuration settings for the application.
# Development stage
DEBUG = os.getenv("DEBUG", "True").lower() == "true"
DEBUG_SCHEDULER_INTERVAL = 1

# Database settings
DB_PATH = "db/interviews.db"
DATABASE_URL = f"sqlite+aiosqlite:///{DB_PATH}"

# Scheduler settings
TIMEZONE = "Europe/Kyiv"
WORKING_HOURS = {
    "start": 7,  # 7 AM
    "end": 22,  # 10 PM
}

# FastAPI server settings
PORT = int(os.getenv("PORT", 8000))
