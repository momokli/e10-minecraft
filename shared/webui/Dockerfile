FROM python:3-slim
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends borgbackup && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY app.py .
COPY templates templates/
EXPOSE 5000
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "1", "--timeout", "30", "app:app"]
