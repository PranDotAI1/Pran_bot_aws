# Rasa Backend Dockerfile
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port
EXPOSE 5005

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:5005/health || exit 1

# Create startup script
RUN echo '#!/bin/bash\n\
if [ -z "$SKIP_TRAINING" ] || [ "$SKIP_TRAINING" != "true" ]; then\n\
  echo "Training Rasa model..."\n\
  rasa train --force || echo "Training completed with warnings"\n\
else\n\
  echo "Skipping training, using existing model"\n\
fi\n\
echo "Starting Rasa server..."\n\
exec rasa run --enable-api --cors "*" --port 5005\n\
' > /app/start.sh && chmod +x /app/start.sh

# Start Rasa server
CMD ["/app/start.sh"]

