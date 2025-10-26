# Use Python 3.12 base image
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install system dependencies for building packages
RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    libffi-dev \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency files
COPY pyproject.toml poetry.lock requirements.txt* /app/

# Upgrade pip and install dependencies
RUN pip install --upgrade pip setuptools wheel

# If you use Poetry
RUN pip install "poetry==2.1.3"
RUN poetry config virtualenvs.create false
RUN poetry install --no-root --only main

# Copy the rest of the code
COPY . /app

# Set environment variables if needed
ENV PYTHONUNBUFFERED=1

# Run the bot
CMD ["python", "bot.py"]
