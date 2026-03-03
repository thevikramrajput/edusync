FROM python:3.11-slim

# ─── System Dependencies ────────────────────────────────
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# ─── Working Directory ──────────────────────────────────
WORKDIR /app

# ─── Python Dependencies (cached layer) ─────────────────
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# ─── Copy Project ───────────────────────────────────────
COPY . .

# ─── Entrypoint ─────────────────────────────────────────
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 8000

ENTRYPOINT ["/entrypoint.sh"]
