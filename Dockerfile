FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
# Note: Using direct pip install for simplicity in this submission
RUN pip install --no-cache-dir \
    openenv-core \
    fastapi \
    uvicorn \
    gradio \
    openai \
    websockets \
    python-dotenv \
    rich \
    pydantic

# Copy the project source
COPY . .

# Set environment variables for HF Spaces
ENV PYTHONUNBUFFERED=1
ENV PORT=7860

# Expose the application port
EXPOSE 7860

# Launch the Gradio + FastAPI server
CMD ["python", "chip_floorplanner/server/app.py"]
