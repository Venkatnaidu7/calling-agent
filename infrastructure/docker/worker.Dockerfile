FROM python:3.12-slim AS builder

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PATH="/home/aicalling/.local/bin:${PATH}"

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

RUN useradd -m -s /bin/bash aicalling
USER aicalling

COPY --chown=aicalling:aicalling pyproject.toml ./
RUN pip install --user build && pip install --user -e .

COPY --chown=aicalling:aicalling . .

CMD ["python", "-m", "celery", "-A", "apps.api.worker.celery_app", "worker", "--loglevel=info"]
