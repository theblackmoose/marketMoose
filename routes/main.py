"""
main.py - Main route definitions for MarketMoose.

Handles request routing, form submissions, dashboard rendering,
transaction and dividend CRUD, data export, and dashboard data computation.
"""

import json
import os
import uuid
import time
import pandas as pd
from datetime import datetime
from flask import g
from flask import (
    Blueprint,
    request,
    render_template,
    redirect,
    url_for,
    flash,
    make_response,
    current_app,
)
from contextlib import contextmanager
from services.transactions import load_transactions, save_transaction
from services.yf_cache import download_stock_data
from services.dividends import load_dividends, save_dividend, delete_dividends
from services.portfolio import (
    get_portfolio_value_history,
    get_portfolio_return_history,
    calculate_portfolio_value_asof,
    calculate_cost_basis_invested,
    calculate_returned_summary,
    compute_dividends,
)
from services.fx import calculate_fx_rates, get_fy_dates
from helpers import dataframe_to_json, render_empty_dashboard, get_benchmark_return_history
from services.pl_calendar import pl_calendar_for_cached
from config import BENCHMARKS, EXCHANGE_SUFFIX, EXCHANGE_CURRENCY, CURRENCY_SYMBOLS

def timed_step(label, func, *args, **kwargs):
    """Times and logs the execution of a function call with the given label."""
    start = time.time()
    result = func(*args, **kwargs)
    elapsed = time.time() - start
    current_app.logger.info(f"[PROFILE] {label} took {elapsed:.3f} seconds.")
    return result

@contextmanager
def log_timing(label: str):
    """Context manager to time a block of code and log the duration with the given label."""
    start = time.perf_counter()
    try:
        yield
    finally:
        elapsed = time.perf_counter() - start
        current_app.logger.info(f"[PROFILE] {label} took {elapsed:.3f} seconds.")

main_bp = Blueprint("main", __name__)

@main_bp.app_context_processor
def inject_currency_symbols():
    # now in every template you can do currency_symbols[code]
    return dict(currency_symbols=CURRENCY_SYMBOLS)

def _handle_delete(request, tx_file, order_by, display_currency, selected_fy, market_value_period, selected_benchmark, current_tab):
    """Handles deletion of one or more transactions and redirects back to the dashboard."""
    ids_to_delete = request.form.getlist("delete_ids")
    df = load_transactions()
    current_app.logger.info(f"Deleting transaction IDs: {ids_to_delete}")

    # Filter out the selected transactions and save the updated dataset
    df = df[~df["id"].isin(ids_to_delete)]
    if "date" in df.columns:
        df["date"] = df["date"].dt.strftime("%Y-%m-%d")

    try:
        with open(tx_file, "w") as f:
            json.dump(df.to_dict(orient="records"), f, indent=2)
        current_app.logger.info(f"Deleted {len(ids_to_delete)} transaction(s).")
        flash(f"Deleted {len(ids_to_delete)} transaction(s).", "warning")
    except Exception as e:
        current_app.logger.error(f"Failed to write transactions file '{tx_file}': {e}")
        flash("Could not delete transactions. Please try again.", "danger")

    return redirect(
        url_for(
            "main.index",
            order_by=order_by,
            display_currency=display_currency,
            fy=selected_fy,
            market_value_period=market_value_period,
            benchmark=selected_benchmark,
            current_tab=current_tab,
        )
        + "#transactions"
    )

def _handle_new_transaction(request, order_by, display_currency, selected_fy, market_value_period, selected_benchmark, current_tab):
    """Validates and saves a new transaction entry submitted via form."""
    raw_symbol = request.form["tx_symbol"].strip().upper()
    symbol = raw_symbol.replace(".", "-")
    side = request.form["tx_side"]
    shares_n = float(request.form["tx_shares"])
    shares = -abs(shares_n) if side == "sell" else shares_n

    price = float(request.form["tx_price"])
    fee = float(request.form["tx_fee"])
    date_str = request.form["tx_date"]
    exch = request.form["tx_exchange"]

    # Validate ticker via yfinance
    suffix = EXCHANGE_SUFFIX.get(exch, "")
    yf_symbol = f"{symbol}{suffix}"
    ticker = __import__("yfinance").Ticker(yf_symbol) 
    try:
        info = ticker.info or {}
    except Exception as e:
        current_app.logger.warning(f"YFinance info lookup failed for {yf_symbol}: {e}")
        info = {}

    if not info.get("regularMarketPrice"):
        current_app.logger.warning(f"Symbol not found: {raw_symbol} on {exch}")
        flash(
            f"❌ Symbol “{raw_symbol}” not found on {exch}. Please check the ticker.",
            "danger",
        )
        return redirect(
            url_for(
                "main.index",
                order_by=order_by,
                display_currency=display_currency,
                fy=selected_fy,
                market_value_period=market_value_period,
                benchmark=selected_benchmark,
                current_tab=current_tab,
            )
            + "#transactions"
        )

    # Compute trade values/costs
    raw_value = shares * price
    total_value = round(raw_value, 2)
    raw_cost = raw_value + fee
    total_cost = round(raw_cost, 2)
    currency = EXCHANGE_CURRENCY.get(exch, "USD")

    data = {
        "id": str(uuid.uuid4()),
        "symbol": symbol,
        "shares": shares,
        "side": side,
        "price": price,
        "trade_value": total_value,
        "currency": currency,
        "date": date_str,
        "exchange": exch,
        "broker_fee": fee,
        "trade_cost": total_cost,
    }

    try:
        save_transaction(data)
        flash("Transaction saved.", "success")
        # trigger yfinance cache for this one ticker
        try:
            download_stock_data([(symbol, exch)], force_refresh=False)
            current_app.logger.info(f"Triggered cache update for {symbol}{suffix}")
        except Exception as e:
            current_app.logger.warning(f"Cache update failed for {symbol}{suffix}: {e}")
    except Exception as e:
        current_app.logger.error(f"Error saving transaction: {e}")
        flash("Could not save transaction. Please try again.", "danger")

    return redirect(
        url_for(
            "main.index",
            order_by=order_by,
            display_currency=display_currency,
            fy=selected_fy,
            market_value_period=market_value_period,
            benchmark=selected_benchmark,
            current_tab=current_tab,
        )
        + "#transactions"
    )

def _load_transactions_for(selected_fy):
    """
    Loads and filters transactions for the selected financial year.
    Returns the raw dataset, calculation subset, table subset, and relevant dates.
    """
    df_tx = load_transactions().sort_values("date", ascending=True)
    current_app.logger.debug(f"Loaded {len(df_tx)} transactions from JSON.")

    # Add a 'fy' column for financial year classification (based on July–June fiscal year)
    if not df_tx.empty:
        df_tx["fy"] = df_tx["date"].apply(
            lambda dt: f"{(dt.year if dt.month >= 7 else dt.year - 1)}/{(dt.year if dt.month >= 7 else dt.year - 1) + 1}"
        )
    else:
        df_tx["fy"] = []
    fy_choices = ["All"] + sorted(df_tx["fy"].unique())

    if selected_fy != "All":
        fy_start, fy_end = get_fy_dates(selected_fy)
        asof_date = fy_end
        df_tx_for_calc = df_tx[df_tx["date"] <= fy_end].copy()
        df_tx_for_table = df_tx[
            (df_tx["date"] >= fy_start) & (df_tx["date"] <= fy_end)
        ].copy()
        current_app.logger.debug(
            f"Filtering transactions for FY {selected_fy}: "
            f"rows for calculation={len(df_tx_for_calc)}, "
            f"rows for table={len(df_tx_for_table)}"
        )
    else:
        fy_start, fy_end = None, None
        asof_date = datetime.now().date()
        df_tx_for_calc = df_tx.copy()
        df_tx_for_table = df_tx.copy()
        current_app.logger.debug("No FY filter applied; using all transactions.")

    return df_tx, df_tx_for_calc, df_tx_for_table, fy_choices, fy_start, fy_end, asof_date

def _handle_new_dividend(request, order_by, display_currency, selected_fy, market_value_period, selected_benchmark, current_tab):
    """Handles form submission for a new dividend record and saves it."""
    symbol = request.form["div_symbol"].strip().upper().replace(".", "-")
    date_str = request.form["div_date"]
    dividend_amount = float(request.form["div_amount"])  
    currency = request.form["div_currency"]

    data = {
        "id": str(uuid.uuid4()),
        "symbol": symbol,
        "date": date_str,
        "dividend_amount": dividend_amount, 
        "currency": currency,
    }

    try:
        save_dividend(data)
        current_app.logger.info(f"Saved new dividend: {data}")
        flash("Dividend saved.", "success")
    except Exception as e:
        current_app.logger.error(f"Could not save dividend: {e}")
        flash("Could not save dividend. Please try again.", "danger")

    return redirect(
        url_for(
            "main.index",
            order_by=order_by,
            display_currency=display_currency,
            fy=selected_fy,
            market_value_period=market_value_period,
            benchmark=selected_benchmark,
            current_tab=current_tab,
        )
        + "#dividends"
    )

def _handle_delete_dividends(request, order_by, display_currency, selected_fy, market_value_period, selected_benchmark, current_tab):
    """Deletes selected dividend records and redirects back to the dividends tab."""
    ids_to_delete = request.form.getlist("delete_ids")
    try:
        delete_dividends(ids_to_delete)
        current_app.logger.info(f"Deleted dividend IDs: {ids_to_delete}")
        flash(f"Deleted {len(ids_to_delete)} dividend record(s).", "warning")
    except Exception as e:
        current_app.logger.error(f"Error deleting dividends: {e}")
        flash("Could not delete dividends. Please try again.", "danger")

    return redirect(
        url_for(
            "main.index",
            order_by=order_by,
            display_currency=display_currency,
            fy=selected_fy,
            market_value_period=market_value_period,
            benchmark=selected_benchmark,
            current_tab=current_tab,
        )
        + "#dividends"
    )
    
def _compute_dashboard_data(
    df_tx_for_calc,
    df_tx_for_table,
    asof_date,
    order_by,
    display_currency,
    selected_benchmark,
    fy_choices,
    selected_fy,
    fy_start,
    fy_end,
):
    """
    Computes and assembles all data needed for the dashboard view.
    Includes portfolio values, FX rates, dividends, benchmark returns,
    live prices, broker fees, and P/L calendar.
    """
    if hasattr(g, 'dashboard_data_cache'):
        current_app.logger.info("Using cached dashboard data for this request")
        return g.dashboard_data_cache
    
    current_app.logger.info("Computing dashboard data...")

    # --- Phase 1: Calculate cost basis and returned value summaries ---
    with log_timing("calculate_cost_basis_invested"):
        invested_summary = calculate_cost_basis_invested(df_tx_for_calc)
    with log_timing("calculate_returned_summary"):
        returned_summary = calculate_returned_summary(df_tx_for_calc)

    current_app.logger.debug(f"Invested summary: {invested_summary}")
    current_app.logger.debug(f"Returned summary: {returned_summary}")

    # --- Phase 2: FX Rates ---
    src_currencies = set(invested_summary.keys()) | {display_currency}
    with log_timing("calculate_fx_rates"):
        fx_rates = calculate_fx_rates(src_currencies, display_currency)
    current_app.logger.info(f"FX rates after calculation: {fx_rates}")
    if fx_rates is None:
        current_app.logger.error("FX rates is None after calculation_fx_rates!")
        raise ValueError("FX rates returned None")

    # --- Phase 3: Dividends ---
    # Load dividends dataframe
    df_div = load_dividends()

    if df_div.empty:
        df_div_for_calc = pd.DataFrame(columns=["id", "symbol", "date", "dividend_amount", "currency"])
    else:
        # Filter dividends by selected financial year (like transactions)
        if fy_start and fy_end:
            df_div_for_calc = df_div[
                (df_div["date"] >= fy_start) & (df_div["date"] <= fy_end)
            ].copy()
        else:
            df_div_for_calc = df_div.copy()

    # Calculate total dividends by currency for filtered dividends
    if not df_div_for_calc.empty:
        total_dividends_by_currency = df_div_for_calc.groupby("currency")["dividend_amount"].sum().round(2).to_dict()
    else:
        total_dividends_by_currency = {}

    # Compute total dividends per symbol (used in portfolio valuation)
    dividends_per_symbol = compute_dividends(df_tx_for_calc, df_div_for_calc, fx_rates)
    total_dividends = round(sum(dividends_per_symbol.values()), 2)
    current_app.logger.debug(f"Computed dividends per symbol: {dividends_per_symbol}")

    # --- Phase 4: Portfolio as-of Date ---
    with log_timing("calculate_portfolio_value_asof"):
        portfolio, total_value_converted, total_change_amt, total_change_pct = calculate_portfolio_value_asof(
            df_tx_for_calc, fx_rates, asof_date, dividends_per_symbol
        )
    
    # build a mapping symbol → transaction currency
    symbol_currency = (
        df_tx_for_table
        .drop_duplicates(subset="symbol", keep="last")
        .set_index("symbol")["currency"]
        .to_dict()
    )

    # stick that currency code onto each portfolio row
    for row in portfolio:
        # fallback to your display_currency if somehow missing
        row["original_currency"] = symbol_currency.get(row["symbol"], display_currency)

    current_app.logger.info(
        f"Portfolio as of {asof_date}: value={total_value_converted}, change={total_change_pct}%"
    )

    # --- Phase 5: Portfolio Sorting ---
    reverse_order = order_by in [
        "shares",
        "live_value",
        "trade_cost",
        "dividends",
        "change_amount",
        "change_pct",
    ]
    if portfolio:
        if order_by in portfolio[0]:
            portfolio = sorted(portfolio, key=lambda x: x[order_by], reverse=reverse_order)
        else:
            portfolio = sorted(portfolio, key=lambda x: x["symbol"])

    fy_end_str = asof_date.strftime("%Y-%m-%d") if asof_date else ""

    # --- Phase 6: Time Series (NAV) with earliest-FY special-case ---
    # figure out which FY is the very first one on disk
    non_all = [fy for fy in fy_choices if fy != "All"]
    # sort by the calendar year of that FY’s start (e.g. "2022/2023" → 2022)
    non_all.sort(key=lambda fy: int(fy.split("/")[0]))
    earliest_fy = non_all[0] if non_all else None

    # only pass start_date=fy_start when we're on that earliest FY;
    # otherwise leave it None so get_portfolio_value_history returns everything up to fy_end
    nav_start = fy_start if selected_fy == earliest_fy else None

    with log_timing("get_portfolio_value_history"):
        full_nav_df = get_portfolio_value_history(
            df_tx_for_calc,
            fx_rates,
            start_date=nav_start,
            end_date=fy_end,
        )
    full_nav_df["date"] = pd.to_datetime(full_nav_df["date"]).dt.normalize()

    if selected_fy == "All":
        # All transactions → no slicing
        value_history_df = full_nav_df

    else:
        # slice to this FY’s July 1→fy_end window
        window = full_nav_df[full_nav_df["date"] >= fy_start].copy()

        # if there’s no point exactly on July 1, prepend a flat baseline there
        if not window["date"].eq(fy_start).any():
            _, nav0, _, _ = calculate_portfolio_value_asof(
                df_tx_for_calc, fx_rates, fy_start, dividends_per_symbol
            )
            baseline = pd.DataFrame({
                "date":        [fy_start],
                "total_value": [nav0]
            })
            window = pd.concat([baseline, window], ignore_index=True)
            window = window.drop_duplicates(subset="date", keep="first")

        value_history_df = window

    value_history_json = dataframe_to_json(value_history_df)

    # --- Phase 7: Return History with earliest-FY special-case ---
    # figure out which FY is the very first one on disk
    non_all = [fy for fy in fy_choices if fy != "All"]
    non_all.sort(key=lambda fy: int(fy.split("/")[0]))
    earliest_fy = non_all[0] if non_all else None

    # only pass start_date=fy_start when we're on that earliest FY
    return_start = fy_start if selected_fy == earliest_fy else None

    with log_timing("get_portfolio_return_history"):
        full_return_df = get_portfolio_return_history(
            df_tx_for_calc,
            fx_rates,
            start_date=return_start,
            end_date=fy_end,
        )
    full_return_df["date"] = pd.to_datetime(full_return_df["date"]).dt.normalize()

    if selected_fy == "All":
        # All-transactions → keep everything
        return_history_df = full_return_df

    else:
        # slice to this FY’s July 1 → fy_end window
        window = full_return_df[
            (full_return_df["date"] >= fy_start) &
            (full_return_df["date"] <= fy_end)
        ].copy()

        # if there’s no zero-point on July 1, prepend it
        if not window["date"].eq(pd.to_datetime(fy_start)).any():
            baseline = pd.DataFrame({
                "date":             [fy_start],
                "return":           [0.0],
                "benchmark_return": [0.0],
            })
            window = pd.concat([baseline, window], ignore_index=True)
            window = window.drop_duplicates(subset="date", keep="first")

        return_history_df = window

    return_history_json = dataframe_to_json(return_history_df)

    # --- Phase 8: Benchmark Return Series ---
    with log_timing("get_benchmark_return_history"):
        if fy_start and fy_end:
            end_for_benchmark = max(fy_end, pd.Timestamp.now().normalize())
            benchmark_df = get_benchmark_return_history(fy_start, end_for_benchmark, benchmark=selected_benchmark)
        else:
            all_dates = pd.to_datetime(df_tx_for_calc["date"])
            start_for_benchmark = all_dates.min()
            end_for_benchmark = max(all_dates.max(), pd.Timestamp.now().normalize())
            benchmark_df = get_benchmark_return_history(start_for_benchmark, end_for_benchmark, benchmark=selected_benchmark)

    if not benchmark_df.empty:
        benchmark_json = benchmark_df.to_json(orient="records")
        current_app.logger.info(f"Fetched benchmark data for {selected_benchmark}")
    else:
        benchmark_json = "[]"
        current_app.logger.info(f"No benchmark data for {selected_benchmark}")

    # Phase 9: Extract latest available prices from cached CSVs as of `asof_date`
    price_mapping = {}
    for sym, exch in (
        df_tx_for_table.drop_duplicates(subset="symbol", keep="last")
        .set_index("symbol")["exchange"]
        .to_dict()
        .items()
    ):
        suffix = EXCHANGE_SUFFIX.get(exch, "")
        cache_file = os.path.join(current_app.config["CACHE_DIR"], f"{sym}{suffix}.csv")
        if os.path.exists(cache_file):
            dfp = pd.read_csv(cache_file, parse_dates=["Date"], index_col="Date")
            dfp.index = pd.to_datetime(dfp.index, utc=True).tz_convert(None).normalize()
            price_rows = dfp[dfp.index <= pd.Timestamp(asof_date)]
            last_close = price_rows["Close"].iloc[-1] if not price_rows.empty else None
            price_mapping[(sym, exch)] = last_close
        else:
            price_mapping[(sym, exch)] = None

    if not df_tx_for_table.empty:
        df_tx_for_table["live_price"] = df_tx_for_table.apply(
            lambda tx: price_mapping.get((tx.symbol, tx.exchange)), axis=1
        )
        df_tx_for_table["live_value"] = df_tx_for_table["live_price"] * df_tx_for_table["shares"]

    # --- Phase 10: Broker Fees ---
    if not df_tx_for_calc.empty:
        broker_fees_by_currency = (
            df_tx_for_calc.groupby("currency")["broker_fee"].sum().round(2).to_dict()
        )
    else:
        broker_fees_by_currency = {}

    # --- Phase 11: P/L Calendar with Caching ---
    current_app.logger.debug(
        f"PL calendar input — transactions from "
        f"{df_tx_for_calc['date'].min()} to {df_tx_for_calc['date'].max()}, "
        f"FY window from {fy_start} to {fy_end}"
    )
    
    with log_timing("pl_calendar_for_cached"):
        pl_calendar_json = pl_calendar_for_cached(df_tx_for_calc, fx_rates, fy_start, fy_end)
    current_app.logger.info("Computed P/L calendar JSON.")

    result = {
        "portfolio": portfolio,
        "total_value": total_value_converted,
        "total_change_amt": total_change_amt,
        "total_change_pct": total_change_pct,
        "invested_summary": invested_summary,
        "returned_summary": returned_summary,
        "dividends_table": df_div_for_calc.sort_values("date"),
        "total_dividends": total_dividends,
        "total_dividends_by_currency": total_dividends_by_currency,
        "value_history_json": value_history_json,
        "return_history_json": return_history_json,
        "benchmark_json": benchmark_json,
        "broker_fees_by_currency": broker_fees_by_currency,
        "pl_calendar_json": pl_calendar_json,
        "transactions_table": df_tx_for_table,
        "fy_end_str": fy_end_str,
    }
    
    g.dashboard_data_cache = result
    return result

@main_bp.route("/", methods=["GET", "POST"])
def index():
    """Main dashboard route. Handles GET for rendering and POST for adding/deleting transactions."""
    benchmark_choices = BENCHMARKS
    
    if request.method == "POST":
        # Read filters from form to preserve state on redirect
        order_by = request.form.get("order_by", "symbol")
        display_currency = request.form.get("display_currency", "AUD")
        selected_fy = request.form.get("fy", "All")
        market_value_period = request.form.get("market_value_period", "all")
        selected_benchmark = request.form.get("benchmark", "none")
        current_tab = request.form.get("current_tab", "transactions")

        tx_file = current_app.config["TRANSACTIONS_FILE"]

        if "delete_ids" in request.form:
            return _handle_delete(request, tx_file, order_by, display_currency, selected_fy, market_value_period, selected_benchmark, current_tab)
        if "tx_symbol" in request.form:
            return _handle_new_transaction(request, order_by, display_currency, selected_fy, market_value_period, selected_benchmark, current_tab)

    # For GET, read filters from args (URL)
    order_by = request.args.get("order_by", "symbol")
    display_currency = request.args.get("display_currency", "AUD")
    market_value_period = request.args.get("market_value_period", "all")
    selected_fy = request.args.get("fy", "All")
    selected_benchmark = request.args.get("benchmark", "none")
    current_tab = request.args.get("current_tab", "")

    # Load and filter transactions
    (
        df_tx,
        df_tx_for_calc,
        df_tx_for_table,
        fy_choices,
        fy_start,
        fy_end,
        asof_date,
    ) = _load_transactions_for(selected_fy)

    if df_tx.empty:
        current_app.logger.info("No transactions found; rendering empty dashboard.")
        return render_empty_dashboard(
            display_currency=display_currency,
            currency_choices=["AUD", "USD", "EUR", "GBP", "JPY", "CAD", "SGD", "NZD", "CNY"],
            transactions=df_tx,
            fy_choices=fy_choices,
            selected_fy=selected_fy,
            order_by=order_by,
            market_value_period=market_value_period,
            fy_end="",
            benchmark_choices=benchmark_choices,
            selected_benchmark=selected_benchmark,
        )

    # Compute everything else 
    data = _compute_dashboard_data(
        df_tx_for_calc,
        df_tx_for_table,
        asof_date,
        order_by,
        display_currency,
        selected_benchmark,
        fy_choices,
        selected_fy,
        fy_start,
        fy_end,
    )

    current_tab = request.args.get("current_tab", "")
    
    return render_template(
        "dashboard.html",
        portfolio=data["portfolio"],
        total_value=data["total_value"],
        total_change_amt=data["total_change_amt"],
        total_change_pct=data["total_change_pct"],
        display_currency=display_currency,
        currency_choices=["AUD", "USD", "EUR", "GBP", "JPY", "CAD", "SGD", "NZD", "CNY"],
        transactions=data["transactions_table"],
        fy_choices=fy_choices,
        selected_fy=selected_fy,
        invested_summary=data["invested_summary"],
        returned_summary=data["returned_summary"],
        order_by=order_by,
        dividends_table=data["dividends_table"],
        total_dividends=data["total_dividends"],
        total_dividends_by_currency=data["total_dividends_by_currency"],
        value_history_json=data["value_history_json"],
        return_history_json=data["return_history_json"],
        market_value_period=market_value_period,
        fy_end=data["fy_end_str"],
        broker_fees_by_currency=data["broker_fees_by_currency"],
        benchmark_json=data["benchmark_json"],
        benchmark_choices=benchmark_choices,
        selected_benchmark=selected_benchmark,
        pl_calendar_json=data["pl_calendar_json"],
        current_tab=current_tab,
    )

@main_bp.route("/dividends", methods=["POST"])
def dividends():
    """Handles creation and deletion of dividend records via POST requests."""
    # read filters from form, not args
    order_by = request.form.get("order_by", "symbol")
    display_currency = request.form.get("display_currency", "AUD")
    selected_fy = request.form.get("fy", "All")
    market_value_period = request.form.get("market_value_period", "all")
    selected_benchmark = request.form.get("benchmark", "none")
    current_tab = request.form.get("current_tab", "dividends")

    if "delete_ids" in request.form:
        return _handle_delete_dividends(request, order_by, display_currency, selected_fy, market_value_period, selected_benchmark, current_tab)
    if "div_symbol" in request.form:
        return _handle_new_dividend(request, order_by, display_currency, selected_fy, market_value_period, selected_benchmark, current_tab)

    return redirect(url_for("main.index"))

@main_bp.route("/export", methods=["GET"])
def export_transactions():
    """Exports filtered transactions as a downloadable CSV file."""
    selected_fy = request.args.get("fy", "All")
    df = load_transactions()
    current_app.logger.debug(f"Exporting transactions for FY {selected_fy}, total rows before filter: {len(df)}")

    df["fy"] = pd.to_datetime(df["date"]).apply(
        lambda dt: f"{(dt.year if dt.month >= 7 else dt.year - 1)}/{(dt.year if dt.month >= 7 else dt.year - 1) + 1}"
    )
    if selected_fy != "All":
        df = df[df["fy"] == selected_fy]
    df = df.sort_values("date", ascending=True).drop(columns=["fy"])
    csv_data = df.to_csv(index=False)

    resp = make_response(csv_data)
    resp.headers["Content-Disposition"] = f"attachment; filename=transactions_{selected_fy.replace('/', '-')}.csv"
    resp.headers["Content-Type"] = "text/csv"

    current_app.logger.info(f"Transactions exported for FY: {selected_fy} ({len(df)} rows)")
    return resp

@main_bp.route("/export_dividends", methods=["GET"])
def export_dividends():
    """Exports filtered dividends as a downloadable CSV file."""
    selected_fy = request.args.get("fy", "All")
    df_div = load_dividends()

    if selected_fy != "All":
        fy_start, fy_end = get_fy_dates(selected_fy)
        df_div = df_div[(df_div["date"] >= fy_start) & (df_div["date"] <= fy_end)].copy()

    df_div = df_div.sort_values("date", ascending=True)
    csv_data = df_div.to_csv(index=False)

    resp = make_response(csv_data)
    resp.headers["Content-Disposition"] = f"attachment; filename=dividends_{selected_fy.replace('/', '-')}.csv"
    resp.headers["Content-Type"] = "text/csv"
    return resp
