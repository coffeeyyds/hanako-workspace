"""
生成金融数据日报 HTML，推送到 GitHub Pages
"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "finboard"))

# 彻底清除代理
for k in list(os.environ.keys()):
    if k.lower().endswith("_proxy") or k.lower().startswith("proxy_"):
        del os.environ[k]
os.environ["NO_PROXY"] = "*"

# 绕过系统代理
import urllib.request
urllib.request.getproxies = lambda: {}

import requests
requests.Session().trust_env = False

import akshare as ak

# 直接调用（绕过 data_fetcher 模块的代理逻辑）
try:
    df = ak.stock_zh_a_hist(symbol="600519", period="daily", start_date="20260515", end_date="20260523", adjust="qfq")
    print("✅ AKShare 数据获取成功")
    print(df[["日期", "收盘", "涨跌幅"]].tail(5).to_string())
except Exception as e:
    print(f"❌ AKShare 失败: {e}")

# 备选：直接用 requests
try:
    import json
    url = "https://push2his.eastmoney.com/api/qt/stock/kline/get"
    params = {
        "secid": "1.600519",
        "fields1": "f1,f2,f3,f4,f5,f6",
        "fields2": "f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61",
        "klt": "101",
        "fqt": "1",
        "end": "20260523",
        "lmt": "5",
    }
    r = requests.get(url, params=params, timeout=10)
    print(f"\n✅ 直连 API: status={r.status_code}, len={len(r.text)}")
except Exception as e:
    print(f"\n❌ 直连 API 失败: {e}")
