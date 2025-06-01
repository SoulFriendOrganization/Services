FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install dependencies for cloudflared
RUN apt-get update && apt-get install -y \
    curl \
    gnupg \
    && rm -rf /var/lib/apt/lists/*

# Add Cloudflare GPG key
RUN mkdir -p --mode=0755 /usr/share/keyrings \
    && curl -fsSL https://pkg.cloudflare.com/cloudflare-main.gpg | tee /usr/share/keyrings/cloudflare-main.gpg >/dev/null

# Add Cloudflare repo
RUN echo 'deb [signed-by=/usr/share/keyrings/cloudflare-main.gpg] https://pkg.cloudflare.com/cloudflared bookworm main' > /etc/apt/sources.list.d/cloudflared.list

# Install cloudflared based on architecture
RUN dpkg --print-architecture | grep -q "amd64" && \
    apt-get update && apt-get install -y cloudflared || \
    apt-get update && apt-get install -y cloudflared

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Command to run cloudflared and then the bot
CMD ["/bin/sh", "-c", "cloudflared access tcp --hostname postgresql.rikztech.my.id --url localhost:9222 & python main.py"]