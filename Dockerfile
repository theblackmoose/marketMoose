# Dockerfile – MarketMoose Production Image
#
# Build structure:
# - Stage 1 ("builder"): Install Python packages inside a virtualenv
# - Stage 2 ("runtime"): Lightweight production image with only what's needed
#
# Highlights:
# - Uses Python 3.12-slim for minimal base image size
# - Creates a non-root user (marketmoose) for better security
# - Uses a read-only root filesystem (see docker-compose.yml for enforcement)
# - Entry point primes the cache and launches Gunicorn

# ─────────────────────────────────────────────────────────────────────────
# Stage 1: builder
# ─────────────────────────────────────────────────────────────────────────
FROM python:3.12.4-slim-bullseye@sha256:9a8f510466b54509a8e7d9d7bc300401d85537d5a08ed9131e389fcba50234b3 AS builder

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    REDIS_URL=redis://redis:6379/0

# Install build tools
RUN apt-get update \
 && apt-get upgrade -y \
 && apt-get install -y --no-install-recommends \
        build-essential gcc \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy only requirements first to leverage Docker cache
COPY requirements.txt .

# Create a virtualenv and install dependencies
RUN python3 -m venv /opt/venv \
 && . /opt/venv/bin/activate \
 && pip install --upgrade pip \
 && pip install --no-cache-dir -r requirements.txt

# Copy the entire project into /app
COPY . .

# ─────────────────────────────────────────────────────────────────────────
# Stage 2: runtime (smaller image)
# ─────────────────────────────────────────────────────────────────────────
FROM python:3.12.4-slim-bullseye@sha256:9a8f510466b54509a8e7d9d7bc300401d85537d5a08ed9131e389fcba50234b3 AS runtime

LABEL org.opencontainers.image.title="MarketMoose" \
      org.opencontainers.image.description="Containerised Flask-based stock portfolio dashboard" \
      org.opencontainers.image.version="1.0.0" \
      org.opencontainers.image.authors="theblackmoose" \
      org.opencontainers.image.source="https://github.com/yourname/marketmoose" \
      org.opencontainers.image.url="https://github.com/yourusername/marketmoose" \
      org.opencontainers.image.documentation="https://github.com/yourusername/marketmoose/wiki" 

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    REDIS_URL=redis://redis:6379/0 \
    FLASK_ENV=production

WORKDIR /app

# Copy the virtualenv from the builder stage
COPY --from=builder /opt/venv /opt/venv

# Copy only what the runtime needs from the builder stage:
COPY --from=builder /app/marketMoose.py     /app/
COPY --from=builder /app/api.py             /app/
COPY --from=builder /app/config.py          /app/
COPY --from=builder /app/entrypoint.sh      /app/
COPY --from=builder /app/helpers.py         /app/
COPY --from=builder /app/data               /app/data
COPY --from=builder /app/routes             /app/routes
COPY --from=builder /app/services           /app/services
COPY --from=builder /app/static             /app/static
COPY --from=builder /app/stock_data_cache   /app/stock_data_cache
COPY --from=builder /app/templates          /app/templates

# Make sure entrypoint.sh is executable
RUN chmod +x /app/entrypoint.sh

# Create a non-root user and chown everything to them
RUN useradd --create-home marketmoose \
 && chown -R marketmoose:marketmoose /app \
 && chown -R marketmoose:marketmoose /opt/venv

USER marketmoose

# Use the venv’s python & pip by prepending to PATH
ENV PATH="/opt/venv/bin:$PATH"

# Expose the same port the Flask (via Gunicorn) will bind to
EXPOSE 8000

# Entrypoint will prime the cache, then exec Gunicorn
ENTRYPOINT [ "/app/entrypoint.sh" ]
