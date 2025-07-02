"""
transactions.py – Transaction persistence layer for MarketMoose

Provides:
- Loading transactions from a JSON file
- Saving a new transaction to the file

Always returns structured DataFrames, handles I/O exceptions gracefully,
and ensures the file remains usable even after data corruption.
"""

import json
import os
import logging
import pandas as pd

TRANSACTIONS_FILE = os.environ.get("TRANSACTIONS_FILE", "transactions.json")

def load_transactions():
    """
    Load the list of transactions from the JSON file specified in config, 'transactions.json'.
    Always returns a pandas.DataFrame, or an empty DataFrame with expected columns if none exist.
    """
    try:
        with open(TRANSACTIONS_FILE, "r") as f:
            tx_list = json.load(f)
    except (json.JSONDecodeError, FileNotFoundError) as e:
        logging.warning(f"Could not load transactions file '{TRANSACTIONS_FILE}': {e}. Resetting to empty list.")
        tx_list = []
        try:
            # If the file didn’t exist or was invalid JSON, overwrite it with an empty list
            with open(TRANSACTIONS_FILE, "w") as f2:
                json.dump([], f2, indent=2)
        except Exception as write_e:
            logging.error(f"Could not write empty transactions file '{TRANSACTIONS_FILE}': {write_e}")
    except Exception as e:
        logging.error(f"Unexpected error loading transactions from '{TRANSACTIONS_FILE}': {e}")
        tx_list = []

    # Convert to DataFrame
    if not tx_list:
        return pd.DataFrame(
            columns=[
                "id",
                "symbol",
                "shares",
                "side",
                "price",
                "trade_value",
                "currency",
                "date",
                "exchange",
                "broker_fee",
                "trade_cost",
            ]
        )

    df = pd.DataFrame(tx_list)
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"])
    return df

def save_transaction(data: dict):
    """
    Append a single transaction to the transaction file.
    Raises RuntimeError if writing fails.
    """
    try:
        # Open in r+ mode so the transaction file can be read and then overwrite
        with open(TRANSACTIONS_FILE, "r+") as f:
            tx_list = json.load(f)
            tx_list.append(data)
            f.seek(0)
            json.dump(tx_list, f, indent=2)
            f.truncate()
        logging.info(f"Saved new transaction to '{TRANSACTIONS_FILE}': {data}")
    except Exception as e:
        logging.error(f"Error saving transaction to '{TRANSACTIONS_FILE}': {e}")
        raise RuntimeError("Could not save transaction") from e
