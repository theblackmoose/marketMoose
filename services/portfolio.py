"""
portfolio.py – Core portfolio analytics for MarketMoose

Provides:
- NAV and return history
- Portfolio valuation as of a date
- Monthly time-weighted returns (TWR)
- Cost basis and realized return summaries
- Dividend cashflow handling
"""

import os
import pandas as pd
import numpy as np
from flask import current_app
from config import EXCHANGE_SUFFIX

def compute_dividends(
    df_tx: pd.DataFrame,
    df_div: pd.DataFrame,
    fx_rates: dict[str, float]
) -> dict[str, float]:
    """
    Calculate total dividends per symbol, converting all amounts
    to the display currency using FX rates.
    """
    if df_div.empty:
        return {}

    df_div = df_div.copy()
    df_div["date"] = pd.to_datetime(df_div["date"]).dt.normalize()

    dividends_per_symbol = {}
    for sym, group in df_div.groupby("symbol"):
        total_div = 0.0
        for _, row in group.iterrows():
            fx = fx_rates.get(row["currency"], 1.0)
            total_div += row["dividend_amount"] * fx
        dividends_per_symbol[sym] = round(total_div, 2)

    return dividends_per_symbol

def get_portfolio_value_history(
    df_tx: pd.DataFrame,
    fx_rates: dict[str, float],
    start_date: pd.Timestamp | None = None,
    end_date: pd.Timestamp | None = None
) -> pd.DataFrame:
    """
    Build a daily Net Asset Value (NAV) history.
    Combines price data with cumulative shares held over time.
    """
    if fx_rates is None:
        raise ValueError("fx_rates argument is None in get_portfolio_value_history")

    if df_tx.empty:
        return pd.DataFrame(columns=["date", "total_value"])

    df_tx = df_tx.copy()
    df_tx["date"] = df_tx["date"].dt.normalize()

    all_min = df_tx["date"].min()
    today = pd.Timestamp.today().normalize()
    min_date = start_date if start_date else all_min
    max_date = end_date if end_date else today
    full_index = pd.date_range(min_date, max_date, freq="D")

    symbol_exch = df_tx.drop_duplicates("symbol", keep="last").set_index("symbol")["exchange"].to_dict()

    # Load historical prices for all symbols
    prices = []
    for sym, exch in symbol_exch.items():
        suffix = EXCHANGE_SUFFIX.get(exch, "")
        cache_file = os.path.join(current_app.config["CACHE_DIR"], f"{sym}{suffix}.csv")
        if not os.path.exists(cache_file):
            continue
        dfp = pd.read_csv(cache_file, parse_dates=["Date"])
        dfp["Date"] = pd.to_datetime(dfp["Date"]).dt.normalize()
        dfp = dfp.set_index("Date")[["Close"]].rename(columns={"Close": sym})
        prices.append(dfp)

    if not prices:
        return pd.DataFrame(columns=["date", "total_value"])

    prices_df = pd.concat(prices, axis=1).sort_index().reindex(full_index)
    missing_data = prices_df.isna().sum()
    for sym, missing_count in missing_data.items():
        if missing_count > 0:
            current_app.logger.debug(f"Missing {missing_count} prices for {sym}")
    prices_df = prices_df.ffill()

    # Build cumulative shares table
    shares_daily = df_tx.groupby(["date", "symbol"])["shares"].sum().unstack(fill_value=0)
    shares_cum = shares_daily.cumsum().reindex(full_index).ffill().fillna(0)

    # Apply FX per symbol
    for sym in shares_cum.columns:
        currency = df_tx[df_tx["symbol"] == sym]["currency"].iloc[0]
        fx = fx_rates.get(currency, 1.0)
        prices_df[sym] *= fx

    # Compute daily total value
    nav = (shares_cum * prices_df).sum(axis=1).reset_index()
    nav.columns = ["date", "total_value"]
    
    current_app.logger.debug(f"Available symbols: {symbol_exch}")
    current_app.logger.debug(f"Price DataFrame columns: {list(prices_df.columns)}")
    current_app.logger.debug(f"Shares DataFrame shape: {shares_cum.shape}")
    current_app.logger.debug(f"Shares DataFrame head:\n{shares_cum.head()}")
    current_app.logger.debug(f"Prices DataFrame head:\n{prices_df.head()}")

    return nav

def get_portfolio_return_history(
    df_tx: pd.DataFrame,
    fx_rates: dict[str, float],
    start_date: pd.Timestamp | None = None,
    end_date: pd.Timestamp | None = None
) -> pd.DataFrame:
    """
    Calculates the daily return percentage of the portfolio using cumulative cost basis.
    """
    if df_tx.empty:
        return pd.DataFrame(columns=["date", "return"])

    current_app.logger.info("Calling get_portfolio_return_history...")

    value_df = get_portfolio_value_history(df_tx, fx_rates, start_date, end_date)
    nav_series = value_df.set_index("date")["total_value"]

    df_tx = df_tx.copy()
    df_tx["date"] = df_tx["date"].dt.normalize()
    df_tx["fx_cost"] = df_tx["trade_cost"] * df_tx["currency"].map(fx_rates)

    cost_series = df_tx.groupby("date")["fx_cost"].sum().reindex(nav_series.index, fill_value=0)
    cost_cum = cost_series.cumsum()

    return_series = ((nav_series - cost_cum) / cost_cum.replace(0, np.nan)) * 100
    return_series = return_series.fillna(0)

    current_app.logger.debug(f"NAV series head:\n{nav_series.head()}")
    current_app.logger.debug(f"Cumulative cost head:\n{cost_cum.head()}")
    current_app.logger.debug(f"Return % head:\n{return_series.head()}")

    return_series.name = "return"
    return return_series.reset_index()

def calculate_portfolio_value_asof(
    df_tx: pd.DataFrame,
    fx_rates: dict[str, float],
    asof_date,     
    dividends_per_symbol: dict[str, float]
) -> tuple[list[dict[str, object]], float, float, float]:
    """
    Computes portfolio valuation snapshot as of a specific date.
    """
    CACHE_DIR = current_app.config["CACHE_DIR"]

    cutoff = pd.to_datetime(asof_date)
    df_up_to_cutoff = df_tx[df_tx["date"] <= cutoff]

    symbol_exch = (
        df_up_to_cutoff
        .drop_duplicates(subset="symbol", keep="last")
        .set_index("symbol")["exchange"]
        .to_dict()
    )

    portfolio: list[dict[str, object]] = []
    total_value_converted = 0.0
    total_trade_cost_converted = 0.0

    for sym, grp in df_up_to_cutoff.groupby("symbol"):
        shares = grp["shares"].sum()
        if shares == 0:
            continue

        exch = symbol_exch.get(sym, "NASDAQ")
        suffix = EXCHANGE_SUFFIX.get(exch, "")
        yf_sym = f"{sym}{suffix}"
        cache_file = os.path.join(CACHE_DIR, f"{yf_sym}.csv")
        if not os.path.exists(cache_file):
            continue

        dfp = pd.read_csv(cache_file, parse_dates=["Date"], index_col="Date")
        dfp.index = pd.to_datetime(dfp.index, utc=True).tz_convert(None).normalize()
        price_rows = dfp[dfp.index <= cutoff]
        if price_rows.empty:
            continue

        price = price_rows["Close"].iloc[-1]

        trade_value = grp["trade_value"].sum()
        trade_cost = grp["trade_cost"].sum()
        rate = fx_rates.get(grp["currency"].iloc[0], 1.0)

        trade_value_c = round(trade_value * rate, 2)
        trade_cost_c = round(trade_cost * rate, 2)
        live_val_c = round(shares * price * rate, 2)

        total_value_converted += live_val_c
        total_trade_cost_converted += trade_cost_c

        change_amt = round(live_val_c - trade_cost_c, 2)
        change_pct = round((change_amt / trade_cost_c) * 100, 2) if trade_cost_c else 0.0

        portfolio.append({
            "symbol": sym,
            "shares": shares,
            "price": price,
            "live_value": live_val_c,
            "trade_value": trade_value_c,
            "trade_cost": trade_cost_c,
            "change_amount": change_amt,
            "change_pct": change_pct,
            "dividends": round(dividends_per_symbol.get(sym, 0.0), 2),
        })

    total_change_amt = round(total_value_converted - total_trade_cost_converted, 2)
    total_change_pct = (
        round((total_change_amt / total_trade_cost_converted) * 100, 2)
        if total_trade_cost_converted else 0.0
    )

    return portfolio, total_value_converted, total_change_amt, total_change_pct

def calculate_cost_basis_invested(df_tx: pd.DataFrame) -> dict[str, float]:
    """
    Returns a dict mapping each currency → total cost basis invested in shares still held.
    (Weighted‐average cost of the shares you haven’t sold.)
    """
    if df_tx.empty:
        return {}

    invested = {}
    net_shares = df_tx.groupby("symbol")["shares"].sum()
    buys = df_tx[df_tx["shares"] > 0]

    for sym, net in net_shares.items():
        if net <= 0:
            continue
        dfb = buys[buys["symbol"] == sym]
        total_buy_shares = dfb["shares"].sum()
        total_buy_cost = dfb["trade_cost"].sum()
        avg_cost = (total_buy_cost / total_buy_shares) if total_buy_shares else 0
        invested[sym] = avg_cost * net

    summary: dict[str, float] = {}
    for sym, amt in invested.items():
        curr = df_tx.loc[df_tx["symbol"] == sym, "currency"].iloc[0]
        summary.setdefault(curr, 0.0)
        summary[curr] += amt

    return {c: round(v, 2) for c, v in summary.items()}

def calculate_returned_summary(df_tx: pd.DataFrame) -> dict[str, float]:
    """
    Returns a dict mapping each currency → total amount returned by sell trades.
    (Sum of negative 'trade_cost' values, inverted to positive.)
    """
    if df_tx.empty:
        return {}

    sales = df_tx[df_tx["shares"] < 0]
    returned_summary = (
        sales.groupby("currency")["trade_cost"]
        .sum()
        .mul(-1)
        .round(2)
        .to_dict()
    )
    return returned_summary

def compute_daily_dividend_flows(
    df_div: pd.DataFrame,
    fx_rates: dict[str, float],
    date_index: pd.DatetimeIndex
) -> pd.Series:
    """
    Compute daily dividend cash flows converted to display currency,
    indexed by date_index, with zeros for missing dates.
    """
    if df_div.empty:
        return pd.Series(0, index=date_index)

    df_div = df_div.copy()
    df_div["date"] = pd.to_datetime(df_div["date"]).dt.normalize()

    # Convert dividend amounts to display currency using fx_rates
    df_div["div_cash_converted"] = df_div["dividend_amount"] * df_div["currency"].map(fx_rates).fillna(1.0)

    div_daily = df_div.groupby("date")["div_cash_converted"].sum()
    div_daily_full = div_daily.reindex(date_index, fill_value=0)

    return div_daily_full

def get_monthly_time_weighted_returns(
    df_tx: pd.DataFrame,
    df_div: pd.DataFrame,
    fx_rates: dict[str, float],
    fy_start: pd.Timestamp | None = None,
    fy_end: pd.Timestamp | None = None
) -> pd.DataFrame:
    """
    Calculates monthly time-weighted return (TWR) percentages for the portfolio.
    """
    current_app.logger.debug(f"get_monthly_time_weighted_returns called with fx_rates: {fx_rates}")
    nav_df = get_portfolio_value_history(df_tx, fx_rates, None, fy_end)
    if nav_df.empty:
        return pd.DataFrame(columns=["month", "twr_pct"])

    nav_df["date"] = pd.to_datetime(nav_df["date"])
    nav_df = nav_df.set_index("date").sort_index()
    nav = nav_df["total_value"]

    # 1a) cash from trades
    tx = df_tx.copy()
    tx["date"] = tx["date"].dt.normalize()
    tx["trade_value_c"] = tx["trade_value"] * tx["currency"].map(fx_rates)
    cash_from_trades = (
        tx.groupby("date")["trade_value_c"]
          .sum()
          .reindex(nav.index, fill_value=0)
    )

    # 1b) cash from dividends
    div_flows = compute_daily_dividend_flows(df_div, fx_rates, nav.index)

    # 2) daily return
    inflows = cash_from_trades.add(div_flows, fill_value=0)
    prev_nav = nav.shift(1).replace(0, np.nan)
    daily_r = ((nav - prev_nav - inflows) / prev_nav).fillna(0)

    # 3) chain‐link into monthly returns (in %)
    monthly_raw = (daily_r + 1).groupby(daily_r.index.to_period("M")).prod().sub(1) * 100

    # 4) build full PeriodIndex
    if fy_start is None or fy_end is None:
        today = pd.Timestamp.now()
        full_periods = pd.period_range(
            start=pd.Timestamp(today.year, 1, 1),
            end=pd.Timestamp(today.year, 12, 31),
            freq="M"
        )
    else:
        full_periods = pd.period_range(start=fy_start, end=fy_end, freq="M")

    monthly_twr = monthly_raw.reindex(full_periods, fill_value=0)

    current_app.logger.debug(f"FY window: {fy_start} → {fy_end}, full months: {list(full_periods)}")
    current_app.logger.debug(f"Reindexed TWR:\n{monthly_twr}")

    return pd.DataFrame({
        "month":  monthly_twr.index.strftime("%b-%y"),
        "twr_pct": monthly_twr.values
    })
    