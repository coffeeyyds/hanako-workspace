import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import init_db
from app.routers import stocks, crypto, macro, news, overview
from app.config import get_settings

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s: %(message)s")
logger = logging.getLogger("finboard")

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await init_db()
    logger.info("✅ 数据库初始化完成")

    from app.scheduler import start_scheduler
    start_scheduler()
    logger.info("📊 后台采集已启动，数据将在几秒内就绪")

    yield
    # Shutdown
    from app.scheduler import stop_scheduler
    stop_scheduler()
    logger.info("👋 FinBoard 已停止")


app = FastAPI(
    title="FinBoard API",
    description="金融全景数据看板后端",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(stocks.router, prefix="/api/stocks", tags=["A股"])
app.include_router(crypto.router, prefix="/api/crypto", tags=["加密货币"])
app.include_router(macro.router, prefix="/api/macro", tags=["宏观"])
app.include_router(overview.router, prefix="/api", tags=["全景快照"])
app.include_router(news.router, prefix="/api/news", tags=["资讯"])


@app.get("/api/health")
async def health():
    from app.tasks.overview_tasks import get_overview_cache
    cache_ok = get_overview_cache() is not None
    return {
        "status": "ok",
        "service": "FinBoard API",
        "cache_ready": cache_ok,
    }
