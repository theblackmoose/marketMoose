#!/bin/sh
#
# entrypoint.sh – Startup script for MarketMoose container
#
# Responsibilities:
# - Waits briefly for dependent services (e.g., Redis)
# - Primes yfinance cache by downloading historical stock data
# - Launches the Flask app using Gunicorn

# 1) Wait for Redis or other services to be ready
sleep 2

if [ ! -d /app/stock_data_cache/yf_cache ]; then
  echo "Creating yf_cache directory..."
  mkdir -p /app/stock_data_cache/yf_cache
else
  echo "yf_cache already exists"
fi

# 2) Run a Python snippet to preload stock data
python3 - <<\EOF
import logging
import os

# Configure basic logging so that yf_cache.py logs are visible
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s"
)

# Set yfinance timezone cache location
from yfinance import set_tz_cache_location
from config import BaseConfig

CACHE_DIR = os.environ.get("CACHE_DIR", BaseConfig.CACHE_DIR)
YF_CACHE_DIR = os.path.join(CACHE_DIR, "yf_cache")
os.makedirs(YF_CACHE_DIR, exist_ok=True)
set_tz_cache_location(YF_CACHE_DIR)

# Prime the stock cache using recent transaction symbols
from services.transactions import load_transactions
from services.yf_cache import download_stock_data

df_tx = load_transactions()
pairs = list(dict.fromkeys(zip(df_tx['symbol'], df_tx['exchange'])))
download_stock_data(pairs, force_refresh=False)
EOF

# 3) Start the Flask app via Gunicorn
exec gunicorn -w 4 -b 0.0.0.0:8000 marketMoose:app
