import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://localhost/hyper_track")
API_URL = os.getenv("HL_API_URL", "https://api.hyperliquid.xyz")

# Polling config
POLL_CONCURRENCY = int(os.getenv("POLL_CONCURRENCY", "5"))
BACKFILL_CONCURRENCY = int(os.getenv("BACKFILL_CONCURRENCY", "2"))
BACKFILL_DAYS = int(os.getenv("BACKFILL_DAYS", "90"))

# Tier intervals (seconds)
TIER_INTERVALS = {
    "hot": 120,
    "warm": 900,
    "cold": 3600,
    "frozen": 21600,
}
