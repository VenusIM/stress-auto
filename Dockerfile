FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    openssh-client \
    libffi-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY config.py .
COPY requirements.txt .
COPY main.py .
COPY .env .

RUN pip install --no-cache-dir -r requirements.txt

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "5"]