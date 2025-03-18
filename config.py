import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")

SPACEX_BASE_URL = os.environ.get("SPACEX_BASE_URL", "https://api.spacexdata.com/v4")

try:
    CACHE_EXPIRY = int(os.environ.get("CACHE_EXPIRY", 3600))
except ValueError:
    logging.error("Invalid CACHE_EXPIRY value, using default of 3600")
    CACHE_EXPIRY = 3600
