FROM node:22-slim

# Added 'build-essential' to compile native C++ Node modules (like better-sqlite3)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl wget git python3 python3-pip python3-full \
    chromium rclone mesa-va-drivers va-driver-all \
    build-essential \
    && pip3 install youtube-transcript-api --break-system-packages \
    && rm -rf /var/lib/apt/lists/*

# Install the absolute latest versions of the packages and immediately clear the bloat
RUN npm install -g openclaw@latest @tobilu/qmd@latest \
    && npm cache clean --force

# Create the dedicated user
RUN useradd -m -s /bin/bash claire

# Define environment variables before directory creation
ENV OPENCLAW_STATE_DIR=/home/claire/.openclaw
ENV XDG_CACHE_HOME=/home/claire/.openclaw/qmd/xdg-cache

# Pre-create the critical file paths and fix all ownership permissions
RUN mkdir -p /home/claire/.openclaw/agents/main/qmd/xdg-cache/qmd/models \
    && mkdir -p ${XDG_CACHE_HOME} \
    && chown -R claire:claire /home/claire

# Lock the container to the non-root user for security and execution
USER claire
WORKDIR /home/claire

EXPOSE 18790
CMD ["openclaw", "gateway"]

