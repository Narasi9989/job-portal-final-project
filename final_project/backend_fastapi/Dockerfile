#Multi-stage build for FastAPI backend

#Stage 1: Builder

FROM python:3.11-slim AS builder

WORKDIR /app

# Install build dependencies

RUN apt-get update && apt-get install -y --no-install-recommends \
build-essential \
gcc \
libpq-dev \
&& rm -rf /var/lib/apt/lists/*

# Copy requirements

COPY requirements.txt .

# Upgrade pip

RUN pip install --upgrade pip

# Install Python dependencies

RUN pip install --no-cache-dir --user -r requirements.txt

# Stage 2: Runtime

FROM python:3.11-slim

WORKDIR /app

# Install runtime dependencies

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    libaio-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy installed packages

COPY --from=builder /root/.local /root/.local

# Environment variables

ENV PATH="/root/.local/bin:$PATH"
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONPATH=/app

# Copy application source

COPY . .

# Create upload directories

RUN mkdir -p uploads/resumes

# Health check

HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 CMD curl -f http://localhost:8000/docs || exit 1

# Expose FastAPI port

EXPOSE 8000

# Start FastAPI

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]