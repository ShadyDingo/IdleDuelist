# Use Python 3.11 slim image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port
EXPOSE 8000

# Set environment variable for Railway
ENV PORT=8000

# Debug: List files to verify correct files are present
RUN ls -la /app/

# Run the application
CMD ["python", "-m", "uvicorn", "full_web_server_simple:app", "--host", "0.0.0.0", "--port", "8000"]
