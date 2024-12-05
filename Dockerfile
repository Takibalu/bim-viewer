FROM python:3.12.7-slim

# Set the working directory in the container
WORKDIR /app

# Install Poetry
RUN pip install poetry

# Telepítjük az ifcopenshell Docker konténert
RUN apt-get update && apt-get install -y \
    docker.io

# Copy the Poetry configuration files
COPY pyproject.toml poetry.lock /app/

# Install dependencies using Poetry
RUN poetry install --no-root

# Copy the rest of the application files
COPY . /app/

# Expose the port FastAPI will run on
EXPOSE 8000

# Run the FastAPI app using Uvicorn
CMD ["poetry", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]