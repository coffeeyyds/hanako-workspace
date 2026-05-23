"""
A股数据采集器 —— 基于 AKShare
"""
import asyncio
import logging
from datetime import datetime, date
from typing import Optional

import akshare as ak
import pandas as pd

logger = logging.getLogger(__name__)


class AStockCollector:
    """A股行情采集器"""

    # 核心指数列表
    MAJOR_INDEXES = {
        "sh000001": "上证指数",
        "sz399001": "深证成指",
        "sz399006": "创业板指",
        "sh000688": "科创50",
        "sh000300": "沪深300",
        "sh000016": "上证50",
        "sz399905": "中证500",
        "sh000852": "中证1000",
    }

    @staticmethod
    async def fetch_spot_all() -> Optional[pd.DataFrame]:
        """获取全市场A股实时行情（东方财富数据源，约3秒延迟）"""
        try:
            df = await asyncio.to_thread(ak.stock_zh_a_spot_em)
            if df is None or df.empty:
                return None
            # 统一列名
            df.columns = [
                "symbol", "name", "price", "change_pct", "change_amount",
                "volume", "turnover", "amplitude", "high", "low", "open",
                "pre_close", "volume_ratio", "turnover_rate", "pe", "pb",
                "total_market_cap", "float_market_cap", "total_shares",
                "float_shares", "_extra", "_extra2", "_extra3",
            ]
            return df
        except Exception as e:
            logger.error(f"fetch_spot_all failed: {e}")
            return None

    @staticmethod
    async def fetch_index_spot() -> Optional[list[dict]]:
        """获取核心指数实时行情"""
        results = []
        try:
            df = await asyncio.to_thread(ak.stock_zh_index_spot_em)
            if df is None or df.empty:
                return None

            # 只保留关注的核心指数
            for _, row in df.iterrows():
                code = str(row.get("代码", ""))
                if code in AStockCollector.MAJOR_INDEXES:
                    results.append({
                        "symbol": code,
                        "name": AStockCollector.MAJOR_INDEXES[code],
                        "price": float(row.get("最新价", 0)),
                        "change_pct": float(row.get("涨跌幅", 0)),
                        "change_amount": float(row.get("涨跌额", 0)),
                        "volume": int(row.get("成交量", 0) or 0),
                        "turnover": float(row.get("成交额", 0) or 0),
                    })
            return results
        except Exception as e:
            logger.error(f"fetch_index_spot failed: {e}")
            return None

    @staticmethod
    async def fetch_limit_up_pool() -> Optional[pd.DataFrame]:
        """获取当日涨停板池"""
        try:
            today = date.today().strftime("%Y%m%d")
            df = await asyncio.to_thread(ak.stock_zt_pool_em, date=today)
            return df
        except Exception as e:
            logger.error(f"fetch_limit_up_pool failed: {e}")
            return None

    @staticmethod
    async def fetch_hot_sectors() -> Optional[list[dict]]:
        """获取热门概念板块"""
        try:
            df = await asyncio.to_thread(ak.stock_board_concept_name_em)
            if df is None or df.empty:
                return None

            today = date.today().strftime("%Y%m%d")
            results = []
            for _, row in df.iterrows():
                results.append({
                    "trade_date": today,
                    "sector_name": str(row.get("板块名称", "")),
                    "sector_code": str(row.get("板块代码", "")),
                    "change_pct": float(row.get("涨跌幅", 0) or 0),
                    "leading_stock": str(row.get("领涨股票", "")),
                    "leading_stock_change": float(row.get("领涨股票涨跌幅", 0) or 0),
                    "stock_count": int(row.get("上涨家数", 0) or 0),
                })
            return results
        except Exception as e:
            logger.error(f"fetch_hot_sectors failed: {e}")
            return None

    @staticmethod
    async def fetch_daily_kline(symbol: str, start_date: str = "20240101") -> Optional[pd.DataFrame]:
        """获取个股历史日K线"""
        try:
            end_date = date.today().strftime("%Y%m%d")
            df = await asyncio.to_thread(
                ak.stock_zh_a_hist,
                symbol=symbol,
                period="daily",
                start_date=start_date,
                end_date=end_date,
                adjust="qfq",  # 前复权
            )
            return df
        except Exception as e:
            logger.error(f"fetch_daily_kline({symbol}) failed: {e}")
            return None
