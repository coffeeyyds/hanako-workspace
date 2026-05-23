"""
全景快照采集器 v2 —— 优先使用 AKShare 宏观接口（24/7 可用）
盘后实时行情失败时用缓存/空值兜底
"""
import asyncio
import logging
from datetime import date
import json
import os

import akshare as ak
import pandas as pd

logger = logging.getLogger(__name__)

# 缓存文件路径
CACHE_FILE = os.path.join(os.path.dirname(__file__), "..", "overview_cache.json")


class OverviewCollector:
    """全局快照采集器（纯国内数据源版）"""

    @staticmethod
    def _save_cache(data: dict):
        try:
            with open(CACHE_FILE, "w") as f:
                json.dump(data, f, ensure_ascii=False, default=str)
        except Exception:
            pass

    @staticmethod
    def _load_cache() -> dict | None:
        try:
            with open(CACHE_FILE, "r") as f:
                return json.load(f)
        except Exception:
            return None

    # ============================================================
    # A 股情绪
    # ============================================================
    @staticmethod
    async def fetch_a_share_sentiment() -> dict:
        try:
            df = await asyncio.to_thread(ak.stock_zh_a_spot_em)
            if df is None or df.empty:
                raise ValueError("empty data")
            total = len(df)
            up_count = len(df[df["涨跌幅"] > 0]) if "涨跌幅" in df.columns else 0
            down_count = len(df[df["涨跌幅"] < 0]) if "涨跌幅" in df.columns else 0
            limit_up = len(df[df["涨跌幅"] >= 9.9]) if "涨跌幅" in df.columns else 0
            limit_down = len(df[df["涨跌幅"] <= -9.9]) if "涨跌幅" in df.columns else 0
            total_turnover = df["成交额"].sum() / 1e8 if "成交额" in df.columns else 0

            return {
                "total_stocks": total, "up_count": up_count, "down_count": down_count,
                "flat_count": total - up_count - down_count,
                "up_ratio": round(up_count / total * 100, 1) if total else 0,
                "limit_up_count": limit_up, "limit_down_count": limit_down,
                "total_turnover_yi": round(total_turnover, 0),
                "status": "live"
            }
        except Exception as e:
            logger.warning(f"A股情绪: 盘后无实时数据 ({e})")
            return {"status": "closed", "total_stocks": 0, "up_count": 0, "down_count": 0}

    # ============================================================
    # 债市快照
    # ============================================================
    @staticmethod
    async def fetch_bond_snapshot() -> dict:
        result = {}
        # LPR
        try:
            df = await asyncio.to_thread(ak.macro_china_lpr)
            if df is not None and not df.empty:
                last = df.iloc[-1]
                result["lpr_1y"] = float(last.get("LPR1Y", 0) or 0)
                result["lpr_5y"] = float(last.get("LPR5Y", 0) or 0)
                result["lpr_date"] = str(last.get("TRADE_DATE", ""))
        except Exception as e:
            logger.warning(f"LPR获取失败: {e}")

        # Shibor 隔夜
        try:
            df = await asyncio.to_thread(
                ak.rate_interbank, market="上海银行间同业拆放利率", symbol="Shibor", indicator="隔夜"
            )
            if df is not None and not df.empty:
                result["shibor_on"] = round(float(df.iloc[-1].get("利率", 0) or 0), 4)
        except Exception:
            pass  # API may have changed, skip gracefully

        # 国债收益率 10Y
        try:
            today_str = date.today().strftime("%Y%m%d")
            df = await asyncio.to_thread(
                ak.bond_china_yield, start_date=today_str, end_date=today_str
            )
            if df is not None and not df.empty:
                mask = df["曲线名称"].str.contains("国债", na=False)
                if mask.any():
                    result["cn_10y_yield"] = float(df[mask].iloc[-1].get("10Y", 0) or 0)
        except Exception as e:
            logger.warning(f"国债收益率获取失败: {e}")

        return result

    # ============================================================
    # 汇率快照
    # ============================================================
    @staticmethod
    async def fetch_fx_snapshot() -> dict:
        result = {}
        try:
            df = await asyncio.to_thread(ak.currency_boc_safe)
            if df is not None and not df.empty:
                last = df.iloc[-1]
                # BOC data: values are CNY per 100 units of foreign currency
                result["usd_cny"] = round(float(last.get("美元", 0) or 0) / 100, 4)
                result["fx_date"] = str(last.get("日期", ""))
                result["fx_source"] = "BOC中间价"
        except Exception as e:
            logger.warning(f"汇率获取失败: {e}")
        return result

    # ============================================================
    # 全球指数快照（用 AKShare 替代 yfinance）
    # ============================================================
    @staticmethod
    async def fetch_global_indexes() -> list[dict]:
        results = []
        # 国内指数用 AKShare
        try:
            df = await asyncio.to_thread(ak.stock_zh_index_spot_em)
            if df is not None and not df.empty:
                target = {"sh000001": "上证指数", "sz399001": "深证成指", "sz399006": "创业板指",
                          "sh000688": "科创50", "sh000300": "沪深300", "sh000016": "上证50"}
                for _, row in df.iterrows():
                    code = str(row.get("代码", ""))
                    if code in target:
                        results.append({
                            "symbol": code, "name": target[code],
                            "price": float(row.get("最新价", 0) or 0),
                            "change_pct": float(row.get("涨跌幅", 0) or 0),
                        })
        except Exception as e:
            logger.warning(f"国内指数获取失败: {e}")

        # 港股
        try:
            df = await asyncio.to_thread(ak.stock_hk_spot_em)
            if df is not None and not df.empty:
                for _, row in df.iterrows():
                    code = str(row.get("代码", ""))
                    if code == "HSI" or "恒生" in str(row.get("名称", "")):
                        results.append({
                            "symbol": "^HSI", "name": "恒生指数",
                            "price": float(row.get("最新价", 0) or 0),
                            "change_pct": float(row.get("涨跌幅", 0) or 0),
                        })
                        break
        except Exception:
            pass

        # 国际指数（美股收盘后可能不可用）
        try:
            import yfinance as yf
            for sym, name in [("^GSPC", "标普500"), ("^IXIC", "纳斯达克"), ("^N225", "日经225")]:
                try:
                    t = yf.Ticker(sym)
                    info = t.info
                    prev = info.get("previousClose", 0) or info.get("regularMarketPreviousClose", 0)
                    curr = info.get("currentPrice", 0) or info.get("regularMarketPrice", 0)
                    if curr and prev:
                        results.append({
                            "symbol": sym, "name": name,
                            "price": round(curr, 2),
                            "change_pct": round((curr - prev) / prev * 100, 2),
                        })
                except Exception:
                    pass
        except Exception:
            pass

        return results

    # ============================================================
    # 币圈快照
    # ============================================================
    @staticmethod
    async def fetch_crypto_snapshot() -> dict:
        result = {}
        # 恐惧贪婪指数（不需要翻墙的 API）
        try:
            import httpx
            async with httpx.AsyncClient(timeout=8.0) as client:
                resp = await client.get("https://api.alternative.me/fng/?limit=1")
                if resp.status_code == 200:
                    data = resp.json().get("data", [{}])[0]
                    result["fear_greed_value"] = int(data.get("value", 50))
                    result["fear_greed_classification"] = data.get("value_classification", "Neutral")
        except Exception:
            pass

        # CoinGecko（需要翻墙，失败时静默）
        try:
            import httpx
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(
                    "https://api.coingecko.com/api/v3/simple/price",
                    params={"ids": "bitcoin,ethereum", "vs_currencies": "usd",
                            "include_24hr_change": "true"}
                )
                if resp.status_code == 200:
                    data = resp.json()
                    btc = data.get("bitcoin", {})
                    eth = data.get("ethereum", {})
                    result["btc_price"] = btc.get("usd", 0)
                    result["btc_change_24h"] = round(btc.get("usd_24h_change", 0), 2)
                    result["eth_price"] = eth.get("usd", 0)
                    result["eth_change_24h"] = round(eth.get("usd_24h_change", 0), 2)
        except Exception:
            pass

        return result

    # ============================================================
    # 大宗商品（用 AKShare 国内期货替代 yfinance）
    # ============================================================
    @staticmethod
    async def fetch_commodity_snapshot() -> dict:
        result = {}
        try:
            df = await asyncio.to_thread(ak.futures_zh_spot)
            if df is not None and not df.empty:
                # Try different column names across AKShare versions
                sym_col = next((c for c in ["品种代码", "symbol", "合约代码"] if c in df.columns), df.columns[0])
                price_col = next((c for c in ["最新价", "price", "最新价格"] if c in df.columns), df.columns[2] if len(df.columns)>2 else df.columns[0])
                chg_col = next((c for c in ["涨跌幅", "change_pct", "涨跌率"] if c in df.columns), None)

                targets = {"AU": "黄金", "SC": "原油", "CU": "铜", "AG": "白银"}
                for _, row in df.iterrows():
                    sym = str(row.get(sym_col, ""))
                    if sym in targets:
                        result[sym] = {
                            "name": targets[sym],
                            "price": float(row.get(price_col, 0) or 0),
                            "change_pct": float(row.get(chg_col, 0) or 0) if chg_col else 0,
                        }
        except Exception as e:
            logger.warning(f"大宗商品获取失败: {e}")
        return result

    # ============================================================
    # Polymarket
    # ============================================================
    @staticmethod
    async def fetch_polymarket_snapshot() -> list[dict]:
        try:
            import httpx
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.get(
                    "https://gamma-api.polymarket.com/markets",
                    params={"limit": 5, "order": "volume24hr", "ascending": False},
                )
                if resp.status_code != 200:
                    return []
                markets = resp.json()
                results = []
                for m in markets:
                    outcomes = m.get("outcomes", [])
                    prices = m.get("outcomePrices", [])
                    outcome_str = " vs ".join(outcomes[:2])
                    top_prob = round(float(prices[0]) * 100, 1) if prices else 0
                    results.append({
                        "question": (m.get("question") or m.get("title", ""))[:80],
                        "outcomes": outcome_str,
                        "probability": top_prob,
                        "volume_24h": round(float(m.get("volume24hr", 0)), 0),
                    })
                return results
        except Exception:
            return []

    # ============================================================
    # 聚合
    # ============================================================
    @staticmethod
    async def fetch_all() -> dict:
        results = await asyncio.gather(
            OverviewCollector.fetch_a_share_sentiment(),
            OverviewCollector.fetch_bond_snapshot(),
            OverviewCollector.fetch_fx_snapshot(),
            OverviewCollector.fetch_global_indexes(),
            OverviewCollector.fetch_crypto_snapshot(),
            OverviewCollector.fetch_commodity_snapshot(),
            OverviewCollector.fetch_polymarket_snapshot(),
            return_exceptions=True,
        )

        keys = [
            "a_share_sentiment", "bond_snapshot", "fx_snapshot",
            "global_indexes", "crypto_snapshot", "commodity_snapshot",
            "polymarket_snapshot",
        ]

        overview = {"updated_at": date.today().isoformat()}
        for key, r in zip(keys, results):
            if isinstance(r, Exception):
                logger.warning(f"Overview {key} failed: {r}")
                overview[key] = {} if key not in ("global_indexes", "polymarket_snapshot") else []
            else:
                overview[key] = r

        # 检查数据质量
        a = overview.get("a_share_sentiment", {})
        bond = overview.get("bond_snapshot", {})
        crypto = overview.get("crypto_snapshot", {})
        filled = sum([
            1 if a.get("up_count") else 0,
            1 if bond.get("lpr_1y") else 0,
            1 if crypto.get("btc_price") else 0,
            1 if len(overview.get("global_indexes", [])) > 3 else 0,
            1 if len(overview.get("commodity_snapshot", {})) > 0 else 0,
        ])
        overview["data_quality"] = f"{filled}/5 板块有数据"

        # 缓存
        OverviewCollector._save_cache(overview)
        logger.info(f"全景: {overview['data_quality']}")
        return overview
