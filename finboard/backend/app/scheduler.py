"""APScheduler 调度器 — 替代 Celery+Redis"""
import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

from app.tasks.stock_tasks import fetch_a_stock_spot, fetch_index_spot, fetch_limit_up_pool, fetch_hot_sectors
from app.tasks.overview_tasks import refresh_overview

logger = logging.getLogger(__name__)

scheduler = BackgroundScheduler(timezone="Asia/Shanghai")


def start_scheduler():
    """启动所有定时任务"""

    # A股实时行情 — 每5秒（AKShare 单次采集约2-3秒，留余量）
    scheduler.add_job(
        fetch_a_stock_spot,
        IntervalTrigger(seconds=5),
        id="a_stock_spot",
        name="A股实时行情",
        max_instances=2,
        replace_existing=True,
    )

    # 核心指数 — 每5秒
    scheduler.add_job(
        fetch_index_spot,
        IntervalTrigger(seconds=5),
        id="index_spot",
        name="核心指数",
        replace_existing=True,
    )

    # 涨停板池 — 每10秒
    scheduler.add_job(
        fetch_limit_up_pool,
        IntervalTrigger(seconds=10),
        id="limit_up",
        name="涨停板",
        replace_existing=True,
    )

    # 热门板块 — 每30秒
    scheduler.add_job(
        fetch_hot_sectors,
        IntervalTrigger(seconds=30),
        id="hot_sectors",
        name="热门板块",
        replace_existing=True,
    )

    # 全景快照 — 每30秒
    scheduler.add_job(
        refresh_overview,
        IntervalTrigger(seconds=30),
        id="overview",
        name="全景快照",
        replace_existing=True,
    )

    scheduler.start()
    logger.info("📊 APScheduler 已启动，6个定时任务就绪")
    for job in scheduler.get_jobs():
        logger.info(f"  · {job.name}: 每 {job.trigger.interval_length} 秒")


def stop_scheduler():
    scheduler.shutdown(wait=False)
