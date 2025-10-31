# Use an official Python base image
FROM python:3.11

# Set the working directory
WORKDIR /app

# Install dependencies
COPY requirements.txt .  
RUN pip install --no-cache-dir -r requirements.txt

# Install Ollama
RUN curl -fsSL https://ollama.com/install.sh | sh

# Copy the FastAPI application
COPY . .

# Expose the FastAPI port
EXPOSE 8000

# Ensure necessary directories exist
RUN mkdir -p /app/logs /app/uploaded_documents /app/faiss_index

# Start Ollama in the background and wait for it to be ready
RUN nohup ollama serve > /app/logs/ollama.log 2>&1 & \
    echo "Waiting for Ollama to start..." && \
    until curl -s http://localhost:11434/api/tags > /dev/null; do \
        sleep 2; \
        echo "Still waiting for Ollama..."; \
    done && \
    echo "Pulling model: llama3..." && \
    ollama pull llama3 && \
    echo "Ollama is ready!"

# Use the startup script as the entrypoint
CMD nohup ollama serve > /app/logs/ollama.log 2>&1 & sleep 5 && \
    uvicorn app:app --host 0.0.0.0 --port 8000 --workers 4