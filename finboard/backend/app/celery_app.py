from celery import Celery
from app.config import get_settings

settings = get_settings()

celery_app = Celery(
    "finboard",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=[
        "app.tasks.stock_tasks",
        "app.tasks.crypto_tasks",
        "app.tasks.news_tasks",
        "app.tasks.overview_tasks",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Shanghai",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=300,
    task_soft_time_limit=240,
    worker_prefetch_multiplier=1,
    beat_schedule_filename="/tmp/celerybeat-schedule",
)

# Celery Beat schedule: when to run periodic tasks
celery_app.conf.beat_schedule = {
    # ===== A股行情 =====
    "fetch-a-stock-spot": {
        "task": "app.tasks.stock_tasks.fetch_a_stock_spot",
        "schedule": 3.0,  # every 3 seconds during trading hours
        "options": {"queue": "stock"},
    },
    "refresh-overview": {
        "task": "app.tasks.overview_tasks.refresh_overview",
        "schedule": 30.0,  # every 30 seconds — keeps dashboard fresh
        "options": {"queue": "stock"},
    },
    "fetch-a-stock-daily": {
        "task": "app.tasks.stock_tasks.fetch_a_stock_daily",
        "schedule": 3600.0,  # every hour
        "options": {"queue": "stock"},
    },
    "fetch-limit-up-pool": {
        "task": "app.tasks.stock_tasks.fetch_limit_up_pool",
        "schedule": 10.0,  # every 10 seconds during trading
        "options": {"queue": "stock"},
    },
    "fetch-hot-sectors": {
        "task": "app.tasks.stock_tasks.fetch_hot_sectors",
        "schedule": 30.0,  # every 30 seconds
        "options": {"queue": "stock"},
    },

    # ===== 加密货币 =====
    "fetch-crypto-tickers": {
        "task": "app.tasks.crypto_tasks.fetch_crypto_tickers",
        "schedule": 60.0,  # every minute
        "options": {"queue": "crypto"},
    },

    # ===== AI 资讯 =====
    "fetch-ai-news": {
        "task": "app.tasks.news_tasks.fetch_ai_news",
        "schedule": 3600.0,  # every hour
        "options": {"queue": "news"},
    },
}
