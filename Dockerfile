# Use slim Python image
FROM python:3.9-slim

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    cmake \
    libgl1-mesa-glx \
    libglib2.0-0 \
    unzip \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set work directory
WORKDIR /app

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Download model
RUN curl -L "https://www.dropbox.com/scl/fi/6kpvzmv25fs3r2im5ztq9/buffalo_l.zip?rlkey=0nlgnsc9qkt6evwi8vwxcycnu&st=glukkdhq&dl=1" \
    -o buffalo_l.zip && \
    mkdir -p /app/buffalo_l && \
    unzip buffalo_l.zip -d /app/buffalo_l && \
    rm buffalo_l.zip

# Copy app code
COPY . .

# Expose port (Railway will dynamically assign, but no harm exposing 8080)
EXPOSE 8080

# Launch with Gunicorn (shell form CMD so ${PORT} is expanded)
CMD gunicorn --workers=1 --threads=2 --timeout=300 --bind=0.0.0.0:${PORT} main:app
