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
  docker compose logs -f web
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

  <img src="https://private-user-images.githubusercontent.com/83482419/466832681-22078a48-1869-4f94-a392-6ee047433ffd.png?jwt=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJnaXRodWIuY29tIiwiYXVkIjoicmF3LmdpdGh1YnVzZXJjb250ZW50LmNvbSIsImtleSI6ImtleTUiLCJleHAiOjE3NTI2NDUzMDgsIm5iZiI6MTc1MjY0NTAwOCwicGF0aCI6Ii84MzQ4MjQxOS80NjY4MzI2ODEtMjIwNzhhNDgtMTg2OS00Zjk0LWEzOTItNmVlMDQ3NDMzZmZkLnBuZz9YLUFtei1BbGdvcml0aG09QVdTNC1ITUFDLVNIQTI1NiZYLUFtei1DcmVkZW50aWFsPUFLSUFWQ09EWUxTQTUzUFFLNFpBJTJGMjAyNTA3MTYlMkZ1cy1lYXN0LTElMkZzMyUyRmF3czRfcmVxdWVzdCZYLUFtei1EYXRlPTIwMjUwNzE2VDA1NTAwOFomWC1BbXotRXhwaXJlcz0zMDAmWC1BbXotU2lnbmF0dXJlPTA1NWE3ZDQ3YzdmMDNhYzA3NDIzNjMwMzcxMjIwNDMyMmRmZDcxMzYwNDczNzA3NWE1OGY2NmFhMDFmYmRmYjkmWC1BbXotU2lnbmVkSGVhZGVycz1ob3N0In0.3NUfgMmrNLGkBbiKhDmCTCzMaithorpkOZfMqNqha_4"/>

  <img src="https://private-user-images.githubusercontent.com/83482419/466832725-1b5ca9d3-7bcd-419e-8797-45be486ce1c3.png?jwt=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJnaXRodWIuY29tIiwiYXVkIjoicmF3LmdpdGh1YnVzZXJjb250ZW50LmNvbSIsImtleSI6ImtleTUiLCJleHAiOjE3NTI2NDY0NjEsIm5iZiI6MTc1MjY0NjE2MSwicGF0aCI6Ii84MzQ4MjQxOS80NjY4MzI3MjUtMWI1Y2E5ZDMtN2JjZC00MTllLTg3OTctNDViZTQ4NmNlMWMzLnBuZz9YLUFtei1BbGdvcml0aG09QVdTNC1ITUFDLVNIQTI1NiZYLUFtei1DcmVkZW50aWFsPUFLSUFWQ09EWUxTQTUzUFFLNFpBJTJGMjAyNTA3MTYlMkZ1cy1lYXN0LTElMkZzMyUyRmF3czRfcmVxdWVzdCZYLUFtei1EYXRlPTIwMjUwNzE2VDA2MDkyMVomWC1BbXotRXhwaXJlcz0zMDAmWC1BbXotU2lnbmF0dXJlPTA5ZTE2YTM5YTRmNjQzYWUxZjcyNDVhY2Q5YThkMWY2OGRmZGU5ZmE5MjQzZDA1MjRiYmNjYWQxZDM5ZWQyMGUmWC1BbXotU2lnbmVkSGVhZGVycz1ob3N0In0.p0mhuOUkZ_EV3iv39dXgv2-z5sqZ7UICZtAjkKGsUgM"/>

  <img src="https://private-user-images.githubusercontent.com/83482419/466832774-5630c0c4-c5bb-42bd-ae55-b0352efee028.png?jwt=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJnaXRodWIuY29tIiwiYXVkIjoicmF3LmdpdGh1YnVzZXJjb250ZW50LmNvbSIsImtleSI6ImtleTUiLCJleHAiOjE3NTI2NDY0NjEsIm5iZiI6MTc1MjY0NjE2MSwicGF0aCI6Ii84MzQ4MjQxOS80NjY4MzI3NzQtNTYzMGMwYzQtYzViYi00MmJkLWFlNTUtYjAzNTJlZmVlMDI4LnBuZz9YLUFtei1BbGdvcml0aG09QVdTNC1ITUFDLVNIQTI1NiZYLUFtei1DcmVkZW50aWFsPUFLSUFWQ09EWUxTQTUzUFFLNFpBJTJGMjAyNTA3MTYlMkZ1cy1lYXN0LTElMkZzMyUyRmF3czRfcmVxdWVzdCZYLUFtei1EYXRlPTIwMjUwNzE2VDA2MDkyMVomWC1BbXotRXhwaXJlcz0zMDAmWC1BbXotU2lnbmF0dXJlPWQ4M2EyZTJhYjE0MzlmMzgyZTI2NmIxMWFiYzM4NWQ1ZTQzYzNkZGMwMTIzNmRmYTVmNmU3ZGVmZjI2ODVkMWMmWC1BbXotU2lnbmVkSGVhZGVycz1ob3N0In0.ZeTTAraPNPbsXZJbgBE8sLw2ZPuW81h-6n--F03AsOc"/>

  <img src="https://private-user-images.githubusercontent.com/83482419/466832821-84cd4734-38f5-4fe6-bd96-339b8ce2ae64.png?jwt=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJnaXRodWIuY29tIiwiYXVkIjoicmF3LmdpdGh1YnVzZXJjb250ZW50LmNvbSIsImtleSI6ImtleTUiLCJleHAiOjE3NTI2NDY0NjEsIm5iZiI6MTc1MjY0NjE2MSwicGF0aCI6Ii84MzQ4MjQxOS80NjY4MzI4MjEtODRjZDQ3MzQtMzhmNS00ZmU2LWJkOTYtMzM5YjhjZTJhZTY0LnBuZz9YLUFtei1BbGdvcml0aG09QVdTNC1ITUFDLVNIQTI1NiZYLUFtei1DcmVkZW50aWFsPUFLSUFWQ09EWUxTQTUzUFFLNFpBJTJGMjAyNTA3MTYlMkZ1cy1lYXN0LTElMkZzMyUyRmF3czRfcmVxdWVzdCZYLUFtei1EYXRlPTIwMjUwNzE2VDA2MDkyMVomWC1BbXotRXhwaXJlcz0zMDAmWC1BbXotU2lnbmF0dXJlPTg2ZjA2YTU5NDlmYThmZTI5NmQ3MDQxYzUwMjU2NWQ1NWYyNjg2NmFiM2M2YjdkZWY3YmYyNmI0ZGUzNzA3MGQmWC1BbXotU2lnbmVkSGVhZGVycz1ob3N0In0.SnwaUv409X6hSPms4uqbeC7iPg-Vk3pN2QiK8toIff8"/>

  <img src="https://private-user-images.githubusercontent.com/83482419/466832913-302af751-1690-4572-a931-39c0131410b4.png?jwt=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJnaXRodWIuY29tIiwiYXVkIjoicmF3LmdpdGh1YnVzZXJjb250ZW50LmNvbSIsImtleSI6ImtleTUiLCJleHAiOjE3NTI2NDY0NjEsIm5iZiI6MTc1MjY0NjE2MSwicGF0aCI6Ii84MzQ4MjQxOS80NjY4MzI5MTMtMzAyYWY3NTEtMTY5MC00NTcyLWE5MzEtMzljMDEzMTQxMGI0LnBuZz9YLUFtei1BbGdvcml0aG09QVdTNC1ITUFDLVNIQTI1NiZYLUFtei1DcmVkZW50aWFsPUFLSUFWQ09EWUxTQTUzUFFLNFpBJTJGMjAyNTA3MTYlMkZ1cy1lYXN0LTElMkZzMyUyRmF3czRfcmVxdWVzdCZYLUFtei1EYXRlPTIwMjUwNzE2VDA2MDkyMVomWC1BbXotRXhwaXJlcz0zMDAmWC1BbXotU2lnbmF0dXJlPTY0MDczYmUyZDUxZmYyNTg3YmNlMzE2OWM2MDRmZDNhNzA4NmY4YTRjZmVkODBhM2JlNmFkOWEwYTNiMTgxZWMmWC1BbXotU2lnbmVkSGVhZGVycz1ob3N0In0.aXpjPCFtPwAFFBvxfTGHENOFle-q9_HQwgXPPJ5BaJk"/>

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

These survive restarts and rebuilds, using the `docker compose down` command.
They are only removed if you explicitly delete the volumes, using the `docker compose down -v` command.

- **View / Edit your data files**:

Because the files are in named volumes, use a helper container or the `exec` command.

Inspect volume mountpoints:

  ```sh
  docker volume ls

  docker volume inspect marketmoose_mm_data marketmoose_mm_stock_data_cache | grep Mountpoint
  ```

List files:

  ```sh
  docker compose exec web ls -lah /app/data

  docker compose exec web ls -lah /app/stock_data_cache
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
  ```

Restore on Linux:

  ```sh
  docker run --rm -v marketmoose_mm_data:/data -v ~/marketmoose_backups:/backup alpine \
    sh -lc 'cd /data && tar xzf /backup/mm_data_YYYYMMDD.tar.gz'

  docker run --rm -v marketmoose_mm_stock_data_cache:/stock_data_cache -v ~/marketmoose_backups:/backup alpine \
    sh -lc 'cd /stock_data_cache && tar xzf /backup/mm_stock_data_cache_YYYYMMDD.tar.gz'
  ```

  Verify the restore worked:

  ```sh
  docker run --rm -v marketmoose_mm_data:/data alpine ls -lah /data

  docker run --rm -v marketmoose_mm_stock_data_cache:/stock_data_cache alpine ls -lah /stock_data_cache
  ```

Backup on Windows:

  ```sh
  mkdir -p C:\Users\(username)\marketmoose_backups

  docker volume ls

  docker run --rm -v marketmoose_mm_data:/data -v "C:\Users\(username)\marketmoose_backups:/backup" alpine \
    sh -c "tar czf /backup/mm_data_$(date +%Y%m%d).tar.gz -C /data ."

  docker run --rm -v marketmoose_mm_stock_data_cache:/stock_data_cache -v "C:\Users\(username)\marketmoose_backups:/backup" alpine \
    sh -c "tar czf /backup/mm_stock_data_cache_$(date +%Y%m%d).tar.gz -C /stock_data_cache ."
  ```

Restore on Windows:

  ```sh

  docker volume ls

  docker run --rm -v marketmoose_mm_data:/data -v "C:\Users\(username)\marketmoose_backups:/backup" alpine \
    sh -lc "cd /data && tar xzf /backup/mm_data_(date).tar.gz"

  docker run --rm -v marketmoose_mm_stock_data_cache:/stock_data_cache -v "C:\Users\(username)\marketmoose_backups:/backup" alpine \
    sh -lc "cd /stock_data_cache && tar xzf /backup/mm_stock_data_cache_(date).tar.gz"
  ```

  Verify the restore worked:

  ```sh
  docker run --rm -v marketmoose_mm_data:/data alpine ls -lah /data

  docker run --rm -v marketmoose_mm_stock_data_cache:/stock_data_cache alpine ls -lah /stock_data_cache
  ```

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
      - mm_data:/app/data
      - mm_stock_data_cache:/app/stock_data_cache
volumes:
  redis_data:
  mm_data:
  mm_stock_data_cache:
```

The `web` service runs `exec gunicorn -w 4 -b 0.0.0.0:8000 marketMoose:app` by default, as defined in the entrypoint.sh.

---

## 👨‍💻 Contact

**theblackmoose** – [GitHub](https://github.com/theblackmoose)
