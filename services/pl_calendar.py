"""
pl_calendar.py – Profit/Loss Calendar Module for MarketMoose

Computes monthly time-weighted return (TWR) series for display in the
P/L calendar chart. Implements request-scope and Redis-based caching to
optimize performance and avoid recomputation.
"""

import json
import time
import hashlib
from flask import current_app, g
from .portfolio import get_monthly_time_weighted_returns
from services.dividends import load_dividends 

def pl_calendar_for_cached(df_tx, fx_rates, fy_start, fy_end):
    """
    Retrieve (or compute and cache) a JSON-encoded monthly P/L calendar
    based on TWR for the provided transactions and FX rates.
    """
    current_app.logger.debug(f"PL Calendar called with fx_rates: {fx_rates}")
    if fx_rates is None:
        current_app.logger.error("fx_rates is None in pl_calendar_for_cached")
        raise ValueError("fx_rates is None in pl_calendar_for_cached")

    # ───────────────────────────────
    # 1. Use request-scope cache if set
    # ───────────────────────────────
    if hasattr(g, 'pl_calendar_cache_result'):
        current_app.logger.info("PL calendar cache hit (request-scoped)")
        return g.pl_calendar_cache_result

    df_div = load_dividends()

    # ───────────────────────────────
    # 2. Prepare Redis caching
    # ───────────────────────────────
    cache_extension = current_app.extensions.get("cache")

    if isinstance(cache_extension, dict):
        cache_backend = next(iter(cache_extension.values()))
    else:
        cache_backend = cache_extension

    is_valid_cache = (
        cache_backend is not None
        and hasattr(cache_backend, "get")
        and hasattr(cache_backend, "set")
    )
    current_app.logger.debug(f"Cache backend type: {type(cache_backend)}")
    current_app.logger.debug(f"is_valid_cache: {is_valid_cache}")

    # ───────────────────────────────
    # 3. Generate stable cache key using hash of inputs
    # ───────────────────────────────
    df_serialized = df_tx.copy()
    for col in df_serialized.select_dtypes(include=['datetime64[ns]']).columns:
        df_serialized[col] = df_serialized[col].astype(str)

    input_str = json.dumps({
        "tx": df_serialized.to_dict(orient="records"),
        "fx": fx_rates,
        "start": str(fy_start),
        "end": str(fy_end),
    }, sort_keys=True)
    digest = hashlib.md5(input_str.encode("utf-8")).hexdigest()
    cache_key = f"pl_calendar:{digest}"

    # ───────────────────────────────
    # 4. Try Redis cache lookup
    # ───────────────────────────────
    if is_valid_cache:
        cached = cache_backend.get(cache_key)
        if cached is not None:
            current_app.logger.info(f"PL calendar cache hit (Flask): {cache_key}")
            g.pl_calendar_cache_result = cached
            return cached
        else:
            current_app.logger.info(f"PL calendar cache miss (Flask): {cache_key}")

    # ───────────────────────────────
    # 5. Compute the calendar if not cached
    # ───────────────────────────────
    start_time = time.perf_counter()
    result = _compute_pl_calendar(df_tx, df_div, fx_rates, fy_start, fy_end)
    elapsed = time.perf_counter() - start_time

    if is_valid_cache:
        cache_backend.set(cache_key, result, timeout=3600)

    g.pl_calendar_cache_result = result
    return result

def _compute_pl_calendar(df_tx, df_div, fx_rates, fy_start, fy_end): 
    """
    Compute the monthly P/L calendar using time-weighted returns.
    """
    current_app.logger.debug(f"_compute_pl_calendar called with fx_rates: {fx_rates}")
    if fx_rates is None:
        current_app.logger.error("fx_rates is None in _compute_pl_calendar")
        raise ValueError("fx_rates is None in _compute_pl_calendar")
    
    df_cal = get_monthly_time_weighted_returns(df_tx, df_div, fx_rates, fy_start, fy_end)
    return df_cal.to_json(orient="records")
