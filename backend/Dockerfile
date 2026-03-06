# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Set the working directory in the container
WORKDIR /app

# The Tesseract installation is no longer needed and has been removed.

# Copy the requirements file into the container
COPY ./requirements.txt /app/requirements.txt

# Install the Python dependencies.
RUN pip install --no-cache-dir --upgrade -r /app/requirements.txt

# Copy our backend application code into the container.
COPY . /app

# The command to run our application.
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

