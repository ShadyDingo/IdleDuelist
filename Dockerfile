FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY backend_requirements.txt .
RUN pip install --no-cache-dir -r backend_requirements.txt

# Copy application code
COPY backend_server.py .
COPY network_manager.py .

# Create non-root user
RUN useradd --create-home --shell /bin/bash app
USER app

# Expose port
EXPOSE 8000

# Start the application
CMD ["uvicorn", "backend_server:app", "--host", "0.0.0.0", "--port", "8000"]
