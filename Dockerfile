# Production Multi-Stage Dockerfile for CyberRFP Maroc
FROM python:3.14-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    TZ=Africa/Casablanca \
    DATABASE_PATH=/app/data/cyberrfp.db

WORKDIR /app

# Install system dependencies (curl, certificates, timezone data)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    tzdata \
    && rm -rf /var/lib/apt/lists/*

# Set Moroccan timezone
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# Install Python requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source & static assets
COPY . .

# Ensure data directory exists for persistent SQLite database and DCEs
RUN mkdir -p /app/data && (cp cyberrfp.db /app/data/cyberrfp.db || true)

# Expose HTTP port
EXPOSE 8000

# Health check to ensure API is responding and real-time scrapers are active
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
  CMD curl -f http://localhost:8000/api/tenders?limit=1 || exit 1

# Run FastAPI production server via Uvicorn
CMD ["uvicorn", "src.server:app", "--host", "0.0.0.0", "--port", "8000"]
