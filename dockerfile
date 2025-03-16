# Use official Python image as base
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    FLASK_APP=run.py

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libjpeg-dev \
    zlib1g-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements files and install dependencies
COPY requirements.txt tests/test_requirements.txt ./
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir -r test_requirements.txt && \
    pip install --no-cache-dir gunicorn==21.2.0

# Copy project files
COPY . .

# Create uploads directory with proper permissions
RUN mkdir -p uploads/images && chmod 777 uploads

# Create an entry script
RUN echo '#!/bin/bash\n\
set -e\n\
# Run migrations\n\
flask db upgrade\n\
# Start the app\n\
exec gunicorn --bind 0.0.0.0:5000 --workers 4 --threads 8 --timeout 120 "run:app"' > /app/entrypoint.sh && \
    chmod +x /app/entrypoint.sh

# Create a script for running tests
RUN echo '#!/bin/bash\n\
cd /app\n\
python -m pytest --cov=app tests/ -v "$@"' > /app/run_tests.sh && \
    chmod +x /app/run_tests.sh

# Expose the port
EXPOSE 5000

# Run the entry script by default
ENTRYPOINT ["/app/entrypoint.sh"]