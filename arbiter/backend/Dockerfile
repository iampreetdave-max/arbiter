# Arbiter Backend - Dockerfile for Google Cloud Run

FROM python:3.11-slim

# Install system dependencies for WeasyPrint (PDF generation)
RUN apt-get update && apt-get install -y \
    libpango-1.0-0 \
    libpangoft2-1.0-0 \
    libharfbuzz0b \
    libffi-dev \
    libcairo2 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Cloud Run expects PORT env var
ENV PORT=8080

# Run the FastAPI app
CMD exec uvicorn main:app --host 0.0.0.0 --port ${PORT} --workers 1
