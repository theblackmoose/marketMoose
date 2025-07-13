"""
config.py – Configuration for MarketMoose

Defines:
- Base configuration for file paths, secrets, retries
- Mappings for exchange suffixes and currencies
- Benchmark index metadata
- Production-specific settings via ProdConfig
"""

import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")

# Ensure DATA_DIR exists on app startup
os.makedirs(DATA_DIR, exist_ok=True)

class BaseConfig:
    # SECURITY
    SECRET_KEY = os.environ.get("MARKETMOOSE_SECRET_KEY",
                                "MARKETMOOSE_SECRET_KEY")

    # DATA FILES
    TRANSACTIONS_FILE = os.environ.get("TRANSACTIONS_FILE") or os.path.join(DATA_DIR, "transactions.json")
    DIVIDENDS_FILE = os.environ.get("DIVIDENDS_FILE") or os.path.join(DATA_DIR, "dividends.json")

    CACHE_DIR = os.environ.get("CACHE_DIR", "stock_data_cache")

    # RETRY LOGIC
    MAX_RETRIES          = int(os.environ.get("MAX_RETRIES", "3"))
    BACKOFF_BASE_SECONDS = int(os.environ.get("BACKOFF_BASE_SECONDS", "15"))

# a simple mapping from exchange code to currency
EXCHANGE_CURRENCY = {
    "ASX":        "AUD",
    "BM&FBOVESPA":"BRL",
    "Euronext":  "EUR",
    "FWB":        "EUR",
    "HKEX":       "HKD",
    "JPX":        "JPY",
    "JSE":        "ZAR",
    "KRX":        "KRW",
    "LSE":        "GBP",
    "NSE":        "INR",
    "SGX":        "SGD",
    "SSE":        "CNY",
    "SZSE":       "CNY",
    "TSX":        "CAD",
    "TWSE":       "TWD",
    "NASDAQ":     "USD",
    "NYSE":       "USD",
}

CURRENCY_SYMBOLS = {
    "AUD": "A$",
    "USD": "US$",
    "EUR": "€",
    "GBP": "£",
    "JPY": "JP¥",
    "CAD": "C$",
    "SGD": "S$",
    "NZD": "NZ$",
    "CNY": "CN¥",
}

# Which suffix to append for each exchange so yfinance knows where to look
EXCHANGE_SUFFIX = {
    "ASX":        ".AX",
    "BM&FBOVESPA": ".SA",
    "Euronext":   "",      # Euronext tickers typically have no suffix
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
    "NASDAQ":     "",      # US exchanges have no suffix
    "NYSE":       "",      # US exchanges have no suffix
}

# Available benchmark indices (customizable by user)
BENCHMARKS = {
    "none": {"ticker": None, "label": "None"},
    "sp500": {"ticker": "^GSPC", "label": "S&P 500 (US)"},
    "asx200": {"ticker": "^AXJO", "label": "ASX 200 (AUS)"},
    "allord": {"ticker": "^AORD", "label": "ALL ORDINARIES (AUS)"}
}

class ProdConfig(BaseConfig):
    DEBUG = False
    CACHE_TYPE = "RedisCache"  
    # URL format: redis://[:password]@hostname:port/db_number
    CACHE_REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
    
