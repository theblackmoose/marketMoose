"""
fx.py – Foreign Exchange Rate Utilities for MarketMoose

This module provides financial year parsing and foreign exchange (FX) rate
calculation between currencies using yfinance. It includes both in-request
memoization and Redis caching (via Flask-Caching) to reduce API calls.
"""

import pandas as pd
import yfinance as yf
from flask import current_app, g
from datetime import datetime

def get_fy_dates(fy_label):
    """
    Convert a financial year label (e.g., "2023/2024") into start and end dates.
    Returns (start_date, end_date) as pd.Timestamp objects.
    """
    if "/" not in fy_label:
        return None, None
    base = fy_label.split("/")[0]
    start_year = 2000 + int(base) if len(base) == 2 else int(base)
    start = pd.Timestamp(year=start_year, month=7, day=1)
    end = pd.Timestamp(year=start_year + 1, month=6, day=30)
    return start, end

def calculate_fx_rates(src_currencies: set[str], target_currency: str) -> dict[str, float]:
    """
    Fetch FX rates to convert each currency in src_currencies to target_currency.
    Uses in-request caching and Redis caching to reduce redundant fetches.
    """
    fx_rates: dict[str, float] = {}
    today = datetime.today().strftime("%Y-%m-%d")
    
    # ─────────────────────────────────────────────
    # 1. Check request-level cache (g)
    # ─────────────────────────────────────────────
    if not hasattr(g, "_fx_rates_cache"):
        g._fx_rates_cache = {}

    cache_key = f"{target_currency}:{today}:" + ",".join(sorted(src_currencies))

    if cache_key in g._fx_rates_cache:
        current_app.logger.info(f"FX rates cache hit (request-scoped): {cache_key}")
        return g._fx_rates_cache[cache_key]

    # ─────────────────────────────────────────────
    # 2. Setup Redis cache backend (via Flask-Caching)
    # ─────────────────────────────────────────────
    cache_extension = current_app.extensions.get("cache", None)
    if isinstance(cache_extension, dict):
        cache_backend = next(iter(cache_extension.values()))
    else:
        cache_backend = cache_extension

    current_app.logger.debug(f"Cache backend in fx_rates: {cache_extension}")
    is_valid_cache = (
        cache_backend is not None
        and hasattr(cache_backend, "get")
        and hasattr(cache_backend, "set")
    )
    current_app.logger.debug(f"is_valid_cache: {is_valid_cache}")

    # ─────────────────────────────────────────────
    # 3. Fetch or look up FX rates per currency
    # ─────────────────────────────────────────────
    for src in src_currencies:
        if src == target_currency:
            fx_rates[src] = 1.0
            continue

        flask_key = f"fx:{src}->{target_currency}:{today}"
        
        # Try Redis cache first
        if is_valid_cache:
            current_app.logger.debug(f"Checking Redis for FX key: {flask_key}")
            cached = cache_backend.get(flask_key)
            if cached is not None:
                current_app.logger.info(f"FX cache hit (Flask): {flask_key}")
                fx_rates[src] = cached
                continue
            else:
                current_app.logger.info(f"FX cache miss (Flask): {flask_key}")

        # Fallback to yfinance API
        try:
            pair = f"{src}{target_currency}=X"
            rate = yf.Ticker(pair).history(period="1d", raise_errors=True)["Close"].iloc[-1]
            rate = float(rate)
            current_app.logger.debug(f"Fetched FX rate for {pair}: {rate}")
        except Exception:
            rate = 1.0
            current_app.logger.warning(f"Failed to fetch FX rate for {pair}; defaulting to 1.0")

        fx_rates[src] = rate

        # Save to Redis cache
        if is_valid_cache:
            current_app.logger.debug(f"Setting Redis cache for FX key: {flask_key}")
            cache_backend.set(flask_key, rate, timeout=3600)

    # Store in request-scope cache
    g._fx_rates_cache[cache_key] = fx_rates
    current_app.logger.debug(f"Set FX rates cache in request scope: {cache_key}")

    return fx_rates
