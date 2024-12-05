# Use the official Python image as a base
FROM python:3.12.7-slim

# Install Wine dependencies
RUN dpkg --add-architecture i386 && \
    apt-get update && \
    apt-get install -y \
    wine32 \
    wine64 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set the working directory in the container
WORKDIR /app

# Install Poetry
RUN pip install poetry

# Copy the Poetry configuration files
COPY pyproject.toml poetry.lock /app/

# Install dependencies using Poetry
RUN poetry install --no-root

# Copy the rest of the application files
COPY . /app/

# Expose the port FastAPI will run on
EXPOSE 8000

# Run the FastAPI app using Uvicorn
CMD ["python", "main.py"]
