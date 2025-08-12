# syntax=docker/dockerfile:1
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN apt-get update && apt-get install -y curl sqlite3 && rm -rf /var/lib/apt/lists/* \
    && pip install --no-cache-dir -r requirements.txt

COPY services/user-service /app

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
