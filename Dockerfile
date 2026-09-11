# ==========================================================
# Stage 1: Build Frontend React SPA
# ==========================================================
FROM node:20-alpine AS frontend-builder
WORKDIR /app/frontend

COPY frontend/package*.json ./
RUN npm install

COPY frontend/ ./
RUN npm run build

# ==========================================================
# Stage 2: Production Python Backend + Unified Static Serving
# ==========================================================
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000

WORKDIR /app

# Install system dependencies for image processing & raster libraries
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libtiff-dev \
    libjpeg-dev \
    zlib1g-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY backend/requirements.txt ./backend/requirements.txt
RUN pip install --no-cache-dir -r ./backend/requirements.txt

# Copy Backend Application
COPY backend ./backend

# Copy Built Frontend from Stage 1 into /app/frontend/dist
COPY --from=frontend-builder /app/frontend/dist ./frontend/dist

# Copy Sample Data and create required storage directories
COPY sample_data ./sample_data
RUN mkdir -p /app/uploads /app/evidence /app/data

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:${PORT}/health || exit 1

# Start production server
CMD python -m uvicorn backend.app.main:app --host 0.0.0.0 --port ${PORT}
