FROM python:3.11-slim

# Environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8080

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc curl wget git \
    dnsutils iputils-ping \
    ca-certificates \
    && update-ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Create directories
RUN mkdir -p reports exports logs static/css static/js templates && \
    chmod -R 755 reports exports logs static templates

# Create user
RUN useradd --create-home --shell /bin/bash --uid 1000 app && \
    chown -R app:app /app

USER app

EXPOSE $PORT

# Health check
HEALTHCHECK --interval=30s --timeout=15s --start-period=45s --retries=3 \
    CMD curl -f http://localhost:$PORT/api/health || exit 1

# Single worker with extended timeout
CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 180 --keep-alive 5 --max-requests 1000 app:app
