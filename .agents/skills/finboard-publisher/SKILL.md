---
name: finboard-publisher
description: |
  金融看板日报生成与发布。当用户要求"生成金融日报""推送金融看板""发布行情日报""更新 GitHub 看板"
  "推送到 GitHub""今天的行情推上去""更新日报""发布到线上"时使用。
  自动运行 Python 脚本抓取 A 股实时数据，生成精美 HTML，推送到 GitHub Pages 获取公网可访问链接。
  触发关键词：金融日报、行情日报、推送到 GitHub、发布看板、更新日报、finboard、生成日报。
---

# 金融看板发布器

自动生成 A 股金融看板 HTML 并推送到 GitHub Pages，在你的任何设备上通过链接访问。

## 工作流

### 第一步：生成日报

在工作区根目录运行生成脚本：

```bash
cd D:/Hanako
python generate_daily.py
```

脚本会读取 `finboard/data_fetcher.py` 模块，通过新浪财经 API 抓取关注标的的实时行情，生成带 CSS 样式的 HTML 文件，保存到 `日报/finboard_YYYYMMDD.html`。

### 第二步：推送到 GitHub

```bash
cd D:/Hanako
git add generate_daily.py finboard/ 日报/
git commit -m "update: 金融看板 $(date +%Y-%m-%d)"
git push origin main
```

### 第三步：返回在线链接

推送成功后，GitHub Pages 会在约 30 秒内部署完成。在线地址格式：

```
https://coffeeyyds.github.io/hanako-workspace/日报/finboard_YYYYMMDD.html
```

确认部署状态：

```bash
python -c "import requests, time; time.sleep(5); r = requests.get('https://coffeeyyds.github.io/hanako-workspace/日报/finboard_YYYYMMDD.html'); print(r.status_code)"
```

HTTP 200 即表示上线成功。

## 关注标的

当前 `generate_daily.py` 中包含以下标的：
- 600519 贵州茅台
- 000858 五粮液
- 300750 宁德时代
- 601318 中国平安
- 000001 平安银行

如需修改，编辑 `D:/Hanako/generate_daily.py` 中的 `WATCHLIST` 字典。

## 数据源说明

- 历史日线：新浪财经 API（国内直连，无需代理）
- 新浪数据源使用 `akshare.stock_zh_a_daily()`
- 东方财富数据源（`stock_zh_a_spot_em`）需要系统代理 127.0.0.1:7890

## 网络适配

`finboard/data_fetcher.py` 会自动检测代理端口 7890 是否可用：
- 可用 → 走代理
- 不可用 → 直连（新浪源可直连，East Money 不可）

## 定时运行

如需每天早上自动生成并推送，让 Hanako 配 cron：

```
每天早上 9:00 运行 cd D:/Hanako && python generate_daily.py && git add 日报/ && git commit -m "update: 金融看板" && git push
```
