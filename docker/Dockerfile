# Use Python 3.9 slim as base image
FROM python:3.9-slim as builder
ARG WORKDIR_PATH=/app

# Install system dependencies and Node.js
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
    gnupg && \
    # Add NodeSource repository
    curl -fsSL https://deb.nodesource.com/setup_18.x | bash - && \
    # Install Node.js and npm
    apt-get install -y nodejs && \
    # Clean up
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

# Copy application code
COPY . .

# Build the frontend
RUN cd frontend && \
    npm install && \
    npm run build && \
    npx shadcn@latest init --defaults -f && \
    npx shadcn@latest add card tabs button alert input badge textarea select

# Create directory for persistent data
RUN mkdir -p /app/data

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV DISPLAY=:99
ENV PYTHONPATH="${PYTHONPATH}:/workspaces/wg-gesucht-containerized/src"
ENV WORKDIR=${WORKDIR_PATH}
ENV NODE_ENV=production

# Create and configure entrypoint script
RUN echo '#!/bin/bash\n\
    mkdir -p /app/data\n\
    cd /app\n\
    # Start the frontend development server in the background\n\
    if [ "$NODE_ENV" = "development" ]; then\n\
    cd frontend && npm run dev & cd ..\n\
    fi\n\
    # Start the Python application\n\
    python wg-gesucht.py' > /app/entrypoint.sh && \
    chmod +x /app/entrypoint.sh

# Expose ports for both backend and frontend
EXPOSE 5000 3000

# Set the entrypoint
ENTRYPOINT ["/app/entrypoint.sh"]