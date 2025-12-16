# Rasa Backend Dockerfile
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    coreutils \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Create models directory
RUN mkdir -p /app/models

# Copy application code
COPY . .

# Expose port
EXPOSE 5005

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:5005/health || exit 1

# Create startup script
RUN cat > /app/start.sh << 'SCRIPT_END'
#!/bin/bash
echo "=== Rasa Backend Startup ==="
echo "Checking for existing Rasa model..."

# Always train fresh model - no corrupted models to deal with
echo "Training fresh Rasa model..."
echo "Creating models directory..."
mkdir -p /app/models

# Remove any existing models to ensure fresh training
rm -f /app/models/*.tar.gz 2>/dev/null || true

set +e
# Train with explicit output directory - use timeout to ensure completion
echo "Running: rasa train --force --skip-validation --out /app/models"
echo "This may take 1-2 minutes with optimized config (3 epochs)..."

# Run training with timeout (15 minutes max) and better error handling
echo "Training started at $(date)"
timeout 900 rasa train --force --skip-validation --out /app/models 2>&1 | tee /tmp/training.log
TRAIN_EXIT=$?

echo "Training finished at $(date)"
echo "Training exit code: $TRAIN_EXIT"

# Wait longer for file system to sync and all components to finish
# ResponseSelector needs to complete after DIETClassifier
echo "Waiting for all training components to complete and model file to be created..."
sleep 30

# Check training log to see if ResponseSelector finished
if grep -q "Finished training component.*ResponseSelector" /tmp/training.log 2>/dev/null; then
  echo "✅ ResponseSelector training completed"
else
  echo "⚠️  ResponseSelector may still be training, waiting longer..."
  sleep 30
fi

# Check if model was created - look in multiple locations
echo "Checking for model files..."
ls -la /app/models/ 2>&1 || true

# Check for model files in /app/models
MODEL_COUNT=$(find /app/models -name "*.tar.gz" 2>/dev/null | wc -l)
echo "Model files in /app/models: $MODEL_COUNT"

# Also check in /app root and move if found
ROOT_MODELS=$(find /app -maxdepth 1 -name "*.tar.gz" 2>/dev/null)
if [ -n "$ROOT_MODELS" ]; then
  echo "Found model files in /app root, moving to /app/models..."
  mkdir -p /app/models
  find /app -maxdepth 1 -name "*.tar.gz" -exec mv {} /app/models/ \; 2>/dev/null || true
  MODEL_COUNT=$(find /app/models -name "*.tar.gz" 2>/dev/null | wc -l)
fi

if [ "$MODEL_COUNT" -gt 0 ]; then
  echo "✅ Model created successfully ($MODEL_COUNT file(s))"
  ls -lh /app/models/*.tar.gz 2>/dev/null || true
else
  echo "⚠️⚠️⚠️  WARNING: No model files found after training ⚠️⚠️⚠️"
  echo "Training log tail (last 50 lines):"
  tail -50 /tmp/training.log 2>/dev/null || true
fi

set -e

# Verify model exists before starting server
if [ -d "/app/models" ]; then
  MODEL_FILES=$(find /app/models -name "*.tar.gz" 2>/dev/null)
  if [ -z "$MODEL_FILES" ]; then
    echo "WARNING: No model files found! Attempting to start server anyway..."
  else
    echo "Model verified, starting server..."
  fi
else
  echo "WARNING: Models directory not found! Attempting to start server anyway..."
fi

echo "Starting Rasa server on port 5005..."

# Try to load model explicitly if found
MODEL_FILE=$(find /app/models -name "*.tar.gz" 2>/dev/null | head -1)
if [ -n "$MODEL_FILE" ]; then
  echo "Loading model: $MODEL_FILE"
  exec rasa run --enable-api --cors "*" --port 5005 --debug --model "$MODEL_FILE"
else
  echo "No model file found, starting server (will try to load from models directory)..."
  exec rasa run --enable-api --cors "*" --port 5005 --debug
fi
SCRIPT_END

RUN chmod +x /app/start.sh

# Start Rasa server
CMD ["/app/start.sh"]
