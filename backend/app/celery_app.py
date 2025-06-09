import os

from celery import Celery

from .core.config import settings

broker_url = os.getenv("CELERY_BROKER_URL", settings.redis_url)
backend_url = os.getenv("CELERY_RESULT_BACKEND", settings.redis_url)

celery_app = Celery("kruzna_karta", broker=broker_url, backend=backend_url)

# Route scraping tasks to a dedicated queue
celery_app.conf.task_routes = {"app.tasks.celery_tasks.*": {"queue": "scraping"}}
