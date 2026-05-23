"""A股行情 API"""
from fastapi import APIRouter, Query, HTTPException
from sqlalchemy import text, select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends

from app.database import get_db
from app.models import StockRealtime, IndexRealtime, LimitUpPool, HotSector

router = APIRouter()


@router.get("/spot")
async def get_stock_spot(
    limit: int = Query(50, ge=1, le=500),
    sort_by: str = Query("change_pct", regex="^(price|change_pct|volume|turnover|total_market_cap)$"),
    order: str = Query("desc", regex="^(asc|desc)$"),
    db: AsyncSession = Depends(get_db),
):
    """获取 A 股实时行情列表"""
    col = getattr(StockRealtime, sort_by)
    order_col = desc(col) if order == "desc" else col
    result = await db.execute(
        select(StockRealtime).order_by(order_col).limit(limit)
    )
    rows = result.scalars().all()
    return [
        {
            "symbol": r.symbol,
            "name": r.name,
            "price": r.price,
            "change_pct": r.change_pct,
            "change_amount": r.change_amount,
            "volume": r.volume,
            "turnover": r.turnover,
            "high": r.high,
            "low": r.low,
            "open": r.open,
            "pre_close": r.pre_close,
            "amplitude": r.amplitude,
            "volume_ratio": r.volume_ratio,
            "turnover_rate": r.turnover_rate,
            "pe": r.pe,
            "pb": r.pb,
            "total_market_cap": r.total_market_cap,
        }
        for r in rows
    ]


@router.get("/spot/{symbol}")
async def get_stock_detail(symbol: str, db: AsyncSession = Depends(get_db)):
    """获取单只股票实时行情"""
    result = await db.execute(
        select(StockRealtime).where(StockRealtime.symbol == symbol)
    )
    stock = result.scalar_one_or_none()
    if not stock:
        raise HTTPException(status_code=404, detail="Stock not found")
    return {
        "symbol": stock.symbol,
        "name": stock.name,
        "price": stock.price,
        "change_pct": stock.change_pct,
        "change_amount": stock.change_amount,
        "volume": stock.volume,
        "turnover": stock.turnover,
        "high": stock.high,
        "low": stock.low,
        "open": stock.open,
        "pre_close": stock.pre_close,
        "amplitude": stock.amplitude,
        "volume_ratio": stock.volume_ratio,
        "turnover_rate": stock.turnover_rate,
        "pe": stock.pe,
        "pb": stock.pb,
        "total_market_cap": stock.total_market_cap,
    }


@router.get("/indexes")
async def get_indexes(db: AsyncSession = Depends(get_db)):
    """获取核心指数实时行情"""
    result = await db.execute(select(IndexRealtime))
    indexes = result.scalars().all()
    return [
        {
            "symbol": i.symbol,
            "name": i.name,
            "price": i.price,
            "change_pct": i.change_pct,
            "change_amount": i.change_amount,
        }
        for i in indexes
    ]


@router.get("/limit-up")
async def get_limit_up_pool(
    date: str = Query(None, description="日期 YYYYMMDD，默认今天"),
    db: AsyncSession = Depends(get_db),
):
    """获取涨停板池"""
    from datetime import date as dt_date
    if date is None:
        date = dt_date.today().strftime("%Y%m%d")

    result = await db.execute(
        select(LimitUpPool)
        .where(LimitUpPool.trade_date == date)
        .order_by(desc(LimitUpPool.consecutive_days))
    )
    rows = result.scalars().all()
    return [
        {
            "symbol": r.symbol,
            "name": r.name,
            "change_pct": r.change_pct,
            "consecutive_days": r.consecutive_days,
            "first_limit_time": r.first_limit_time,
            "last_limit_time": r.last_limit_time,
            "limit_order_amount": r.limit_order_amount,
            "break_count": r.break_count,
            "turnover_rate": r.turnover_rate,
        }
        for r in rows
    ]


@router.get("/sectors")
async def get_hot_sectors(
    date: str = Query(None),
    limit: int = Query(30, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """获取热门板块"""
    from datetime import date as dt_date
    if date is None:
        date = dt_date.today().strftime("%Y%m%d")

    result = await db.execute(
        select(HotSector)
        .where(HotSector.trade_date == date)
        .order_by(desc(HotSector.change_pct))
        .limit(limit)
    )
    rows = result.scalars().all()
    return [
        {
            "sector_name": r.sector_name,
            "sector_code": r.sector_code,
            "change_pct": r.change_pct,
            "leading_stock": r.leading_stock,
            "leading_stock_change": r.leading_stock_change,
            "stock_count": r.stock_count,
        }
        for r in rows
    ]
