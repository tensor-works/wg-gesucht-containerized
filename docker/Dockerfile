# Use Python 3.9 slim as base image
FROM python:3.9-slim as builder
ARG WORKDIR_PATH=/app

# Install system dependencies, PostgreSQL, and Node.js
RUN apt-get update -qq -y && \
    apt-get install -y \
    libasound2 \
    libatk-bridge2.0-0 \
    libgtk-4-1 \
    libnss3 \
    xdg-utils \
    wget \
    unzip \
    curl \
    gnupg \
    gettext-base \
    postgresql postgresql-contrib && \
    curl -fsSL https://deb.nodesource.com/setup_18.x | bash - && \
    apt-get install -y nodejs && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Verify Node.js and npm installation
RUN node --version && npm --version

# Download and install Chrome
RUN wget -q -O chrome-linux64.zip https://bit.ly/chrome-linux64-121-0-6167-85 && \
    unzip chrome-linux64.zip && \
    mkdir -p /opt/chrome && \
    mv chrome-linux64/* /opt/chrome/ && \
    rm -rf chrome-linux64.zip chrome-linux64 && \
    ln -s /opt/chrome/chrome /usr/local/bin/chrome

# Download and install ChromeDriver
RUN wget -q -O chromedriver-linux64.zip https://bit.ly/chromedriver-linux64-121-0-6167-85 && \
    unzip -j chromedriver-linux64.zip chromedriver-linux64/chromedriver && \
    rm chromedriver-linux64.zip && \
    mv chromedriver /usr/local/bin/ && \
    chmod +x /usr/local/bin/chromedriver

# Set up Python environment
WORKDIR /workspaces

# Copy requirements and install Python dependencies
COPY docker/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && \
    playwright install chromium

# Set up PostgreSQL data directory for persistence
RUN mkdir -p /workspaces/wg-gesucht-containerized/pgdata && \ 
    chown postgres:postgres /workspaces/wg-gesucht-containerized/pgdata && \
    chmod 700 /workspaces/wg-gesucht-containerized/pgdata

USER postgres

# Initialize PostgreSQL database cluster
RUN /usr/lib/postgresql/15/bin/initdb -D /workspaces/wg-gesucht-containerized/pgdata

# Configure PostgreSQL to use the persistent data directory
RUN echo "data_directory = '/workspaces/wg-gesucht-containerized/pgdata'" >> /etc/postgresql/15/main/postgresql.conf

USER root

# Copy application code
COPY . .

# Copy the existing entrypoint.sh script from the etc directory
COPY etc/entrypoint.sh /etc/entrypoint.sh

# Ensure the entrypoint script is executable
RUN chmod +x /etc/entrypoint.sh

# Expose ports for both backend and frontend
EXPOSE 5000 3000

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV DISPLAY=:99
ENV PYTHONPATH="${PYTHONPATH}:/workspaces/wg-gesucht-containerized/backend/src:/workspaces/wg-gesucht-containerized/backend/"
ENV WORKDIR=${WORKDIR_PATH}
ENV NODE_ENV=production

# Set the entrypoint
ENTRYPOINT ["/etc/entrypoint.sh"]
