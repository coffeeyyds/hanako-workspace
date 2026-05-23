"""
AKShare 数据获取辅助模块
解决代理冲突问题，提供常用数据获取函数
"""
import os

# 临时清除代理，避免 AKShare 走系统代理
_DEFAULT_ENV = {
    "HTTP_PROXY": "",
    "HTTPS_PROXY": "",
    "http_proxy": "",
    "https_proxy": "",
    "NO_PROXY": "*",
    "no_proxy": "*",
}


def _clean_proxy():
    """清除当前进程的代理环境变量"""
    for k, v in _DEFAULT_ENV.items():
        os.environ[k] = v


_clean_proxy()

import akshare as ak


def get_stock_spot():
    """获取 A 股实时行情"""
    df = ak.stock_zh_a_spot_em()
    return df


def get_stock_history(symbol: str, start_date: str = "20250101", end_date: str = None):
    """获取个股历史日线数据（前复权）"""
    if end_date is None:
        from datetime import datetime
        end_date = datetime.now().strftime("%Y%m%d")
    df = ak.stock_zh_a_hist(
        symbol=symbol,
        period="daily",
        start_date=start_date,
        end_date=end_date,
        adjust="qfq",
    )
    return df


def get_macro_cpi():
    """获取中国 CPI 数据"""
    df = ak.macro_china_cpi_yearly()
    return df


def get_macro_pmi():
    """获取中国 PMI 数据"""
    df = ak.macro_china_pmi()
    return df


def get_money_supply():
    """获取货币供应量（M0/M1/M2）"""
    df = ak.macro_china_money_supply()
    return df


def get_sector_flow():
    """获取行业资金流向"""
    df = ak.stock_sector_fund_flow_rank(indicator="今日")
    return df


def get_shibor():
    """获取 Shibor 利率"""
    df = ak.rate_interbank(market="上海银行间同业拆放利率")
    return df


# 测试
if __name__ == "__main__":
    print("✅ AKShare 数据模块就绪")
    print("可用函数: get_stock_spot, get_stock_history, get_macro_cpi, get_macro_pmi, get_money_supply, get_sector_flow, get_shibor")
