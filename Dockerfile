# Use the official Python 3.12.7 slim image as the base
FROM python:3.12.7-slim

# Install required system dependencies and WINE
RUN dpkg --add-architecture i386 && \
    apt-get update && \
    apt-get install -y --no-install-recommends \
    software-properties-common \
    wget \
    gnupg2 && \
    wget -nc https://dl.winehq.org/wine-builds/winehq.key && \
    apt-key add winehq.key && \
    add-apt-repository "deb https://dl.winehq.org/wine-builds/debian/ $(lsb_release -cs) main" && \
    apt-get update && \
    apt-get install -y --no-install-recommends \
    winehq-stable \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Set environment variables for WINE to suppress interactive dialogs
ENV DEBIAN_FRONTEND=noninteractive
ENV WINEDEBUG=-all

# Create a working directory
WORKDIR /app

# Copy application code
COPY . /app

# Install Python dependencies
RUN pip install --no-cache-dir poetry
RUN poetry install --no-root

# Expose the port (Render will use $PORT)
EXPOSE 8000

# Run the server
CMD ["python", "main.py"]
