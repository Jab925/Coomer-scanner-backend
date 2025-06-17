FROM python:3.9-slim

# Install required system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    cmake \
    libgl1-mesa-glx \
    libglib2.0-0 \
    unzip \
    && rm -rf /var/lib/apt/lists/*

# Set workdir
WORKDIR /app

# Copy Python requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install gdown

# Copy app code
COPY . .

# Download model and extract
RUN gdown --id 1yxiWQzsnpmh9DLO5R6CNaH4vmhYXmOYo -O buffalo_l.zip && \
    unzip buffalo_l.zip -d buffalo_l && \
    rm buffalo_l.zip

EXPOSE 8080

CMD ["python", "main.py"]
