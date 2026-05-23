# FinBoard — 金融全景看板

> 一行命令启动的金融全景仪表盘。  
> A股·债市·汇率·币圈·大宗·预测市场·AI 动向，等权一览。

## 启动（零依赖，无需 Docker）

```bash
cd D:\Hanako\finboard\backend

# 1. 安装 Python 依赖
pip install -r requirements.txt

# 2. （可选）配置代理 + DeepSeek Key
# 如果系统已设 HTTP_PROXY 环境变量，自动生效
set DEEPSEEK_API_KEY=sk-your-key-here

# 3. 启动后端
python run.py
```

```bash
# 另一个终端：启动前端
cd D:\Hanako\finboard\frontend
npm install
npm run dev
```

浏览器打开 **http://localhost:5173**

## 架构

```
python run.py                     ← 单进程启动
  ├── FastAPI (localhost:8000)     ← API 服务
  ├── APScheduler                  ← 内置定时任务（替代 Celery+Redis）
  │   · A股行情 3s
  │   · 核心指数 5s
  │   · 涨停板 10s
  │   · 热门板块 30s
  │   · 全景快照 30s（含债市/汇率/币圈/大宗/Polymarket）
  └── SQLite (finboard.db)         ← 本地数据库（替代 PostgreSQL）
```

## API

| 端点 | 说明 |
|------|------|
| `GET /api/health` | 健康检查 |
| `GET /api/overview` | 全景快照（所有板块） |
| `GET /api/stocks/spot` | A股实时行情 |
| `GET /api/stocks/indexes` | 核心指数 |
| `GET /api/stocks/limit-up` | 涨停板池 |
| `GET /api/stocks/sectors` | 热门板块 |
