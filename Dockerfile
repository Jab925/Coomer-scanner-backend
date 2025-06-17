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

# Copy and install Python requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Download buffalo_l.zip from Google Drive and unzip it
# Replace the ID below if you change your Drive link
RUN curl -L -o buffalo_l.zip "https://drive.google.com/uc?export=download&id=1yxiWQzsnpmh9DLO5R6CNaH4vmhYXmOYo" && \
    unzip buffalo_l.zip && \
    rm buffalo_l.zip

# Copy your app code
COPY . .

# Expose port
EXPOSE 8080

# Run the app
CMD ["python", "main.py"]
