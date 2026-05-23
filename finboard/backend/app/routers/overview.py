"""全景快照 API"""
import logging
from fastapi import APIRouter, HTTPException
from app.tasks.overview_tasks import get_overview_cache
from app.collectors.overview import OverviewCollector

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/overview")
async def get_overview():
    """全局仪表盘快照，各板块等权"""
    cached = get_overview_cache()
    if cached:
        return cached

    # 首次启动，实时采集
    try:
        data = await OverviewCollector.fetch_all()
        return data
    except Exception as e:
        logger.warning(f"全景快照不可用: {e}")
        raise HTTPException(status_code=503, detail="服务初始化中，请稍候...")
