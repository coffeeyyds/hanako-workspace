"""全景快照任务（SQLite 版，APScheduler 调度）"""
import asyncio
import logging
import json

from app.collectors.overview import OverviewCollector

logger = logging.getLogger(__name__)
collector = OverviewCollector()

# In-memory cache (replaces Redis)
_overview_cache: dict | None = None


def get_overview_cache() -> dict | None:
    return _overview_cache


def refresh_overview():
    """每30秒：刷新全局仪表盘快照"""
    global _overview_cache
    try:
        import threading
        # 在独立线程中运行 asyncio，避免与 FastAPI 事件循环冲突
        def _run():
            loop = asyncio.new_event_loop()
            try:
                data = loop.run_until_complete(collector.fetch_all())
                global _overview_cache
                _overview_cache = data
            finally:
                loop.close()

        t = threading.Thread(target=_run, daemon=True)
        t.start()
        t.join(timeout=60)

        if _overview_cache:
            a = _overview_cache.get("a_share_sentiment", {})
            bond = _overview_cache.get("bond_snapshot", {})
            crypto = _overview_cache.get("crypto_snapshot", {})
            logger.info(
                f"全景刷新: A股涨跌{a.get('up_count',0)}/{a.get('down_count',0)}, "
                f"LPR1Y {bond.get('lpr_1y',0)}%, "
                f"BTC ${crypto.get('btc_price',0):.0f}"
            )
        return {"status": "ok"}
    except Exception as e:
        logger.error(f"全景刷新失败: {e}")
        return {"status": "error", "error": str(e)}
