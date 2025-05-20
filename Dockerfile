# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set work directory
WORKDIR /app

# Install dependencies
COPY requirements.txt /app/
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Copy project
COPY . /app/

# Сделать entrypoint.sh исполняемым
RUN chmod +x /app/entrypoint.sh

# Создать необходимые директории
RUN mkdir -p /app/staticfiles /app/media

# Expose port 8080
EXPOSE 8080

# Run the application using entrypoint script
CMD ["/app/entrypoint.sh"] 