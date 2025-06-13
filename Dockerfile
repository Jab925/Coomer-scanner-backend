# Use a lightweight Python base image with build tools
FROM python:3.12-slim

# Install system dependencies needed for insightface and OpenCV
RUN apt-get update && apt-get install -y \
    libgl1 \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Copy the buffalo_l model directory into the image
# This assumes you have buffalo_l/ in your project root locally
COPY buffalo_l /app/buffalo_l

# Expose the port your app will run on
EXPOSE 8080

# Command to run your app
CMD ["python", "main.py"]
