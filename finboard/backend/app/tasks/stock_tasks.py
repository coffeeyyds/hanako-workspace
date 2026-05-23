"""A股采集任务（SQLite 同步版，由 APScheduler 调度）"""
import asyncio
import logging
from datetime import datetime, date
from sqlalchemy import create_engine, select, delete
from sqlalchemy.orm import sessionmaker
from app.config import get_settings
from app.models import StockRealtime, IndexRealtime, LimitUpPool, HotSector
from app.collectors.a_stock import AStockCollector

logger = logging.getLogger(__name__)
settings = get_settings()
collector = AStockCollector()

# SQLite sync engine
sync_engine = create_engine(
    settings.database_url.replace("+aiosqlite", "+pysqlite").replace("aiosqlite:///", "sqlite:///"),
    echo=False,
)
SyncSession = sessionmaker(bind=sync_engine)


def fetch_a_stock_spot():
    """每3秒：全市场A股实时行情"""
    try:
        df = asyncio.run(collector.fetch_spot_all())
        if df is None or df.empty:
            logger.debug("A股: 无数据（非交易时段）")
            return {"status": "no_data"}

        with SyncSession() as session:
            rows = 0
            for _, row in df.iterrows():
                try:
                    symbol = str(row.get("symbol", ""))[:20]
                    existing = session.get(StockRealtime, symbol)
                    vals = {
                        "symbol": symbol,
                        "name": str(row.get("name", ""))[:50],
                        "price": float(row.get("price", 0) or 0),
                        "change_pct": float(row.get("change_pct", 0) or 0),
                        "change_amount": float(row.get("change_amount", 0) or 0),
                        "volume": int(row.get("volume", 0) or 0),
                        "turnover": float(row.get("turnover", 0) or 0),
                        "high": float(row.get("high", 0) or 0),
                        "low": float(row.get("low", 0) or 0),
                        "open": float(row.get("open", 0) or 0),
                        "pre_close": float(row.get("pre_close", 0) or 0),
                        "amplitude": float(row.get("amplitude", 0) or 0),
                        "volume_ratio": float(row.get("volume_ratio", 0) or 0),
                        "turnover_rate": float(row.get("turnover_rate", 0) or 0),
                        "pe": float(row.get("pe", 0) or 0),
                        "pb": float(row.get("pb", 0) or 0),
                        "total_market_cap": float(row.get("total_market_cap", 0) or 0),
                        "updated_at": datetime.utcnow(),
                    }
                    if existing:
                        for k, v in vals.items():
                            if k != "symbol":
                                setattr(existing, k, v)
                    else:
                        session.add(StockRealtime(**vals))
                    rows += 1
                except Exception:
                    continue
            session.commit()
            logger.info(f"A股行情: {rows} 条写入")
            return {"status": "ok", "rows": rows}
    except Exception as e:
        logger.error(f"A股行情失败: {e}")
        return {"status": "error", "error": str(e)}


def fetch_index_spot():
    """更新核心指数"""
    try:
        indexes = asyncio.run(collector.fetch_index_spot())
        if not indexes:
            return {"status": "no_data"}

        with SyncSession() as session:
            for idx in indexes:
                symbol = idx["symbol"]
                existing = session.get(IndexRealtime, symbol)
                vals = {
                    "symbol": symbol,
                    "name": idx["name"],
                    "price": idx["price"],
                    "change_pct": idx["change_pct"],
                    "change_amount": idx["change_amount"],
                    "volume": idx.get("volume", 0),
                    "turnover": idx.get("turnover", 0),
                    "updated_at": datetime.utcnow(),
                }
                if existing:
                    for k, v in vals.items():
                        if k != "symbol":
                            setattr(existing, k, v)
                else:
                    session.add(IndexRealtime(**vals))
            session.commit()
        return {"status": "ok", "count": len(indexes)}
    except Exception as e:
        logger.error(f"指数采集失败: {e}")
        return {"status": "error"}


def fetch_limit_up_pool():
    """涨停板池"""
    try:
        df = asyncio.run(collector.fetch_limit_up_pool())
        if df is None or df.empty:
            return {"status": "no_data"}

        today_str = date.today().strftime("%Y%m%d")

        with SyncSession() as session:
            session.execute(delete(LimitUpPool).where(LimitUpPool.trade_date == today_str))
            rows = 0
            for _, row in df.iterrows():
                session.add(LimitUpPool(
                    trade_date=today_str,
                    symbol=str(row.get("代码", ""))[:20],
                    name=str(row.get("名称", ""))[:50],
                    change_pct=float(row.get("涨跌幅", 0) or 0),
                    consecutive_days=int(row.get("连板数", 0) or 0),
                    first_limit_time=str(row.get("首次封板时间", "")),
                    last_limit_time=str(row.get("最后封板时间", "")),
                    limit_order_amount=float(row.get("封单额", 0) or 0),
                    break_count=int(row.get("炸板次数", 0) or 0),
                    turnover_rate=float(row.get("换手率", 0) or 0),
                ))
                rows += 1
            session.commit()
        logger.info(f"涨停板: {rows} 只")
        return {"status": "ok", "rows": rows}
    except Exception as e:
        logger.error(f"涨停板采集失败: {e}")
        return {"status": "error"}


def fetch_hot_sectors():
    """热门板块"""
    try:
        sectors = asyncio.run(collector.fetch_hot_sectors())
        if not sectors:
            return {"status": "no_data"}

        today_str = date.today().strftime("%Y%m%d")

        with SyncSession() as session:
            session.execute(delete(HotSector).where(HotSector.trade_date == today_str))
            for s in sectors:
                session.add(HotSector(
                    trade_date=today_str,
                    sector_name=s["sector_name"],
                    sector_code=s["sector_code"],
                    change_pct=s["change_pct"],
                    leading_stock=s["leading_stock"],
                    leading_stock_change=s["leading_stock_change"],
                    stock_count=s["stock_count"],
                ))
            session.commit()
        return {"status": "ok", "count": len(sectors)}
    except Exception as e:
        logger.error(f"板块采集失败: {e}")
        return {"status": "error"}
