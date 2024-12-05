# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \

# Copy the current directory contents into the container at /app
COPY . /app

# Install Python dependencies
RUN pip install --no-cache-dir poetry
RUN poetry install --no-root

# Create necessary directories
RUN mkdir -p /app/uploads /app/converted

# Make port 8000 available to the world outside this container
EXPOSE 8000

# Define environment variable to ensure Python output is sent straight to terminal
ENV PYTHONUNBUFFERED=1

# Run the application
CMD ["python","main.py"]