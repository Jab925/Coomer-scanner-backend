FROM python:3.9-slim

# Install system dependencies including git
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    cmake \
    libgl1-mesa-glx \
    libglib2.0-0 \
    unzip \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Download and extract your model
RUN curl -L "https://www.dropbox.com/scl/fi/6kpvzmv25fs3r2im5ztq9/buffalo_l.zip?rlkey=0nlgnsc9qkt6evwi8vwxcycnu&st=glukkdhq&dl=1" \
    -o buffalo_l.zip && \
    mkdir -p /app/buffalo_l && \
    unzip buffalo_l.zip -d /app/buffalo_l && \
    rm buffalo_l.zip

# Copy the app code
COPY . .

EXPOSE 8080

CMD ["python", "main.py"]
