FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p data logs

# Install the package in development mode
RUN pip install -e .

# Expose dashboard port
EXPOSE 8050

# Set environment variables
ENV PYTHONPATH=/app
ENV APP_DASHBOARD_HOST=0.0.0.0
ENV APP_DASHBOARD_PORT=8050

# Default command (can be overridden)
CMD ["python", "-m", "src.weather_pipeline.cli", "dashboard"]