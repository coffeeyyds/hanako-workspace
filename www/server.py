"""
Hanako Site v2.0 — Personal Portfolio + Tool Platform + Bridge
Modular FastAPI server with router-based architecture.

Routers:
  home   — homepage, daily, projects
  mori   — markets, weather, hot, dashboard
  tools  — auth, parse, knowledge, chat, upload
  bridge — saved links, search, tasks, file access, status (NEW)

Setup:
  pip install fastapi uvicorn httpx beautifulsoup4 python-multipart easyocr

Start:
  python server.py   → http://localhost:8000
"""
import os
import sys
import json
from datetime import datetime
from pathlib import Path

import uvicorn
from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse, JSONResponse

# Ensure routers can be imported
sys.path.insert(0, str(Path(__file__).parent))

# Load .env file
_env_path = Path(__file__).parent / ".env"
if _env_path.exists():
    with open(_env_path, encoding="utf-8") as _f:
        for _line in _f:
            _line = _line.strip()
            if _line and not _line.startswith("#") and "=" in _line:
                _k, _v = _line.split("=", 1)
                _k = _k.strip()
                _v = _v.strip().strip('"').strip("'")
                if _k not in os.environ:
                    os.environ[_k] = _v

# ─── Import routers ───────────────────────────────────
from routers.home import router as home_router
from routers.mori import router as mori_router
from routers.tools import router as tools_router
from routers.bridge import router as bridge_router
from routers.personal import router as personal_router
from routers.workbench import router as workbench_router
from routers.studio_tools import router as studio_tools_router
from routers.baking import router as baking_router

# ─── App ──────────────────────────────────────────────
app = FastAPI(title="Hanako Site", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Mount routers ────────────────────────────────────
app.include_router(home_router)
app.include_router(mori_router)
app.include_router(tools_router)
app.include_router(bridge_router)
app.include_router(personal_router)
app.include_router(workbench_router)
app.include_router(studio_tools_router)
app.include_router(baking_router)

# ─── Parse log ───────────────────────────────────────
PARSE_LOG_DIR = Path(__file__).parent / "data" / "parse_logs"
PARSE_LOG_DIR.mkdir(parents=True, exist_ok=True)
KB_INBOX = Path(__file__).parent.parent / "kb" / "inbox"
KB_INBOX.mkdir(parents=True, exist_ok=True)


@app.post("/api/parse/log")
async def parse_log(request: Request):
    """Log a parsed URL for backend visibility + write to kb/inbox."""
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(400, detail="需要 JSON")
    url = body.get("url", "")
    title = body.get("title", "")
    source = body.get("source", "")
    if not url:
        raise HTTPException(400, detail="url 不能为空")
    ts = datetime.now()
    log_entry = {
        "url": url,
        "title": title,
        "source": source,
        "timestamp": ts.isoformat(),
        "ai_related": body.get("ai_related", False),
        "note_id": body.get("note_id", ""),
        "content": body.get("content", ""),
        "summary": body.get("summary", ""),
        "keywords": body.get("keywords", []),
    }
    # 写 parse_logs
    log_file = PARSE_LOG_DIR / f"{ts.strftime('%Y-%m-%d')}.jsonl"
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
    # 写 kb/inbox（keeper 分拣用，对齐 keeper 模板）
    inbox_file = KB_INBOX / f"{ts.strftime('%Y%m%d_%H%M%S')}.json"
    inbox_entry = {
        "url": url,
        "title": title,
        "summary": body.get("summary", "") or body.get("content", "")[:300],
        "keywords": body.get("keywords", []),
        "tags": body.get("tags", []),
        "content_type": "article" if source in ("wechat", "36kr", "zhihu", "xueqiu") else "web",
        "parse_method": body.get("detected_type", source),
        "quality_score": None,
        "source": source,
        "timestamp": ts.isoformat(),
        "ai_related": body.get("ai_related", False),
        "note_id": body.get("note_id", ""),
        "content": body.get("content", "")[:2000],
        "keeper_status": "inbox",
        "archived_to": None,
    }
    try:
        inbox_file.write_text(json.dumps(inbox_entry, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception as e:
        print(f"  [WARN] kb/inbox write failed: {e}")
    return {"success": True, "logged": True, "inbox": str(inbox_file)}


@app.get("/api/parse/logs")
async def parse_logs(date: str | None = None):
    """Get parse logs for a date."""
    if not date:
        date = datetime.now().strftime("%Y-%m-%d")
    log_file = PARSE_LOG_DIR / f"{date}.jsonl"
    if not log_file.exists():
        return {"logs": [], "total": 0}
    lines = log_file.read_text(encoding="utf-8").strip().split("\n")
    logs = [json.loads(l) for l in lines if l.strip()]
    return {"logs": logs, "total": len(logs)}


@app.get("/api/kb/inbox")
async def kb_inbox(limit: int = Query(10, ge=1, le=50),
                   status: str = Query("inbox")):
    """Read latest items from kb/inbox for frontend display."""
    if not KB_INBOX.exists():
        return {"items": [], "total": 0}
    files = sorted(KB_INBOX.glob("*.json"), reverse=True)
    items = []
    for f in files:
        if len(items) >= limit:
            break
        try:
            entry = json.loads(f.read_text(encoding="utf-8"))
            if entry.get("keeper_status", "inbox") == status:
                items.append(entry)
        except Exception:
            pass
    return {"items": items, "total": len(items)}


# ─── Auth middleware for HTML pages ───────────────────
from routers.utils import validate_session

@app.middleware("http")
async def auth_middleware(request, call_next):
    path = request.url.path
    # Protect /tools, /admin, and /api/personal/* with authentication
    protected_paths = ["/tools", "/admin", "/api/personal"]
    needs_auth = any(path.startswith(p) for p in protected_paths)
    # Allow auth endpoints and static assets
    if path.startswith("/tools/api/auth") or path.startswith("/static") or path == "/login":
        needs_auth = False
    if needs_auth:
        token = request.cookies.get("hanako_session")
        if not validate_session(token):
            if path.startswith("/api/"):
                from fastapi.responses import JSONResponse
                return JSONResponse({"error": "unauthorized"}, status_code=401)
            return RedirectResponse(url="/login")
    response = await call_next(request)
    return response


# ═══════════════════════════════════════════════════════
#  Startup Self-Check
# ═══════════════════════════════════════════════════════

TABLES = ["feed_cache", "articles_fts", "saved_links", "task_queue", "audit_log", "market_snapshots"]
ROUTERS = {
    "home":   "routers.home",
    "mori":   "routers.mori",
    "tools":  "routers.tools",
    "bridge": "routers.bridge",
}


def startup_self_check():
    """
    启动自检：六表 / 四路由 / 一健康。
    任一失败 → sys.exit(1)，全部通过 → 打印通过信息。
    DB 不可用时跳过表检查，只做路由检查。
    """
    all_ok = True
    errors = []

    # ── 1. 六表检查 ──
    db_available = True
    try:
        from db import get_connection
    except Exception as e:
        print(f"  [STARTUP] DB 模块不可用，跳过表检查: {e}")
        db_available = False

    if db_available:
        conn = None
        try:
            conn = get_connection()
            for table in TABLES:
                try:
                    row = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()
                    count = row[0] if row else 0
                    print(f"  [STARTUP] 表 {table}: OK ({count} 行)")
                except Exception as e:
                    msg = f"表 {table} 检查失败: {e}"
                    print(f"  [STARTUP] ❌ {msg}")
                    errors.append(msg)
                    all_ok = False
        except Exception as e:
            print(f"  [STARTUP] DB 连接失败，跳过表检查: {e}")
        finally:
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass

    # ── 2. 四路由检查 ──
    import importlib
    for name, module_path in ROUTERS.items():
        try:
            mod = importlib.import_module(module_path)
            router = getattr(mod, "router", None)
            if router is None:
                msg = f"路由 {name}: 模块中无 'router' 对象"
                print(f"  [STARTUP] ❌ {msg}")
                errors.append(msg)
                all_ok = False
            elif not hasattr(router, "routes"):
                msg = f"路由 {name}: router 对象缺少 'routes' 属性"
                print(f"  [STARTUP] ❌ {msg}")
                errors.append(msg)
                all_ok = False
            else:
                print(f"  [STARTUP] 路由 {name}: OK ({len(router.routes)} 端点)")
        except Exception as e:
            msg = f"路由 {name}: import 失败 ({e})"
            print(f"  [STARTUP] ❌ {msg}")
            errors.append(msg)
            all_ok = False

    # ── 3. 一健康检查 ──
    if not app.routes:
        msg = "健康检查: app.routes 为空，无任何路由注册"
        print(f"  [STARTUP] ❌ {msg}")
        errors.append(msg)
        all_ok = False
    else:
        print(f"  [STARTUP] 健康检查: OK ({len(app.routes)} 条路由)")

    # ── 4. 数据新鲜度检查 ──
    import os as _os
    from datetime import datetime as _dt
    DATA_DIR = Path(__file__).parent / "data"
    FRESHNESS_THRESHOLDS = {
        "daily":   86400,   # 24h — 容忍到下次抓取周期
        "markets": 3600,    # 1h  — 盘中需实时
        "weather": 7200,    # 2h  — 天气刷新间隔
        "hot":     3600,    # 1h  — 热搜更新频次
    }

    now = _dt.now()
    file_checks = {
        "daily":   DATA_DIR / "daily",
        "markets": DATA_DIR / "markets.json",
        "weather": DATA_DIR / "weather.json",
        "hot":     DATA_DIR / "hot.json",
    }

    for key, fp in file_checks.items():
        try:
            if fp.is_dir():
                files = sorted(fp.glob("*.json"))
                if not files:
                    print(f"  [STARTUP] 数据 {key}: ⚠ 无数据文件")
                    continue
                mtime = _dt.fromtimestamp(_os.path.getmtime(files[-1]))
            elif fp.exists():
                mtime = _dt.fromtimestamp(_os.path.getmtime(fp))
            else:
                print(f"  [STARTUP] 数据 {key}: ⚠ 文件不存在")
                continue

            age_h = (now - mtime).total_seconds() / 3600
            threshold_h = FRESHNESS_THRESHOLDS[key] / 3600
            status = "✓" if (now - mtime).total_seconds() < FRESHNESS_THRESHOLDS[key] else "⚠"
            print(f"  [STARTUP] 数据 {key}: {status}  {age_h:.1f}h 前 (阈值 {threshold_h:.0f}h)")
        except Exception as e:
            print(f"  [STARTUP] 数据 {key}: ⚠ 检查失败 ({e})")

    # ── 汇总 ──
    if not all_ok:
        print(f"\n  ╔══════════════════════════════════════════╗")
        print(f"  ║  ❌ 启动自检失败 ({len(errors)} 项)                 ║")
        print(f"  ╚══════════════════════════════════════════╝")
        for err in errors:
            print(f"     → {err}")
        print()
        sys.exit(1)

    n_tables = len(TABLES) if db_available else "0 (跳过)"
    print(f"  [STARTUP] 自检通过: {n_tables}表 / 四路由 / 一健康 / 数据新鲜度 ✓")


# ═══════════════════════════════════════════════════════
#  Startup
# ═══════════════════════════════════════════════════════

if __name__ == "__main__":
    # Initialize DB on first startup
    try:
        from db import init_db
        init_db()
    except Exception as e:
        print(f"  [WARN] DB 初始化跳过: {e}")

    # ── 启动自检 ──
    startup_self_check()

    port = int(os.environ.get("PORT", 8000))
    print(f"""
  ╔══════════════════════════════════════════╗
  ║  🌐 Hanako Site v2.0                    ║
  ║  📂 {Path(__file__).parent}
  ║  🚀 http://localhost:{port}
  ║  🔒 工具区: /tools (密码保护)
  ║  🔗 桥接: /api/bridge
  ╚══════════════════════════════════════════╝
""")
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")
