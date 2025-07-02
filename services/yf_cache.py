"""
yf_cache.py – Yahoo Finance data caching module for MarketMoose

Handles:
- Fetching and caching full historical stock price data
- Incremental updates for existing cached data
- Rate limit retries and backoff
- Parallelized downloads with thread pooling
"""

import os
import time
import pandas as pd
import yfinance as yf
import logging
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor
from yfinance.exceptions import YFRateLimitError

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Read from environment rather than current_app
MAX_RETRIES          = int(os.environ.get("MAX_RETRIES", "3"))
BACKOFF_BASE_SECONDS = int(os.environ.get("BACKOFF_BASE_SECONDS", "15"))
CACHE_DIR            = os.environ.get("CACHE_DIR", "stock_data_cache")

# Hard‐coded exchange suffixes
EXCHANGE_SUFFIX_DICT = {
    "ASX":        ".AX",
    "BM&FBOVESPA":".SA",
    "Euronext":   "",
    "FWB":        ".DE",
    "HKEX":       ".HK",
    "JPX":        ".T",
    "JSE":        ".JO",
    "KRX":        ".KS",
    "LSE":        ".L",
    "NSE":        ".NS",
    "SGX":        ".SI",
    "SSE":        ".SS",
    "SZSE":       ".SZ",
    "TSX":        ".TO",
    "TWSE":       ".TW",
    "NASDAQ":     "",
    "NYSE":       "",
}

def fetch_and_cache(yf_symbol: str):
    """
    Fetch full historical price data for a given Yahoo Finance symbol and save to CSV cache.
    Retries on rate limit errors with exponential backoff.
    """
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            ticker = yf.Ticker(yf_symbol)
            df = ticker.history(
                period="max",
                auto_adjust=False,
                raise_errors=True,
                actions=True,
            )
            if not df.empty:
                df.index = pd.to_datetime(df.index, utc=True).tz_convert(None).normalize()
                df.index = df.index.strftime("%Y-%m-%d")
                df.index.name = "Date"

                os.makedirs(CACHE_DIR, exist_ok=True)
                out_path = os.path.join(CACHE_DIR, f"{yf_symbol}.csv")
                df.to_csv(out_path)

            logger.info(f"Fetched and cached data for {yf_symbol}")
            return

        except (YFRateLimitError, Exception) as e:
            code = getattr(getattr(e, "response", None), "status_code", None)
            logger.warning(
                f"Error fetching {yf_symbol}: {e} (status_code={code}), attempt {attempt}"
            )
            if isinstance(e, YFRateLimitError) or code == 429:
                time.sleep(BACKOFF_BASE_SECONDS * attempt)
            else:
                break

    logger.error(f"Failed to fetch data for {yf_symbol} after {MAX_RETRIES} attempts.")

def fetch_missing(yf_symbol: str, start_date: pd.Timestamp) -> pd.DataFrame:
    """
    Fetch price data from start_date to today for a given symbol.
    Returns:
        pd.DataFrame: A DataFrame of new data rows, or empty if fetch fails.
    """
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            ticker = yf.Ticker(yf_symbol)
            df = ticker.history(
                start=start_date,
                end=datetime.now().date() + timedelta(days=1),
                auto_adjust=False,
                raise_errors=True,
                actions=True,
            )
            if not df.empty:
                # Normalize to tz-naive datetime index
                df.index = pd.to_datetime(df.index, utc=True).tz_convert(None).normalize()
            return df

        except (YFRateLimitError, Exception) as e:
            code = getattr(getattr(e, "response", None), "status_code", None)
            if isinstance(e, YFRateLimitError) or code == 429:
                time.sleep(BACKOFF_BASE_SECONDS * attempt)
                continue
            else:
                return pd.DataFrame()

    return pd.DataFrame()

def download_stock_data(
    pairs: list[tuple[str, str]],
    force_refresh: bool = False,
):
    """
    Update local CSV cache for a list of (symbol, exchange) pairs.
    Performs a full refresh if the file is missing or force_refresh is True.
    Otherwise, performs incremental fetch of only missing data.
    """
    full_fetch_symbols = []
    partial_symbols = []

    for sym, exch in pairs:
        suffix = EXCHANGE_SUFFIX_DICT.get(exch, "")
        yf_symbol = f"{sym}{suffix}"
        cache_file = os.path.join(CACHE_DIR, f"{yf_symbol}.csv")

        if force_refresh or not os.path.exists(cache_file):
            if os.path.exists(cache_file):
                try:
                    os.remove(cache_file)
                except Exception as e:
                    logger.warning(f"Could not remove old cache file '{cache_file}': {e}")
            full_fetch_symbols.append(yf_symbol)
        else:
            partial_symbols.append(yf_symbol)

    if full_fetch_symbols:
        max_workers = min(10, len(full_fetch_symbols))
        logger.info(f"Starting parallel fetch for {len(full_fetch_symbols)} symbols (max_workers={max_workers})")
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            executor.map(fetch_and_cache, full_fetch_symbols)

    for yf_symbol in partial_symbols:
        cache_file = os.path.join(CACHE_DIR, f"{yf_symbol}.csv")

        try:
            df_cached = pd.read_csv(cache_file, parse_dates=["Date"], index_col="Date")
            df_cached.index = pd.to_datetime(df_cached.index).normalize()
        except Exception as e:
            logger.warning(f"Could not read cached CSV '{cache_file}': {e}. Re-fetching full history.")
            fetch_and_cache(yf_symbol)
            continue

        if df_cached.empty:
            logger.info(f"Cached CSV for {yf_symbol} is empty. Re-fetching full history.")
            fetch_and_cache(yf_symbol)
            continue

        last_date = df_cached.index.max()
        df_new = fetch_missing(yf_symbol, start_date=last_date + timedelta(days=1))

        if df_new is None or df_new.empty:
            continue

        df_new.index = pd.to_datetime(df_new.index).normalize()
        df_new = df_new[df_new.index > last_date]
        if df_new.empty:
            continue

        df_new.index = df_new.index.strftime("%Y-%m-%d")
        df_new.index.name = "Date"

        try:
            df_new.to_csv(cache_file, mode="a", header=False)
            logger.info(f"Appended {len(df_new)} new rows to cache for {yf_symbol}")
        except Exception as e:
            logger.error(f"Failed to append new data to '{cache_file}': {e}")
