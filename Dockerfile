FROM python:3.11-slim

# Install git for task sync
RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements first for better layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY *.py ./

# Create data directory mount point
RUN mkdir -p /data

# Set environment variables
ENV REPO_PATH=/data
ENV PYTHONUNBUFFERED=1

CMD ["python", "bot.py"]
