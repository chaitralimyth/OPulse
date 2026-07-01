# Stage 1: Build dependencies and wheels
FROM python:3.11-slim AS builder

WORKDIR /app

# Install system compilation dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

# Build dependencies in a local folder
RUN pip install --no-cache-dir --user -r requirements.txt

# Stage 2: Final minimal runtime environment
FROM python:3.11-slim AS runner

WORKDIR /app

# Install runtime database client shared libraries
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Copy installed site-packages from builder stage
COPY --from=builder /root/.local /root/.local
COPY requirements.txt .

ENV PATH=/root/.local/bin:$PATH
ENV PYTHONUNBUFFERED=1

# Copy project source files
COPY ./app ./app
COPY ./alembic.ini ./alembic.ini
COPY ./migrations ./migrations

EXPOSE 8000

# Start backend using uvicorn server
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
