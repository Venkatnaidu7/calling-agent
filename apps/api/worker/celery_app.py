from celery import Celery
from apps.api.config import settings

celery_app = Celery(
    "aicalling_worker",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=["apps.api.worker.tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,  # 1 hour hard limit
    worker_prefetch_multiplier=1,
)

if __name__ == "__main__":
    celery_app.start()
