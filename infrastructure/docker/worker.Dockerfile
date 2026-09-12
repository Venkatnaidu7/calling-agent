FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY . .

RUN pip install --no-cache-dir .

RUN useradd -m -s /bin/bash aicalling && \
    chown -R aicalling:aicalling /app

USER aicalling

CMD ["python", "-m", "celery", "-A", "apps.api.worker.celery_app", "worker", "--loglevel=info"]
