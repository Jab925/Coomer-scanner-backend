# Use slim Python base image
FROM python:3.9-slim

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    cmake \
    libgl1-mesa-glx \
    libglib2.0-0 \
    unzip \
    curl && \
    rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Download and extract buffalo_l model
RUN curl -L "https://www.dropbox.com/scl/fi/6kpvzmv25fs3r2im5ztq9/buffalo_l.zip?rlkey=0nlgnsc9qkt6evwi8vwxcycnu&st=glukkdhq&dl=1" \
    -o buffalo_l.zip && \
    mkdir -p /app/buffalo_l && \
    unzip buffalo_l.zip -d /app/buffalo_l && \
    rm buffalo_l.zip

# Copy the app code
COPY . .

# Expose port
EXPOSE 8080

# Run app with Gunicorn with extended timeout to avoid worker timeouts
CMD ["gunicorn", "-w", "2", "-b", "0.0.0.0:8080", "--timeout", "120", "main:app"]
