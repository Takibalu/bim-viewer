# Use an official Python image as the base
FROM python:3.10-slim

# Install system dependencies, including WINE
RUN apt-get update && apt-get install -y --no-install-recommends \
    wine \
    wine32 \
    wine64 \
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
