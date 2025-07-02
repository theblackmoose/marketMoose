"""
dividends.py – MarketMoose

Handles all logic related to reading, writing, and deleting dividend records.
Dividends are stored in a JSON file specified by the Flask app's DIVIDENDS_FILE config.
"""

import json
import pandas as pd
from flask import current_app

def load_dividends():
    """
    Loads the list of dividends from the JSON file and returns it as a DataFrame.
    If the file is missing or corrupt, an empty DataFrame with expected columns is returned.
    """
    file_path = current_app.config["DIVIDENDS_FILE"]
    try:
        with open(file_path, "r") as f:
            div_list = json.load(f)
    except (json.JSONDecodeError, FileNotFoundError) as e:
        current_app.logger.warning(f"Could not load dividends file '{file_path}': {e}. Resetting to empty list.")
        div_list = []
        # Attempt to reset the file to a valid empty list
        try:
            with open(file_path, "w") as f2:
                json.dump([], f2, indent=2)
        except Exception as write_e:
            current_app.logger.error(f"Could not write empty dividends file '{file_path}': {write_e}")
    except Exception as e:
        current_app.logger.error(f"Unexpected error loading dividends from '{file_path}': {e}")
        div_list = []

    # Return empty DataFrame with defined schema if no valid data
    if not div_list:
        return pd.DataFrame(columns=["id", "symbol", "date", "dividend_amount", "currency"])

    df = pd.DataFrame(div_list)
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"])
    return df

def save_dividend(data: dict):
    """
    Appends a single dividend record to the JSON file.
    Writes atomically using r+ and truncates after saving.
    """
    file_path = current_app.config["DIVIDENDS_FILE"]
    try:
        with open(file_path, "r+") as f:
            div_list = json.load(f)
            div_list.append(data)
            f.seek(0)
            json.dump(div_list, f, indent=2)
            f.truncate()
        current_app.logger.info(f"Saved new dividend to '{file_path}': {data}")
    except Exception as e:
        current_app.logger.error(f"Error saving dividend to '{file_path}': {e}")
        raise RuntimeError("Could not save dividend") from e

def delete_dividends(ids: list[str]):
    """
    Deletes dividends from the JSON file by matching IDs.
    """
    file_path = current_app.config["DIVIDENDS_FILE"]
    try:
        with open(file_path, "r+") as f:
            div_list = json.load(f)
            div_list = [d for d in div_list if d.get("id") not in ids]
            f.seek(0)
            json.dump(div_list, f, indent=2)
            f.truncate()
        current_app.logger.info(f"Deleted dividends: {ids}")
    except Exception as e:
        current_app.logger.error(f"Error deleting dividends from '{file_path}': {e}")
        raise RuntimeError("Could not delete dividends") from e
