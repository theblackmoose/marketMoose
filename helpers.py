"""
helpers.py – Shared utility functions for MarketMoose

This module provides reusable helpers including:
- Converting DataFrames to JSON
- Rendering empty dashboards
- Fetching and formatting benchmark return histories
"""

import pandas as pd
import logging
from flask import render_template
from config import BENCHMARKS

def dataframe_to_json(df, date_column="date"):
    """
    Convert a DataFrame to JSON, ensuring the date_column is formatted as 'YYYY-MM-DD'.
    If the column is already strings, this is a no‐op.
    """
    if not df.empty and df[date_column].dtype != "O":
        temp = df.copy()
        temp[date_column] = temp[date_column].dt.strftime("%Y-%m-%d")
        return temp.to_json(orient="records")
    else:
        return "[]"

def render_empty_dashboard(**kwargs):
    """
    Renders your 'dashboard.html' template with everything empty/default.
    Any keyword args you pass override the defaults.
    """
    defaults = dict(
        portfolio=[],
        total_value=0.0,
        total_change_amt=0.0,
        total_change_pct=0.0,
        invested_summary={},
        returned_summary={},
        total_dividends=0.0,
        total_dividends_by_currency={},
        value_history_json="[]",
        return_history_json="[]",
        broker_fees_by_currency={},
        benchmark_json="[]",
        pl_calendar_json="[]",
        dividends_table=pd.DataFrame(columns=["id", "symbol", "date", "dividend_amount", "currency"]),
        transactions_table=pd.DataFrame(columns=[]),
        fy_choices=[],
        selected_fy="All",
        order_by="symbol",
        market_value_period="all",
        benchmark_choices=[],
        selected_benchmark="none",
        fy_end_str="",
    )
    defaults.update(kwargs)
    return render_template("dashboard.html", **defaults)

def get_benchmark_return_history(start_date, end_date, benchmark="sp500"):
    """
    Fetch historical benchmark data from yfinance and calculate % return from start.
    Returns:
        pd.DataFrame: DataFrame with 'date' and 'benchmark_return' columns.
    """
    info = BENCHMARKS.get(benchmark)
    if not info or info["ticker"] is None:
        logging.info(f"Benchmark not found: {benchmark}")
        return pd.DataFrame(columns=["date", "benchmark_return"])

    ticker_symbol = info["ticker"]
    try:
        hist = __import__("yfinance").Ticker(ticker_symbol).history(
            start=start_date,
            end=end_date + pd.Timedelta(days=1),
        )
    except Exception as e:
        logging.error(f"Failed to fetch benchmark {ticker_symbol}: {e}")
        return pd.DataFrame(columns=["date", "benchmark_return"])

    if hist.empty or "Close" not in hist:
        logging.warning(
            f"No data found for benchmark {ticker_symbol} between {start_date} and {end_date}"
        )
        return pd.DataFrame(columns=["date", "benchmark_return"])

    closes = hist["Close"]
    start_val = closes.iloc[0]
    pct_return = ((closes - start_val) / start_val) * 100

    df = pd.DataFrame({
        "date": closes.index.normalize().strftime("%Y-%m-%d"),
        "benchmark_return": pct_return.values,
    })
    logging.info(
        f"Benchmark {ticker_symbol} fetched for range {start_date} to {end_date}"
    )
    return df
