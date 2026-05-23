"""SQLite-compatible models"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, Text
from app.database import Base


class StockRealtime(Base):
    __tablename__ = "stock_realtime"

    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(20), nullable=False, unique=True)
    name = Column(String(50))
    price = Column(Float)
    change_pct = Column(Float)
    change_amount = Column(Float)
    volume = Column(Integer)
    turnover = Column(Float)
    high = Column(Float)
    low = Column(Float)
    open = Column(Float)
    pre_close = Column(Float)
    amplitude = Column(Float)
    volume_ratio = Column(Float)
    turnover_rate = Column(Float)
    pe = Column(Float)
    pb = Column(Float)
    total_market_cap = Column(Float)
    updated_at = Column(DateTime, default=datetime.utcnow)


class IndexRealtime(Base):
    __tablename__ = "index_realtime"

    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(20), nullable=False, unique=True)
    name = Column(String(50))
    price = Column(Float)
    change_pct = Column(Float)
    change_amount = Column(Float)
    volume = Column(Integer)
    turnover = Column(Float)
    updated_at = Column(DateTime, default=datetime.utcnow)


class LimitUpPool(Base):
    __tablename__ = "limit_up_pool"

    id = Column(Integer, primary_key=True, autoincrement=True)
    trade_date = Column(String(20), nullable=False, index=True)
    symbol = Column(String(20), index=True)
    name = Column(String(50))
    change_pct = Column(Float)
    limit_price = Column(Float)
    first_limit_time = Column(String(20))
    last_limit_time = Column(String(20))
    consecutive_days = Column(Integer)
    limit_order_amount = Column(Float)
    break_count = Column(Integer)
    turnover_rate = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)


class HotSector(Base):
    __tablename__ = "hot_sectors"

    id = Column(Integer, primary_key=True, autoincrement=True)
    trade_date = Column(String(20), index=True)
    sector_name = Column(String(100), index=True)
    sector_code = Column(String(20))
    change_pct = Column(Float)
    leading_stock = Column(String(50))
    leading_stock_change = Column(Float)
    stock_count = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)


class CryptoRealtime(Base):
    __tablename__ = "crypto_realtime"

    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(20), nullable=False, unique=True)
    name = Column(String(50))
    price_usd = Column(Float)
    price_cny = Column(Float, nullable=True)
    change_24h_pct = Column(Float)
    market_cap = Column(Float)
    volume_24h = Column(Float)
    high_24h = Column(Float)
    low_24h = Column(Float)
    updated_at = Column(DateTime, default=datetime.utcnow)


class MacroIndicator(Base):
    __tablename__ = "macro_indicators"

    id = Column(Integer, primary_key=True, autoincrement=True)
    indicator_name = Column(String(100), nullable=False, index=True)
    indicator_value = Column(Float)
    indicator_date = Column(String(20), index=True)
    category = Column(String(50))
    created_at = Column(DateTime, default=datetime.utcnow)


class NewsArticle(Base):
    __tablename__ = "news_articles"

    id = Column(Integer, primary_key=True, autoincrement=True)
    source = Column(String(100), index=True)
    source_type = Column(String(20))
    title = Column(String(500))
    url = Column(String(500))
    summary = Column(Text, nullable=True)
    ai_summary = Column(Text, nullable=True)
    published_at = Column(DateTime, index=True)
    tags = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
