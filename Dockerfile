# Enhanced SEO Audit Tool V3.0 - Python 3.11 Dockerfile
# FIXED for Python 3.13 compatibility issues

FROM python:3.11.9-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    FLASK_ENV=production \
    PORT=5000 \
    PYTHONPATH=/app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies with explicit Python 3.11 compatibility
RUN python -m pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p logs reports exports cache static/img templates

# Set proper permissions
RUN chmod +x run.py || true && \
    chmod -R 755 static/ || true && \
    chmod -R 755 templates/ || true

# Create non-root user for security
RUN adduser --disabled-password --gecos '' appuser && \
    chown -R appuser:appuser /app
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:$PORT/api/health || exit 1

# Expose port
EXPOSE 5000

# Run the application
CMD ["python", "app.py"]
