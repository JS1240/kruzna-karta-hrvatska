# Backend Dockerfile
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV UV_CACHE_DIR=/tmp/uv-cache

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install uv
RUN pip install uv

# Set working directory
WORKDIR /app

# Copy project files
COPY pyproject.toml ./

# Install dependencies globally to avoid volume mount conflicts
RUN pip install fastapi uvicorn sqlalchemy psycopg2-binary pydantic pydantic-settings python-dotenv httpx beautifulsoup4 alembic playwright redis celery pandas scikit-learn python-jose passlib requests boto3 prometheus-client psutil cryptography qrcode python-dateutil stripe email-validator openai schedule

# Install playwright browsers
RUN playwright install --with-deps chromium

# Copy application code
COPY . .

# Create non-root user
RUN useradd --create-home --shell /bin/bash app && chown -R app:app /app
USER app

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Start the application  
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]