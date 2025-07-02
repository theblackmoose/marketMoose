"""
marketMoose.py – Flask app factory and entry point

Initializes the MarketMoose application, including:
- Flask config loading
- Cache initialization (e.g., Redis)
- Logging setup (Gunicorn-aware)
- Blueprint registration
- Error handler for uncaught exceptions
"""

import os
import json
import logging
from flask import Flask, render_template, flash
from flask_caching import Cache
from config import ProdConfig, EXCHANGE_SUFFIX, EXCHANGE_CURRENCY, BENCHMARKS

cache = Cache()

def create_app():
    """
    Flask application factory for MarketMoose.

    This function:
    - Loads production configuration
    - Initializes Flask-Caching
    - Ensures required directories and files exist
    - Configures YFinance cache path
    - Hooks into Gunicorn’s logging (if available)
    - Registers main and optional API blueprints
    - Adds a catch-all error handler
    """
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(ProdConfig)

    # ───────────────────────────────
    # 1) Add these three into app.config
    # ───────────────────────────────
    app.config["EXCHANGE_SUFFIX"]   = EXCHANGE_SUFFIX
    app.config["EXCHANGE_CURRENCY"]  = EXCHANGE_CURRENCY
    app.config["BENCHMARKS"]        = BENCHMARKS

    # ───────────────────────────────
    # 2) Make sure CACHE_DIR exists
    # ───────────────────────────────
    os.makedirs(app.config["CACHE_DIR"], exist_ok=True)

    # ───────────────────────────────
    # 3) Ensure TRANSACTIONS_FILE exists
    # ───────────────────────────────
    transactions_path = app.config["TRANSACTIONS_FILE"]
    if not os.path.exists(transactions_path):
        with open(transactions_path, "w") as f:
            json.dump([], f)

    # ───────────────────────────────
    # 4) Configure YFinance cache under CACHE_DIR / "yf_cache"
    # ───────────────────────────────
    YF_CACHE_DIR = os.path.join(app.config["CACHE_DIR"], "yf_cache")
    os.makedirs(YF_CACHE_DIR, exist_ok=True)
    import yfinance as yf
    yf.set_tz_cache_location(YF_CACHE_DIR)

    cache.init_app(app)
    app.logger.info(f"Cache initialized with backend: {cache.cache}")
    
    # ───────────────────────────────
    # 5) Attach Gunicorn’s handlers to Flask’s logger
    # ───────────────────────────────
    # If running under Gunicorn, “gunicorn.error” will exist.
    gunicorn_logger = logging.getLogger("gunicorn.error")
    if gunicorn_logger.handlers:
        # Replace Flask’s default handlers with Gunicorn’s
        app.logger.handlers = []
        app.logger.handlers.extend(gunicorn_logger.handlers)
        app.logger.setLevel(gunicorn_logger.level)

        # Clear root logger’s handlers before assigning
        root_logger = logging.getLogger()
        root_logger.handlers = []
        root_logger.handlers.extend(gunicorn_logger.handlers)
        root_logger.setLevel(gunicorn_logger.level)

        # Prevent double propagation from submodules
        logging.getLogger("marketMoose").propagate = False

    # ───────────────────────────────
    # 6) Register Blueprints
    # ───────────────────────────────
    from routes.main import main_bp
    app.register_blueprint(main_bp)

    try:
        from api import api_bp
        app.register_blueprint(api_bp, url_prefix="/api")
    except ImportError:
        pass
    
    # ───────────────────────────────
    # 7) Global error handler
    # ───────────────────────────────
    # Catches all unhandled exceptions and logs the full traceback.
    @app.errorhandler(Exception)
    def handle_exception(e):
        app.logger.error("Unhandled exception:", exc_info=True)
        flash("An unexpected error occurred. Please check the logs or try again.", "danger")
        return render_template("error.html"), 500

    return app

app = create_app()
