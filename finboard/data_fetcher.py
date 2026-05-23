"""
AKShare 数据获取辅助模块
新浪数据源优先（国内直连），East Money 作为备选。
"""
import os
import socket

# 检测代理可用性
def _detect_network():
    """智能检测网络环境，返回最佳连接策略"""
    s = socket.socket()
    s.settimeout(1)
    proxy_ok = s.connect_ex(("127.0.0.1", 7890)) == 0
    s.close()
    return proxy_ok

_proxy_ok = _detect_network()

if _proxy_ok:
    os.environ["HTTPS_PROXY"] = "http://127.0.0.1:7890"
    os.environ["HTTP_PROXY"] = "http://127.0.0.1:7890"
else:
    for k in ("HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy"):
        os.environ[k] = ""

import akshare as ak
from datetime import datetime


def get_stock_history(symbol: str, start_date: str = "20250101", end_date: str = None):
    """获取个股历史日线（前复权）| 新浪数据源，国内直连"""
    if end_date is None:
        end_date = datetime.now().strftime("%Y%m%d")

    # 新浪格式：sh600519 或 sz000001
    prefix = "sh" if symbol.startswith(("6", "5", "9")) else "sz"
    sina_symbol = f"{prefix}{symbol}"

    df = ak.stock_zh_a_daily(
        symbol=sina_symbol,
        start_date=start_date,
        end_date=end_date,
        adjust="qfq",
    )
    df = df.rename(columns={
        "date": "日期", "open": "开盘", "close": "收盘",
        "high": "最高", "low": "最低", "volume": "成交量",
        "amount": "成交额", "turnover": "换手率"
    })
    return df


def get_stock_spot():
    """获取 A 股实时行情 | 东方财富源，需代理"""
    return ak.stock_zh_a_spot_em()


def get_macro_cpi():
    """中国 CPI 月度数据"""
    return ak.macro_china_cpi_monthly()


def get_macro_pmi():
    """中国 PMI"""
    return ak.macro_china_pmi()


def get_money_supply():
    """货币供应量 M0/M1/M2"""
    return ak.macro_china_money_supply()


def get_shibor():
    """Shibor 利率"""
    return ak.rate_interbank(market="上海银行间同业拆放利率")


if __name__ == "__main__":
    print("✅ AKShare 数据模块就绪（新浪源优先）")
    print("代理状态:", "可用" if _proxy_ok else "不可用（直连）")
