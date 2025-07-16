<h1 align="center">
  <a href="https://github.com/theblackmoose/marketMoose">
    <img src="https://github.com/theblackmoose/marketMoose/blob/main/static/MarketMoose.png" 
    width="400" />
  </a>
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

- **Clone the repository**

  ```sh
  git clone https://github.com/theblackmoose/marketMoose.git
  ```
  ```sh
  cd marketMoose
  ```

  Note: For Windows users, you will be required to first install [Git for Windows](https://git-scm.com/downloads/win) to be able to run `git clone`.

- **Start Docker** 

  Ensure Docker Engine or Docker Desktop is running on your machine.

- **Start with Docker Compose**

  ```sh
  docker-compose up -d --build
  ```

  - **What happens:**
    - The Python environment and dependencies are installed inside the Docker image via the Dockerfile and requirements.txt.
    - Gunicorn launches the Flask application with 4 worker processes.
    - Redis service is available for caching.

- **Access the Dashboard** 

  Open a web browser at [http://localhost:30053](http://localhost:30053).

- **View application logs** (Optional)

  ```sh
  docker-compose logs -f web
  ```

- **Stopping**

  ```sh
  docker-compose down -v
  ```

---

<details>
  <summary>Click to view screenshots of Dashboard</summary>

<img src="https://private-user-images.githubusercontent.com/83482419/466832681-22078a48-1869-4f94-a392-6ee047433ffd.png?jwt=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJnaXRodWIuY29tIiwiYXVkIjoicmF3LmdpdGh1YnVzZXJjb250ZW50LmNvbSIsImtleSI6ImtleTUiLCJleHAiOjE3NTI2NDUzMDgsIm5iZiI6MTc1MjY0NTAwOCwicGF0aCI6Ii84MzQ4MjQxOS80NjY4MzI2ODEtMjIwNzhhNDgtMTg2OS00Zjk0LWEzOTItNmVlMDQ3NDMzZmZkLnBuZz9YLUFtei1BbGdvcml0aG09QVdTNC1ITUFDLVNIQTI1NiZYLUFtei1DcmVkZW50aWFsPUFLSUFWQ09EWUxTQTUzUFFLNFpBJTJGMjAyNTA3MTYlMkZ1cy1lYXN0LTElMkZzMyUyRmF3czRfcmVxdWVzdCZYLUFtei1EYXRlPTIwMjUwNzE2VDA1NTAwOFomWC1BbXotRXhwaXJlcz0zMDAmWC1BbXotU2lnbmF0dXJlPTA1NWE3ZDQ3YzdmMDNhYzA3NDIzNjMwMzcxMjIwNDMyMmRmZDcxMzYwNDczNzA3NWE1OGY2NmFhMDFmYmRmYjkmWC1BbXotU2lnbmVkSGVhZGVycz1ob3N0In0.3NUfgMmrNLGkBbiKhDmCTCzMaithorpkOZfMqNqha_4"/>

</details>

---

## ⚙️ Testing & Configuration

- **View Docker containers**:

  ```sh
  docker-compose ps
  ```

- **Shell Access**:

  ```sh
  docker-compose exec web sh
  ```

---

Place runtime settings in the `.env` file and reference them in `docker-compose.yml`. Key variables:

| Variable                | Description                               | Default                       |
| ----------------------- | ----------------------------------------- | ----------------------------- |
| `FLASK_ENV`             | Flask environment (`production`)          | `production`                  |
| `SECRET_KEY`            | Flask secret key                          | (none)                        |
| `REDIS_URL`             | Redis connection URL                      | `redis://redis:6379/0`        |
| `CACHE_DIR`             | Directory for file caching                | `/app/stock_data_cache`       |
| `TRANSACTIONS_FILE`     | Path to transactions JSON file            | `/app/data/transactions.json` |
| `DIVIDENDS_FILE`        | Path to dividends JSON file               | `/app/data/dividends.json`    |
| `EXCHANGE_SUFFIX`       | Suffix for ticker symbols (e.g. `.AX`)    | `ASX: .AX`, `JPX: .T,`, etc   |
| `BENCHMARKS`            | List of benchmark symbols                 | `^GSPC`, `^AXJO`, `^AORD`     |

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
