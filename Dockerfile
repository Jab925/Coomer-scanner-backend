# Use Python base image
FROM python:3.9-slim

# Install system dependencies needed for insightface + gdown
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    cmake \
    libgl1-mesa-glx \
    libglib2.0-0 \
    unzip \
    && rm -rf /var/lib/apt/lists/*

# Set work directory
WORKDIR /app

# Install gdown and other Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir gdown

# Download buffalo_l.zip and extract it
RUN gdown --id 1yxiWQzsnpmh9DLO5R6CNaH4vmhYXmOYo -O /app/buffalo_l.zip && \
    unzip /app/buffalo_l.zip -d /app/buffalo_l && \
    rm /app/buffalo_l.zip

# Copy your app code into the container
COPY . .

# Expose port (optional, depending on your app)
EXPOSE 8080

# Command to run the app
CMD ["python", "main.py"]
