# Use Python base image
FROM python:3.9-slim

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    cmake \
    libgl1-mesa-glx \
    libglib2.0-0 \
    curl \
    unzip \
    && rm -rf /var/lib/apt/lists/*

# Set work directory
WORKDIR /app

# Copy Python requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app code
COPY . .

# Download model from Dropbox, extract, and clean up
RUN curl -L -o buffalo_l.zip "https://www.dropbox.com/scl/fi/6kpvzmv25fs3r2im5ztq9/buffalo_l.zip?rlkey=0nlgnsc9qkt6evwi8vwxcycnu&st=6sjlg1d3&dl=1" && \
    unzip buffalo_l.zip -d buffalo_l && \
    rm buffalo_l.zip

# Expose app port
EXPOSE 8080

# Run the app
CMD ["python", "main.py"]
