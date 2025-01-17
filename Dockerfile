# Use the official Python base image
FROM python:3.12

# Set the working directory
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN apt-get update
RUN apt-get install -y libpq-dev
RUN pip install --upgrade pip

# Install Spacy
RUN pip install -U pip setuptools wheel
RUN pip install spacy==3.7.5
RUN python -m spacy download zh_core_web_trf

# RUN pip install spacy
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY . .

# Expose the port the app will run on
EXPOSE 8000
