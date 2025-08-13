FROM python:3.11-slim

# Set Python environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PIP_NO_CACHE_DIR=1
ENV PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libffi-dev \
    libssl-dev \
    libpq-dev \
    postgresql-client \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip and install build tools
RUN pip install --no-cache-dir --upgrade pip setuptools wheel

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Environment variables (production defaults - can be overridden at runtime)
ENV ENVIRONMENT=prod
ENV DATABASE_TYPE=postgresql
ENV DATABASE_URL=""
ENV SECRET_KEY=""
ENV JWT_SECRET_KEY=""
ENV CORS_ORIGINS=""

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/api/v1/health || exit 1

# Run the application with database initialization
CMD ["sh", "-c", "python scripts/init_database.py && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
