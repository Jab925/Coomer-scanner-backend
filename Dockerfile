# Use official Python slim image
FROM python:3.12-slim

# Install system packages needed for OpenCV + compiling insightface
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        libgl1-mesa-glx \
        libglib2.0-0 \
        build-essential \
        gcc \
        g++ \
        && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port (optional)
EXPOSE 8080

# Run app
CMD ["python", "main.py"]
