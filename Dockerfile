FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create a startup script
RUN echo '#!/bin/bash\n\
echo "Waiting for database..."\n\
sleep 10\n\
echo "Initializing database..."\n\
export PYTHONPATH=/app:$PYTHONPATH\n\
python scripts/init_database.py\n\
echo "Starting application..."\n\
uvicorn app.main:app --host 0.0.0.0 --port 8001' > /app/start.sh

RUN chmod +x /app/start.sh

EXPOSE 8001

CMD ["/app/start.sh"]
