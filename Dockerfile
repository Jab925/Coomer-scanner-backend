# Use Python base image
FROM python:3.9-slim

# Install system dependencies needed to build insightface
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    cmake \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Set work directory
WORKDIR /app

# Copy requirements first for caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy your app code
COPY . .

# Expose port (optional, depending on your app)
EXPOSE 8080

# Command to run app
CMD ["python", "main.py"]
