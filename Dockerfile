# Base image with Python 3.13
FROM python:3.13-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set the working directory
WORKDIR /code

# Copy requirements.txt and install dependencies
COPY requirements.txt /code/
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire project to the working directory
COPY . /code/

# Expose the port the Django app runs on
EXPOSE 8000

# Set the entrypoint
ENTRYPOINT ["/bin/sh", "/code/entrypoint.sh"]

# Default command to run the Django development server
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
