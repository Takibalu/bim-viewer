# Use an official Python image as the base
FROM python:3.12.7-slim

# Install dependencies and WINE for Linux
RUN dpkg --add-architecture i386 && \
    apt-get update && \
    apt-get install -y --no-install-recommends \
    software-properties-common \
    wget \
    gnupg2 \
    lsb-release \
    && wget -nc https://dl.winehq.org/wine-builds/winehq.key && \
    apt-key add winehq.key && \
    echo "deb https://dl.winehq.org/wine-builds/debian/ buster main" > /etc/apt/sources.list.d/winehq.list && \
    apt-get update && \
    apt-get install -y --no-install-recommends \
    winehq-stable \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Set environment variables for WINE
ENV DEBIAN_FRONTEND=noninteractive
ENV WINEDEBUG=-all

# Create a working directory
WORKDIR /app

# Copy application code
COPY . /app

# Install Python dependencies
RUN pip install --no-cache-dir poetry
RUN poetry install --no-root

# Expose the port
EXPOSE 8000

# Run the server
CMD ["python", "main.py"]
