"""
生成金融日报 HTML，包含实时数据，推送到 GitHub Pages
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "finboard"))
from data_fetcher import get_stock_history
from datetime import datetime

today = datetime.now()
date_str = today.strftime("%Y-%m-%d")
filename = f"D:/Hanako/日报/finboard_{today.strftime('%Y%m%d')}.html"

# 关注的标的
WATCHLIST = {
    "600519": "贵州茅台",
    "000858": "五粮液",
    "300750": "宁德时代",
    "601318": "中国平安",
    "000001": "平安银行",
    "510300": "沪深300ETF",
}

rows_html = ""
for code, name in WATCHLIST.items():
    try:
        df = get_stock_history(code, "20260501")
        if len(df) >= 5:
            recent = df.tail(5)
            latest = recent.iloc[-1]
            prev = recent.iloc[-2]
            chg = (latest["收盘"] - prev["收盘"]) / prev["收盘"] * 100
            chg_class = "up" if chg >= 0 else "down"
            rows_html += f"""<tr>
                <td>{code}</td><td>{name}</td>
                <td class="price">{latest['收盘']:.2f}</td>
                <td class="{chg_class}">{chg:+.2f}%</td>
                <td>{latest['换手率']:.4f}%</td>
            </tr>"""
    except Exception as e:
        rows_html += f"""<tr><td>{code}</td><td>{name}</td><td colspan="3" class="err">数据获取失败</td></tr>"""

html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>金融看板 · {date_str}</title>
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{ font-family: 'Segoe UI', 'PingFang SC', 'Microsoft YaHei', sans-serif; background: #f5f0eb; color: #2c2c2c; padding: 40px 20px; }}
.container {{ max-width: 800px; margin: 0 auto; }}
.header {{ text-align: center; padding: 40px 0; }}
.header h1 {{ font-size: 2em; font-weight: 300; letter-spacing: 4px; color: #1a1a1a; }}
.header .date {{ color: #999; font-size: 0.9em; margin-top: 8px; }}
.header .source {{ color: #bbb; font-size: 0.75em; margin-top: 4px; }}
table {{ width: 100%; border-collapse: collapse; background: #fff; border-radius: 12px; overflow: hidden; box-shadow: 0 2px 20px rgba(0,0,0,0.06); }}
th {{ background: #1a1a1a; color: #fff; font-weight: 400; padding: 14px 16px; text-align: left; font-size: 0.85em; letter-spacing: 1px; }}
td {{ padding: 14px 16px; border-bottom: 1px solid #f0ebe3; font-size: 0.95em; }}
tr:last-child td {{ border-bottom: none; }}
.price {{ font-weight: 600; font-variant-numeric: tabular-nums; }}
.up {{ color: #c0392b; font-weight: 600; }}
.down {{ color: #27ae60; font-weight: 600; }}
.err {{ color: #ccc; font-style: italic; }}
.footer {{ text-align: center; margin-top: 40px; color: #bbb; font-size: 0.8em; }}
.footer a {{ color: #999; text-decoration: none; }}
</style>
</head>
<body>
<div class="container">
<div class="header">
    <h1>📊 金融看板</h1>
    <div class="date">{date_str} · 近5日趋势</div>
    <div class="source">数据来源：新浪财经 · 由 Hanako 自动生成</div>
</div>
<table>
    <thead><tr><th>代码</th><th>名称</th><th>最新价</th><th>日涨跌</th><th>换手率</th></tr></thead>
    <tbody>{rows_html}</tbody>
</table>
<div class="footer">
    <p>由 <a href="https://github.com/coffeeyyds/hanako-workspace">Hanako</a> 自动生成 · 数据仅供参考</p>
</div>
</div>
</body>
</html>"""

os.makedirs(os.path.dirname(filename), exist_ok=True)
with open(filename, "w", encoding="utf-8") as f:
    f.write(html)

print(f"✅ 日报已生成: {filename}")
print(f"   文件大小: {len(html)} 字节")
print(f"   在线地址: https://coffeeyyds.github.io/hanako-workspace/日报/finboard_{today.strftime('%Y%m%d')}.html")
