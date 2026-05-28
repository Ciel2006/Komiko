FROM python:3.12-slim

LABEL org.opencontainers.image.title="Komiko"
LABEL org.opencontainers.image.description="Self-hosted comics library platform"
LABEL org.opencontainers.image.source="https://github.com/komiko/komiko"

ENV KOMIKO_DATA_DIR=/data
ENV FLASK_ENV=production
ENV SECRET_KEY=change-me-in-production

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libxml2-dev libxslt1-dev && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p /data/covers

EXPOSE 5000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:5000/api/health')" || exit 1

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "--threads", "4", "--timeout", "120", "run:app"]