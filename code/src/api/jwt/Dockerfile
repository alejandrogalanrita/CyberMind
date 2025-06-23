# Use Python 3.12.4 as the base image
FROM python:3.12.4

# Set the working directory in the container to /app
WORKDIR /app
ENV PYTHONPATH=/app

# Copy and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the CONTENTS of src/ into the container's /app
COPY /src/api/jwt .
COPY /resources/ ./resources/

# Expose app port
EXPOSE 80

# Set environment variables for Flask
ENV FLASK_APP=app.py
ENV FLASK_RUN_HOST=0.0.0.0
ENV FLASK_RUN_PORT=80
ENV FLASK_DEBUG=1

# Run the app
CMD ["flask", "run", "--host=0.0.0.0"]

