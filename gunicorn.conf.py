# gunicorn.conf.py – Gunicorn configuration for MarketMoose

import os

# ─────────────────────────────────────────────────────────────────────────
# Server mechanics
# ─────────────────────────────────────────────────────────────────────────
bind    = "0.0.0.0:8000"
workers = 4
timeout = 120

# ─────────────────────────────────────────────────────────────────────────
# Logging — write to the same files as configured in entrypoint.sh
# ─────────────────────────────────────────────────────────────────────────
accesslog = "/app/logs/access.log"
errorlog  = "/app/logs/error.log"
loglevel  = "info"

# ─────────────────────────────────────────────────────────────────────────
# Worker hooks
# ─────────────────────────────────────────────────────────────────────────
def post_fork(server, worker):
    """
    Runs every time a worker boots — whether on initial startup or after
    a crash/timeout. Primes the stock cache for any missing data.
    """
    try:
        from yfinance import set_tz_cache_location
        from config import BaseConfig
        from datetime import datetime, timezone, timedelta

        CACHE_DIR     = os.environ.get("CACHE_DIR", BaseConfig.CACHE_DIR)
        YF_CACHE_DIR  = os.path.join(CACHE_DIR, "yf_cache")
        os.makedirs(YF_CACHE_DIR, exist_ok=True)
        set_tz_cache_location(YF_CACHE_DIR)

        cache_update_hour = float(os.environ.get("CACHE_UPDATE_HOUR_UTC", "6.5"))
        now_utc = datetime.now(timezone.utc)
        now_hours = now_utc.hour + now_utc.minute / 60

        from services.transactions import load_transactions
        from services.yf_cache import download_stock_data

        df_tx = load_transactions()
        pairs = list(dict.fromkeys(zip(df_tx["symbol"], df_tx["exchange"])))

        if now_hours >= cache_update_hour:
            # After market close — fetch everything including today
            download_stock_data(pairs, force_refresh=False)
        else:
            # Before market close — fetch previous days only, not today
            yesterday = (now_utc - timedelta(days=1)).date()
            rows_appended = download_stock_data(pairs, force_refresh=False, cutoff_date=yesterday)
            if rows_appended > 0:
                server.log.info("Worker booted before market close — fetching previous days only.")
            else:
                server.log.info("Worker booted before market close — skipping cache update.")

    except Exception as e:
        server.log.error(f"Cache priming failed in worker {worker.pid}: {e}")
