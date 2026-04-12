FROM python:3.11-slim

WORKDIR /app

# Install dependencies first (cached Docker layer)
COPY chip_floorplanner/server/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# Copy the entire project
COPY . /app/

ENV PYTHONPATH=/app

HEALTHCHECK --interval=30s --timeout=10s --start-period=20s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:7860/health')" || exit 1

EXPOSE 7860

CMD ["uvicorn", "chip_floorplanner.server.app:app", "--host", "0.0.0.0", "--port", "7860"]
