# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    HF_HUB_DISABLE_SYMLINKS_WARNING=1

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt .

# 1. Install CPU-only PyTorch to reduce image size and memory usage
RUN pip install --no-cache-dir torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu

# 2. Install the rest of the dependencies
RUN pip install --no-cache-dir -r requirements.txt

# 3. Pre-bake the model weights during the Docker build process
# This ensures the container starts instantly without downloading the model on cold start
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')"

# Copy the rest of the backend source code
COPY . .

# Expose the API port
EXPOSE 8000

# Command to run the application (uses PORT env variable provided by cloud hosts like Render/Koyeb, defaults to 8000)
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"]
