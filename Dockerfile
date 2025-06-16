# Use Python base image
FROM python:3.9-slim

# Install system dependencies needed for insightface + OpenCV
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    cmake \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Set work directory
WORKDIR /app

# Copy requirements first
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Extra packages for insightface (in case requirements.txt misses it)
RUN pip install --no-cache-dir \
    insightface \
    onnxruntime \
    opencv-python-headless \
    gdown

# Copy your app code
COPY . .

# Expose port
EXPOSE 8080

# Run app
CMD ["python", "main.py"]
