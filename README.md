<h1 align="center">
  <a href="https://github.com/theblackmoose/marketMoose">
    <img src="https://github.com/theblackmoose/marketMoose/blob/main/static/MarketMoose.png" 
    width="400" />
  </a>
  <br>MarketMoose<br>
</h1>

# MarketMoose

**Big antlers, big insights.**

MarketMoose is a containerised Flask application for tracking, analysing, and visualising your stock portfolio’s performance. It retrieves live and historical stock data, computes portfolio metrics, and presents interactive charts and tables, all served via Gunicorn in Docker containers.

---

## ✨ Features

- **Containerized Deployment:** Everything runs in Docker with a single `docker-compose up` command.
- **Gunicorn Server:** High-performance WSGI server for production-grade serving.
- **Portfolio Tracking:** Imports transactions to view current and historical holdings.
- **Time-Weighted Returns:** Monthly and daily time-weighted return calculations.
- **Live Pricing:** Fetches real-time prices using yfinance (with retry/backoff logic).
- **Historical Analysis:** View P/L calendars and return history, with benchmark comparisons.
- **Caching:** Redis caching to minimize API calls.

---

## 💡 Requirements

- Docker (20.10+)
- Docker Compose (1.29+)
- Docker Engine or Docker Desktop must be running

---

## 🚀 Installation & Usage

1. **Clone the repository**

  ```sh
  git clone https://github.com/theblackmoose/marketMoose.git
  ```
  ```sh
  cd marketMoose
  ```

  Note: For Windows users, you will be required to first install [Git for Windows](https://git-scm.com/downloads/win) to be able to run `git clone`.

2. **Start Docker** 

  Ensure Docker Engine or Docker Desktop is running on your machine.

3. **Start with Docker Compose**

  ```sh
  docker-compose up -d --build
  ```

  - **What happens:**
    - The Python environment and dependencies are installed inside the Docker image via the Dockerfile and requirements.txt.
    - Gunicorn launches the Flask application with 4 worker processes.
    - Redis service is available for caching.

4. **Access the Dashboard** 

  Open a web browser at [http://localhost:30053](http://localhost:30053).

5. **View application logs** (Optional)

  ```sh
  docker-compose logs -f web
  ```

6. **Stopping**

  ```sh
  docker-compose down -v
  ```

---

## ⚙️ Testing & Configuration

- **View Docker containers**:
  ```bash
  docker-compose ps
  ```
- **Shell Access**:
  ```bash
  docker-compose exec web sh
  ```

---

Place runtime settings in the `.env` file and reference them in `docker-compose.yml`. Key variables:

| Variable                | Description                               | Default                       |
| ----------------------- | ----------------------------------------- | ----------------------------- |
| `FLASK_ENV`             | Flask environment (`production`)          | `production`                  |
| `SECRET_KEY`            | Flask secret key                          | (none)                        |
| `ALPHA_VANTAGE_API_KEY` | Alpha Vantage API key for stock data      | (none)                        |
| `REDIS_URL`             | Redis connection URL                      | `redis://redis:6379/0`        |
| `CACHE_DIR`             | Directory for file caching                | `/app/stock_data_cache`       |
| `TRANSACTIONS_FILE`     | Path to transactions JSON file            | `/app/data/transactions.json` |
| `DIVIDENDS_FILE`        | Path to dividends JSON file               | `/app/data/dividends.json`    |
| `EXCHANGE_SUFFIX`       | Suffix for ticker symbols (e.g. `.AX`)    | `.AX`                         |
| `BENCHMARKS`            | Comma-separated list of benchmark symbols | (none)                        |

---

## 📄 Docker Compose References

```yaml
services:
  redis:
    image: redis:7
    restart: unless-stopped
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
  web:
    build: .
    image: marketmoose:latest
    restart: unless-stopped
    depends_on:
      - redis
    ports:
      - "30053:8000" # External port 30053 → Flask app inside container on port 8000
    environment:
      - TRANSACTIONS_FILE=/app/data/transactions.json
      - CACHE_DIR=/app/stock_data_cache
      - DIVIDENDS_FILE=/app/data/dividends.json
      - REDIS_URL=redis://redis:6379/0
      - FLASK_APP=marketMoose
    cap_drop:
      - ALL
    security_opt:
      - no-new-privileges:true
    read_only: true
    tmpfs:
      - /tmp
    volumes:
      - ./data:/app/data
      - ./stock_data_cache:/app/stock_data_cache
volumes:
  redis_data:
```

The `web` service runs `exec gunicorn -w 4 -b 0.0.0.0:8000 marketMoose:app` by default, as defined in the entrypoint.sh.

---

## 👨‍💻 Contact

**Jerome Bellavance** – [GitHub](https://github.com/theblackmoose)
