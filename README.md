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

- **Containerized Deployment:** Everything runs in Docker with a single `docker compose up` command.
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
  docker compose up -d --build
  ```

  - **What happens:**
    - The Python environment and dependencies are installed inside the Docker image via the Dockerfile and requirements.txt.
    - Gunicorn launches the Flask application with 4 worker processes.
    - Redis service is available for caching.

- **Access the Dashboard** 

  Open a web browser at [http://localhost:30053](http://localhost:30053).

- **View application logs** (Optional)

  ```sh
  docker compose exec web tail -n +1 -f /app/logs/error.log
  ```

- **Stopping**

  ```sh
  docker compose stop
  ```

- **Remove containers** (data persists)

  ```sh
  docker compose down
  ```

- **Remove containers AND volumes** (All data is deleted)

  ```sh
  docker compose down -v
  ```

---

<details>
  <summary>Click to view screenshots of Dashboard</summary>

  <img src="https://github.com/theblackmoose/marketMoose/blob/main/static/466832681-22078a48-1869-4f94-a392-6ee047433ffd.png"/>

  <img src="https://github.com/theblackmoose/marketMoose/blob/main/static/466832725-1b5ca9d3-7bcd-419e-8797-45be486ce1c3.png"/>

  <img src="https://github.com/theblackmoose/marketMoose/blob/main/static/466832774-5630c0c4-c5bb-42bd-ae55-b0352efee028.png"/>

  <img src="https://github.com/theblackmoose/marketMoose/blob/main/static/466832821-84cd4734-38f5-4fe6-bd96-339b8ce2ae64.png"/>

  <img src="https://github.com/theblackmoose/marketMoose/blob/main/static/466832913-302af751-1690-4572-a931-39c0131410b4.png"/>

</details>

---

## ⚙️ Testing & Configuration

- **View Docker containers**:

  ```sh
  docker compose ps
  ```

- **Shell Access**:

  ```sh
  docker compose exec web sh
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

## 💾 Persistent Files & Volumes

- **Persistent Files**:

Docker Compose uses named volumes stored in the following locations:

mm_data → mounted at /app/data (transactions.json, dividends.json, etc.)

mm_stock_data_cache → mounted at /app/stock_data_cache (yfinance cache)

mm_logs → mounted at /app/logs (error.log and access.log)

These survive restarts and rebuilds, using the `docker compose down` command.
They are only removed if you explicitly delete the volumes, using the `docker compose down -v` command.

- **View / Edit your data files**:

Because the files are in named volumes, use a helper container or the `exec` command.

Inspect volume mountpoints:

  ```sh
  docker volume ls

  docker volume inspect marketmoose_mm_data marketmoose_mm_stock_data_cache marketmoose_mm_logs | grep Mountpoint
  ```

List files:

  ```sh
  docker compose exec web ls -lah /app/data

  docker compose exec web ls -lah /app/stock_data_cache

  docker compose exec web ls -lah /app/logs
  ```

Open a shell in the running container and edit:

  ```sh
  docker compose exec web sh

  nano /app/data/transactions.json
  ```

- **Backup & Restore volumes**:

Backup on Linux:

  ```sh
  mkdir -p ~/marketmoose_backups

  docker volume ls

  docker run --rm -v marketmoose_mm_data:/data -v ~/marketmoose_backups:/backup alpine \
    tar czf /backup/mm_data_$(date +%Y%m%d).tar.gz -C /data .

  docker run --rm -v marketmoose_mm_stock_data_cache:/stock_data_cache -v ~/marketmoose_backups:/backup alpine \
    tar czf /backup/mm_stock_data_cache_$(date +%Y%m%d).tar.gz -C /stock_data_cache .

  docker run --rm -v marketmoose_mm_logs:/logs -v ~/marketmoose_backups:/backup alpine \
    tar czf /backup/mm_logs_$(date +%Y%m%d).tar.gz -C /logs .
  ```

Restore on Linux:

  ```sh
  docker run --rm -v marketmoose_mm_data:/data -v ~/marketmoose_backups:/backup alpine \
    sh -lc 'cd /data && tar xzf /backup/mm_data_YYYYMMDD.tar.gz'

  docker run --rm -v marketmoose_mm_stock_data_cache:/stock_data_cache -v ~/marketmoose_backups:/backup alpine \
    sh -lc 'cd /stock_data_cache && tar xzf /backup/mm_stock_data_cache_YYYYMMDD.tar.gz'

  docker run --rm -v marketmoose_mm_logs:/logs -v ~/marketmoose_backups:/backup alpine \
    sh -lc 'cd /logs && tar xzf /backup/mm_logs_YYYYMMDD.tar.gz'
  ```

  Verify the restore worked:

  ```sh
  docker run --rm -v marketmoose_mm_data:/data alpine ls -lah /data

  docker run --rm -v marketmoose_mm_stock_data_cache:/stock_data_cache alpine ls -lah /stock_data_cache

  docker run --rm -v marketmoose_mm_logs:/logs alpine ls -lah /logs
  ```

Backup on Windows:

  ```sh
  mkdir -p C:\Users\(username)\marketmoose_backups

  docker volume ls

  docker run --rm -v marketmoose_mm_data:/data -v "C:\Users\(username)\marketmoose_backups:/backup" alpine \
    sh -c "tar czf /backup/mm_data_$(date +%Y%m%d).tar.gz -C /data ."

  docker run --rm -v marketmoose_mm_stock_data_cache:/stock_data_cache -v "C:\Users\(username)\marketmoose_backups:/backup" alpine \
    sh -c "tar czf /backup/mm_stock_data_cache_$(date +%Y%m%d).tar.gz -C /stock_data_cache ."

  docker run --rm -v marketmoose_mm_logs:/logs -v "C:\Users\(username)\marketmoose_backups:/backup" alpine \
    sh -c "tar czf /backup/mm_logs_$(date +%Y%m%d).tar.gz -C /logs ."
  ```

Restore on Windows:

  ```sh

  docker volume ls

  docker run --rm -v marketmoose_mm_data:/data -v "C:\Users\(username)\marketmoose_backups:/backup" alpine \
    sh -lc "cd /data && tar xzf /backup/mm_data_(date).tar.gz"

  docker run --rm -v marketmoose_mm_stock_data_cache:/stock_data_cache -v "C:\Users\(username)\marketmoose_backups:/backup" alpine \
    sh -lc "cd /stock_data_cache && tar xzf /backup/mm_stock_data_cache_(date).tar.gz"

  docker run --rm -v marketmoose_mm_logs:/logs -v "C:\Users\(username)\marketmoose_backups:/backup" alpine \
    sh -lc "cd /logs && tar xzf /backup/mm_logs_(date).tar.gz"
  ```

  Verify the restore worked:

  ```sh
  docker run --rm -v marketmoose_mm_data:/data alpine ls -lah /data

  docker run --rm -v marketmoose_mm_stock_data_cache:/stock_data_cache alpine ls -lah /stock_data_cache

  docker run --rm -v marketmoose_mm_logs:/logs alpine ls -lah /logs
  ```

---

## 📄 Docker Compose References

```yaml
services:
  redis:
    image: redis:7
    restart: unless-stopped
    logging:
      driver: "json-file"
      options:
        max-size: "10m"   # Rotate after 10 MB
        max-file: "5"     # Keep 5 rotated files (50 MB total)
    networks:
      - internal # Redis only on internal network
    volumes:
      - redis_data:/data
  web:
    build: .
    image: marketmoose:latest
    restart: unless-stopped
    depends_on:
      - redis
    ports:
      - "127.0.0.1:30053:8000" # External port 30053 → Flask app inside container on port 8000
    logging:
      driver: "json-file"
      options:
        max-size: "10m"   # Rotate after 10 MB
        max-file: "5"     # Keep 5 rotated files (50 MB total)
    environment:
      - TRANSACTIONS_FILE=/app/data/transactions.json
      - CACHE_DIR=/app/stock_data_cache
      - DIVIDENDS_FILE=/app/data/dividends.json
      - REDIS_URL=redis://redis:6379/0
      - FLASK_APP=marketMoose
    networks:
      - internal # Can reach Redis
      - external # Can accept incoming connections
    cap_drop:
      - ALL
    security_opt:
      - no-new-privileges:true
    read_only: true
    tmpfs:
      - /tmp
    volumes:
      - mm_data:/app/data
      - mm_stock_data_cache:/app/stock_data_cache
      - mm_logs:/app/logs
volumes:
  redis_data:
  mm_data:
  mm_stock_data_cache:
  mm_logs:
networks:
  internal:
    driver: bridge
    internal: true # Redis lives here, no external access
  external:
    driver: bridge # Web container accepts connections through this
```

The `web` service runs `exec gunicorn -w 4 -b 0.0.0.0:8000 --access-logfile /app/logs/access.log --error-logfile /app/logs/error.log marketMoose:app` by default, as defined in the entrypoint.sh.

---

## 👨‍💻 Contact

**theblackmoose** – [GitHub](https://github.com/theblackmoose)
