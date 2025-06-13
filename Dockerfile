# Use official Python slim image
FROM python:3.12-slim

# Install system libraries required for OpenCV (cv2)
RUN apt-get update && \
    apt-get install -y --no-install-recommends libgl1-mesa-glx libglib2.0-0 && \
    rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose app port (optional, for clarity)
EXPOSE 8080

# Run the Flask app
CMD ["python", "main.py"]
