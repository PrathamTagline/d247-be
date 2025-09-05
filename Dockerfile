# Base image with Python 3.13
FROM python:3.13-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install system dependencies (Chromium + ChromeDriver + utils)
RUN apt-get update && apt-get install -y \
    wget \
    curl \
    gnupg \
    unzip \
    chromium \
    chromium-driver \
    && rm -rf /var/lib/apt/lists/*

# Explicit paths for Selenium
ENV CHROMIUM_PATH=/usr/bin/chromium
ENV CHROMEDRIVER_PATH=/usr/bin/chromedriver

# Set the working directory
WORKDIR /code

# Copy requirements.txt and install dependencies
COPY requirements.txt /code/
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire project
COPY . /code/

# Copy entrypoint
COPY entrypoint.sh /code/entrypoint.sh
RUN chmod +x /code/entrypoint.sh

# Expose port for Django app
EXPOSE 5001

# Default entrypoint
ENTRYPOINT ["/bin/sh", "/code/entrypoint.sh"]

# Default command (only used for web, Celery overrides this in docker-compose.yml)
CMD ["gunicorn", "backend.wsgi:application", "--bind", "0.0.0.0:5001"]
