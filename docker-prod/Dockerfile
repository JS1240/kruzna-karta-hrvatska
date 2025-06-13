# Multi-stage Dockerfile for production deployment

# --- Build frontend ---
FROM node:18 AS frontend-build
WORKDIR /frontend
COPY frontend/package*.json ./
RUN npm install
COPY frontend .
RUN npm run build

# --- Build backend ---
FROM python:3.11-slim AS backend-build
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential curl git && rm -rf /var/lib/apt/lists/*
RUN pip install uv
WORKDIR /app
COPY backend/pyproject.toml backend/uv.lock ./
RUN uv venv /app/.venv && uv sync
ENV PATH="/app/.venv/bin:$PATH"
COPY backend/app ./app

# --- Final image ---
FROM python:3.11-slim
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
RUN apt-get update && apt-get install -y --no-install-recommends nginx \
    && rm -rf /var/lib/apt/lists/*
RUN pip install uv
COPY --from=backend-build /app /app
COPY --from=frontend-build /frontend/dist /usr/share/nginx/html
COPY nginx/nginx.conf /etc/nginx/nginx.conf
COPY nginx/conf.d /etc/nginx/conf.d
COPY docker-prod/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
WORKDIR /app
EXPOSE 80
CMD ["/entrypoint.sh"]
