# Base image with Python 3.13
FROM python:3.13-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV CHROME_BIN=/usr/bin/chromium
ENV CHROMEDRIVER=/usr/bin/chromedriver

# Set the working directory
WORKDIR /code

# Install dependencies for Chromium and ChromeDriver
RUN apt-get update && apt-get install -y \
    wget \
    curl \
    unzip \
    gnupg \
    chromium \
    chromium-driver \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements.txt and install Python dependencies
COPY requirements.txt /code/
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire project to the working directory
COPY . /code/

# Copy entrypoint
COPY entrypoint.sh /code/entrypoint.sh
RUN chmod +x /code/entrypoint.sh

# Expose the port the Django app runs on
EXPOSE 5001

# Set the entrypoint
ENTRYPOINT ["/bin/sh", "/code/entrypoint.sh"]

# Default command to run the Django development server
CMD ["gunicorn", "backend.wsgi:application", "--bind", "0.0.0.0:5001"]
