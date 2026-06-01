"""
Baking Recipe Library — Public recipe sharing with comments and admin management.
Routes: /api/baking/* (API), /baking (page)
"""
from __future__ import annotations

import hashlib
import html as html_lib
import json
import os
import secrets
import threading
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

import httpx
from fastapi import APIRouter, File, Form, HTTPException, Query, Request, UploadFile
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse

from .utils import STATIC_DIR, detect_link_type

router = APIRouter(tags=["baking"])

# ─── Paths ─────────────────────────────────────────────
BASE_DIR = Path(__file__).parent.parent
BAKING_DIR = BASE_DIR / "workstation" / "baking"
RECIPES_PATH = BAKING_DIR / "recipes.jsonl"
COMMENTS_PATH = BAKING_DIR / "comments.jsonl"
HISTORY_PATH = BAKING_DIR / "recipe_history.jsonl"
IMAGES_DIR = BAKING_DIR / "images"

BAKING_DIR.mkdir(parents=True, exist_ok=True)
IMAGES_DIR.mkdir(parents=True, exist_ok=True)

for p in [RECIPES_PATH, COMMENTS_PATH, HISTORY_PATH]:
    if not p.exists():
        p.write_text("", encoding="utf-8")

# ─── Config ────────────────────────────────────────────
ADMIN_PIN = os.getenv("BAKING_ADMIN_PIN", "")
MAX_IMAGE_SIZE = 5 * 1024 * 1024  # 5MB
ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp"}
COMMENT_MAX_LENGTH = 500
COMMENT_MIN_LENGTH = 2
COMMENT_RATE_LIMIT_SEC = 30
WRITE_RATE_LIMIT_SEC = 8
HEAVY_RATE_LIMIT_SEC = 45
NICKNAME_MAX_LENGTH = 30
ADMIN_TOKEN_TTL_SEC = 6 * 60 * 60

# In-memory rate limiter (cleared on restart, acceptable for v1)
_rate_limit: dict[str, float] = {}
_rate_lock = threading.Lock()
_admin_tokens: dict[str, float] = {}
_admin_lock = threading.Lock()

# File write locks to prevent concurrent JSONL corruption
_recipes_lock = threading.Lock()
_comments_lock = threading.Lock()
_history_lock = threading.Lock()

# DeepSeek API for recipe parsing
DS_API_KEY = os.getenv("DS_API_KEY", "")
DS_API_URL = "https://api.deepseek.com/chat/completions"
DS_MODEL = "deepseek-chat"  # Flash / V3


# ─── Helpers ───────────────────────────────────────────

def _read_jsonl(path: Path) -> list[dict]:
    """Read all lines from a JSONL file."""
    items = []
    if path.exists():
        for line in path.read_text(encoding="utf-8").strip().split("\n"):
            line = line.strip()
            if line:
                try:
                    items.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    return items


def _write_jsonl(path: Path, items: list[dict]) -> None:
    """Write all items to a JSONL file (full overwrite, thread-safe)."""
    lock = _lock_for_path(path)
    with lock:
        lines = "\n".join(json.dumps(item, ensure_ascii=False) for item in items) + "\n"
        path.write_text(lines, encoding="utf-8")


def _append_jsonl(path: Path, item: dict) -> None:
    """Append a single item to a JSONL file (thread-safe)."""
    lock = _lock_for_path(path)
    with lock:
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")


def _lock_for_path(path: Path) -> threading.Lock:
    if path == RECIPES_PATH:
        return _recipes_lock
    if path == COMMENTS_PATH:
        return _comments_lock
    return _history_lock


def _update_recipe(recipe_id: str, updates: dict) -> dict | None:
    """Update a recipe in-place in the JSONL file."""
    recipes = _read_jsonl(RECIPES_PATH)
    for i, r in enumerate(recipes):
        if r.get("recipe_id") == recipe_id:
            r.update(updates)
            r["updated_at"] = datetime.now().isoformat()
            _write_jsonl(RECIPES_PATH, recipes)
            return r
    return None


def _update_comment(comment_id: str, updates: dict) -> dict | None:
    """Update a comment in-place in the JSONL file."""
    comments = _read_jsonl(COMMENTS_PATH)
    for i, c in enumerate(comments):
        if c.get("comment_id") == comment_id:
            c.update(updates)
            c["updated_at"] = datetime.now().isoformat()
            _write_jsonl(COMMENTS_PATH, comments)
            return c
    return None


def _short_id() -> str:
    return str(uuid.uuid4())[:8]


def _rate_check(ip: str, action: str = "comment", seconds: int = COMMENT_RATE_LIMIT_SEC) -> bool:
    """Check if IP is within rate limit. Returns True if allowed."""
    now = time.time()
    key = f"{action}:{ip}"
    with _rate_lock:
        last = _rate_limit.get(key, 0)
        if now - last < seconds:
            return False
        _rate_limit[key] = now
        return True


def _client_ip(request: Request) -> str:
    return request.client.host if request.client else "unknown"


def _public_recipe(recipe: dict) -> dict:
    return {k: v for k, v in recipe.items() if k not in {"edit_token"}}


def _append_recipe_history(recipe_id: str, before: dict | None, after: dict | None,
                           action: str, actor: str) -> dict:
    entry = {
        "history_id": _short_id(),
        "recipe_id": recipe_id,
        "action": action,
        "actor": actor,
        "before": before,
        "after": after,
        "created_at": datetime.now().isoformat(),
    }
    _append_jsonl(HISTORY_PATH, entry)
    return entry


def _issue_admin_token() -> str:
    token = secrets.token_urlsafe(32)
    with _admin_lock:
        _admin_tokens[token] = time.time() + ADMIN_TOKEN_TTL_SEC
    return token


def _verify_admin(request: Request) -> bool:
    token = request.headers.get("X-Admin-Token", "")
    if token:
        now = time.time()
        with _admin_lock:
            expires = _admin_tokens.get(token, 0)
            if expires > now:
                _admin_tokens[token] = now + ADMIN_TOKEN_TTL_SEC
                return True
            _admin_tokens.pop(token, None)
    return False


def _safe_image_path(image_path: str) -> Path:
    if not image_path.startswith("workstation/baking/images/"):
        raise HTTPException(400, "只能识别本页面上传的图片")
    full_path = (BASE_DIR / image_path).resolve()
    image_root = IMAGES_DIR.resolve()
    try:
        full_path.relative_to(image_root)
    except ValueError:
        raise HTTPException(400, "图片路径无效")
    if not full_path.exists() or not full_path.is_file():
        raise HTTPException(404, "图片文件不存在")
    return full_path


async def _ai_parse_recipe(raw_text: str, source_url: str = "") -> dict:
    """Use DeepSeek Flash to parse raw text into a readable recipe.
    Returns a dict with a human-readable recipe_md field, plus structured fields for storage.
    AI fills whatever it can find; missing fields stay empty. No forced template.
    """
    if not DS_API_KEY:
        return {}

    prompt = f"""你是一个烘焙配方解析助手。请从以下内容中提取烘焙配方，输出 JSON。

规则：
- 只提取确实存在的信息，没有的字段留空字符串或空数组
- description 是给配方卡片用的一句话简介，必须由你概括成 20-60 个中文字，写出口味、特点或适用场景；不要输出「材料」「步骤」这类栏目名
- recipe_md 是一段完整可读的配方（markdown），包含你能找到的所有内容
- 如果内容完全不包含配方，返回 {{"has_recipe": false}}
- title 必须是一个正经的配方名称，从材料/做法推断，不要保留「好吃到跺脚」「绝了」「必做」等营销文案，也不要保留烤箱品牌名或页标题后缀（如「- 小红书」）

JSON 格式：
{{
  "has_recipe": true,
  "title": "配方名称",
  "description": "一句话简介，说明这个配方的风味、特点或适合谁做",
  "recipe_md": "## 材料\\n- 面粉 200g\\n- 糖 80g\\n\\n## 步骤\\n1. 第一步\\n2. 第二步\\n\\n## 提示\\n- 注意事项",
  "ingredients": [{{"name": "材料名", "amount": "用量"}}],
  "steps": [{{"text": "步骤"}}],
  "temperature": "温度或空",
  "time": "时间或空",
  "servings": "份量或空",
  "tips": ["提示"]
}}

内容：
{raw_text[:5000]}"""

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                DS_API_URL,
                headers={
                    "Authorization": f"Bearer {DS_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": DS_MODEL,
                    "messages": [
                        {"role": "system", "content": "你是一个烘焙配方解析器。只输出合法 JSON，不输出其他内容。recipe_md 用 markdown 写，方便人阅读。"},
                        {"role": "user", "content": prompt},
                    ],
                    "temperature": 0.3,
                    "max_tokens": 3072,
                },
            )
            data = resp.json()
            content = data["choices"][0]["message"]["content"]
            content = content.strip()
            if content.startswith("```"):
                content = content.split("\n", 1)[-1]
                if content.endswith("```"):
                    content = content[:-3]
                content = content.strip()
            result = json.loads(content)
            return result if result.get("has_recipe") else {}
    except Exception as e:
        print(f"[AI Parse] Failed: {e}")
        return {}


async def _ai_reintegrate(current_recipe: dict, supplement: str) -> dict:
    """Take an existing parsed recipe and user supplement, use AI to produce final integrated recipe."""
    if not DS_API_KEY:
        return current_recipe

    prompt = f"""请将以下配方与补充内容整合，输出一个完整配方 JSON。

当前已解析的配方：
{json.dumps(current_recipe, ensure_ascii=False, indent=2)}

用户补充内容：
{supplement}

请重新整理并输出（不要遗漏补充内容中的信息）：
{{
  "title": "配方名称",
  "description": "一句话简介，说明这个配方的风味、特点或适合谁做",
  "recipe_md": "完整的 markdown 配方",
  "ingredients": [{{"name": "材料", "amount": "用量"}}],
  "steps": [{{"text": "步骤"}}],
  "temperature": "温度或空",
  "time": "时间或空",
  "servings": "份量或空",
  "tips": ["提示"]
}}"""

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                DS_API_URL,
                headers={
                    "Authorization": f"Bearer {DS_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": DS_MODEL,
                    "messages": [
                        {"role": "system", "content": "你是一个配方整合助手。只输出合法 JSON。"},
                        {"role": "user", "content": prompt},
                    ],
                    "temperature": 0.3,
                    "max_tokens": 3072,
                },
            )
            data = resp.json()
            content = data["choices"][0]["message"]["content"]
            content = content.strip()
            if content.startswith("```"):
                content = content.split("\n", 1)[-1]
                if content.endswith("```"):
                    content = content[:-3]
                content = content.strip()
            result = json.loads(content)
            return result
    except Exception as e:
        print(f"[AI Reintegrate] Failed: {e}")
        return current_recipe


async def _extract_cover_image(html: str, source_type: str) -> str:
    """Extract and download the first cover image from HTML content.
    Returns local path like 'workstation/baking/images/xxx.jpg' or empty string.
    """
    import re as _re
    img_url = None

    # Try og:image meta tag first
    for meta in _re.findall(r"<meta[^>]+>", html, _re.IGNORECASE):
        if "og:image" not in meta:
            continue
        content_match = _re.search(r'content=["\']([^"\']+)["\']', meta, _re.IGNORECASE)
        if content_match:
            img_url = content_match.group(1)
            break

    # Try WeChat data-src (lazy loaded images)
    if not img_url and source_type == "wechat":
        wx_match = _re.search(r'data-src=["\'](https?://mmbiz\.qpic\.cn/[^"\']+)["\']', html)
        if wx_match:
            img_url = wx_match.group(1)

    # Try Xiaohongshu note images (sns-webpic-qc.xhscdn.com)
    if not img_url and source_type == "xiaohongshu":
        xhs_match = _re.search(r'https?://sns-webpic-qc\.xhscdn\.com/[^"\s]+', html)
        if xhs_match:
            img_url = xhs_match.group(0)

    # Try regular img src
    if not img_url:
        img_match = _re.search(r'<img[^>]+src="(https?://[^"]+\.(?:jpg|jpeg|png|webp|gif)[^"]*)"', html, _re.IGNORECASE)
        if img_match:
            img_url = img_match.group(1)

    if not img_url:
        return ""

    if img_url.startswith("//"):
        img_url = "https:" + img_url

    # Download the image
    try:
        referer = "https://www.xiaohongshu.com/" if source_type == "xiaohongshu" else "https://mp.weixin.qq.com/"
        async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
            resp = await client.get(
                img_url,
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                    "Referer": referer,
                }
            )
            if resp.status_code != 200:
                return img_url.replace("http://", "https://", 1)
            content_type = resp.headers.get("content-type", "")
            if not content_type.startswith("image/") or len(resp.content) > MAX_IMAGE_SIZE:
                return ""
            ext = "jpg"
            if "png" in content_type:
                ext = "png"
            elif "webp" in content_type:
                ext = "webp"
            elif "gif" in content_type:
                ext = "gif"
            filename = f"{_short_id()}.{ext}"
            filepath = IMAGES_DIR / filename
            filepath.write_bytes(resp.content)
            return f"workstation/baking/images/{filename}"
    except Exception as e:
        print(f"[Cover Extract] Failed: {e}")
        return img_url.replace("http://", "https://", 1)


async def _parse_link_content(url: str) -> dict:
    """Parse a recipe link (WeChat Official Account / Xiaohongshu).
    Returns a draft recipe dict with as much auto-filled data as possible.
    Uses httpx.AsyncClient for non-blocking HTTP requests.
    """
    link_type = detect_link_type(url)
    result = {
        "source_url": url,
        "source_type": link_type,
        "title": "",
        "description": "",
        "ingredients": [],
        "steps": [],
        "tips": [],
        "raw_text": "",
        "parse_success": False,
    }

    if link_type == "wechat":
        try:
            async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
                resp = await client.get(
                    url,
                    headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
                )
                html = resp.text
            import re
            title_match = re.search(r'<title>(.+?)</title>', html, re.IGNORECASE)
            if title_match:
                title = title_match.group(1).strip()
                title = re.sub(r'\s*[_|\-–—]\s*微信公众号.*$', '', title)
                title = re.sub(r'\s*[_|\-–—]\s*微信.*$', '', title)
                result["title"] = html_lib.unescape(title)
            if not result["title"]:
                og_title = re.search(r'<meta[^>]+property=["\']og:title["\'][^>]+content=["\']([^"\']+)["\']', html, re.IGNORECASE)
                msg_title = re.search(r'var\s+msg_title\s*=\s*["\']([^"\']+)["\']', html)
                title = (og_title.group(1) if og_title else "") or (msg_title.group(1) if msg_title else "")
                result["title"] = html_lib.unescape(title).strip()
            body_match = re.search(r'id="js_content"[^>]*>(.*?)</div>\s*<script', html, re.DOTALL)
            if body_match:
                body_html = body_match.group(1)
                body_text = re.sub(r'<[^>]+>', '\n', body_html)
                body_text = re.sub(r'&nbsp;', ' ', body_text)
                body_text = re.sub(r'\n{3,}', '\n\n', body_text).strip()
                result["raw_text"] = body_text[:5000]
                result["parse_success"] = True
                result["description"] = body_text[:300]

                # AI structured parsing
                ai_result = await _ai_parse_recipe(body_text, url)
                if ai_result:
                    result["title"] = ai_result.get("title") or result["title"]
                    result["description"] = ai_result.get("description") or result["description"]
                    result["recipe_md"] = ai_result.get("recipe_md") or ""
                    result["ingredients"] = ai_result.get("ingredients") or []
                    result["steps"] = ai_result.get("steps") or []
                    result["temperature"] = ai_result.get("temperature") or ""
                    result["time"] = ai_result.get("time") or ""
                    result["servings"] = ai_result.get("servings") or ""
                    result["tips"] = ai_result.get("tips") or []
                    result["ai_parsed"] = True

                # Extract cover image
                cover_path = await _extract_cover_image(html, "wechat")
                if cover_path:
                    result["cover_image"] = cover_path
        except Exception as e:
            result["raw_text"] = f"[解析失败: {str(e)}]"

    elif link_type == "xiaohongshu":
        # Resolve short links and fetch page with desktop headers for better content
        result["parse_success"] = False
        try:
            async with httpx.AsyncClient(timeout=20.0, follow_redirects=True) as client:
                resp = await client.get(
                    url,
                    headers={
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
                        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                        "Accept-Language": "zh-CN,zh;q=0.9",
                    }
                )
                html = resp.text
                final_url = str(resp.url)
                result["source_url"] = final_url

            import re
            def meta_content(attr_name: str, attr_value: str) -> str:
                for meta in re.findall(r"<meta[^>]+>", html, re.IGNORECASE):
                    if f'{attr_name}="{attr_value}"' not in meta and f"{attr_name}='{attr_value}'" not in meta:
                        continue
                    m = re.search(r'content=["\']([^"\']+)["\']', meta, re.IGNORECASE)
                    if m:
                        return html_lib.unescape(m.group(1)).strip()
                return ""

            # Extract title
            title_match = re.search(r'<title>(.+?)</title>', html, re.IGNORECASE)
            if title_match:
                title = html_lib.unescape(title_match.group(1)).strip()
                title = re.sub(r'\s*[-–—|]\s*小红书.*$', '', title)
                result["title"] = "" if title in ("小红书", "小红书 - 你的生活指南") else title
            og_title = meta_content("property", "og:title")
            if og_title:
                og_title = re.sub(r'\s*[-–—|]\s*小红书.*$', '', og_title).strip()
                if og_title and og_title not in ("小红书", "小红书 - 你的生活指南"):
                    result["title"] = og_title

            # Extract meta description
            desc = meta_content("name", "description")
            if not desc or desc == "3 亿人的生活经验，都在小红书":
                og_desc = meta_content("property", "og:description")
                if og_desc and og_desc != "3 亿人的生活经验，都在小红书":
                    desc = og_desc
            if desc:
                result["description"] = desc[:300]

            # Proper text extraction: remove script/style/svg/noscript blocks first
            clean = html
            for tag in ['script', 'style', 'svg', 'noscript', 'iframe', 'nav', 'footer', 'header']:
                clean = re.sub(rf'<{tag}[^>]*>.*?</{tag}>', '', clean, flags=re.DOTALL | re.IGNORECASE)
            # Remove remaining HTML tags
            clean = re.sub(r'<[^>]+>', '\n', clean)
            # Decode entities and clean whitespace
            clean = re.sub(r'&nbsp;|&amp;|&lt;|&gt;|&#x2F;|&#x27;', ' ', clean)
            clean = re.sub(r'\n{3,}', '\n\n', clean)
            clean = re.sub(r'[ \t]{3,}', '  ', clean)

            # Filter: keep lines that have Chinese chars or are substantial (>30 chars)
            lines = clean.split('\n')
            filtered = []
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                has_chinese = bool(re.search(r'[\u4e00-\u9fff]', line))
                is_substantial = len(line) > 30
                # Skip common noise patterns
                is_noise = re.match(r'^(function\s|var\s|const\s|let\s|\.|#|@|\{|\}|\(|\/\*|window\.|document\.)', line)
                # Skip known footer/admin text patterns
                footer_patterns = ['ICP', '公网安备', '许可证', '营业执照', '增值电信', '医疗器械', '药品信息', '网络文化', '举报电话', '举报中心', '算法', '地址：', '电话：', '行吟信息', '关于我们', '个性化推荐', '网上有害信息']
                is_footer = any(p in line for p in footer_patterns)
                if (has_chinese or is_substantial) and not is_noise and not is_footer:
                    filtered.append(line)

            body_text = '\n'.join(filtered).strip()
            fallback_text = result.get("description", "").strip()

            if len(body_text) > 80:
                result["raw_text"] = body_text[:6000]
                result["parse_success"] = True
            elif len(fallback_text) > 30:
                result["raw_text"] = fallback_text[:6000]
                result["parse_success"] = True
            else:
                result["raw_text"] = body_text[:2000] if body_text else ""
                result["parse_success"] = False

            # AI parse the extracted text (same as WeChat branch)
            if result.get("raw_text"):
                ai_result = await _ai_parse_recipe(result["raw_text"], result.get("source_url", ""))
                if ai_result:
                    result["title"] = ai_result.get("title") or result.get("title", "")
                    result["description"] = ai_result.get("description") or result.get("description", "")
                    result["recipe_md"] = ai_result.get("recipe_md") or ""
                    result["ingredients"] = ai_result.get("ingredients") or []
                    result["steps"] = ai_result.get("steps") or []
                    result["temperature"] = ai_result.get("temperature") or ""
                    result["time"] = ai_result.get("time") or ""
                    result["servings"] = ai_result.get("servings") or ""
                    result["tips"] = ai_result.get("tips") or []
                    result["ai_parsed"] = True

            # Extract cover image
            cover_path = await _extract_cover_image(html, "xiaohongshu")
            if cover_path:
                result["cover_image"] = cover_path
        except Exception as e:
            result["raw_text"] = f"小红书链接解析失败: {str(e)}"

    else:
        try:
            async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
                resp = await client.get(
                    url,
                    headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
                )
                html = resp.text
            import re
            title_match = re.search(r'<title>(.+?)</title>', html, re.IGNORECASE)
            if title_match:
                result["title"] = title_match.group(1).strip()
            desc_match = re.search(r'<meta[^>]+name="description"[^>]+content="([^"]+)"', html, re.IGNORECASE)
            if desc_match:
                result["description"] = desc_match.group(1)[:300]
            result["raw_text"] = f"[通用链接解析，请手动补充配方内容]\n来源：{url}"
            result["parse_success"] = False
        except Exception as e:
            result["raw_text"] = f"[解析失败: {str(e)}]"
            result["parse_success"] = False

    return result


def _ocr_image(image_path: str) -> str:
    """Run OCR on an image and return extracted text."""
    try:
        import easyocr
        reader = easyocr.Reader(['ch_sim', 'en'], gpu=False)
        results = reader.readtext(image_path, detail=0)
        return "\n".join(results)
    except ImportError:
        return "[OCR 模块未安装，请手动输入内容]"
    except Exception as e:
        return f"[OCR 失败: {str(e)}]"


# ─── Page Routes ───────────────────────────────────────

@router.get("/baking", response_class=HTMLResponse)
async def baking_page():
    """Serve the baking recipe library SPA."""
    html_path = STATIC_DIR / "baking.html"
    if not html_path.exists():
        return HTMLResponse("<h1>Baking page not found</h1>", status_code=404)
    return HTMLResponse(html_path.read_text(encoding="utf-8"))


@router.get("/baking/{recipe_id}", response_class=HTMLResponse)
async def baking_detail_page(recipe_id: str):
    """Serve the baking SPA (detail view handled by JS hash routing)."""
    html_path = STATIC_DIR / "baking.html"
    if not html_path.exists():
        return HTMLResponse("<h1>Baking page not found</h1>", status_code=404)
    return HTMLResponse(html_path.read_text(encoding="utf-8"))


# ─── Static File Serving (dev mode, nginx handles in prod) ───

@router.get("/workstation/baking/images/{filename}")
async def serve_baking_image(filename: str):
    """Serve uploaded recipe images."""
    path = IMAGES_DIR / filename
    if not path.exists() or not path.is_file():
        raise HTTPException(404, "图片不存在")
    return FileResponse(path)


# ─── Recipe API ────────────────────────────────────────

@router.get("/api/baking/recipes")
async def list_recipes(
    q: str = Query(default="", description="Search query"),
    uploader: str = Query(default="", description="Filter by uploader"),
    tag: str = Query(default="", description="Filter by tag"),
    status: str = Query(default="public", description="Status filter (admin)"),
    request: Request = None,
):
    """List recipes with optional search and filter."""
    recipes = _read_jsonl(RECIPES_PATH)
    is_admin = _verify_admin(request) if request else False

    # Filter by status
    if is_admin and status == "all":
        pass  # Show all
    else:
        recipes = [r for r in recipes if r.get("status") == "public"]

    # Search
    if q:
        q_lower = q.lower()
        filtered = []
        for r in recipes:
            searchable = " ".join([
                r.get("title", ""),
                r.get("description", ""),
                r.get("uploader_nickname", ""),
                " ".join(r.get("tags", [])),
                " ".join(
                    ing.get("name", "") for ing in (r.get("ingredients") or [])
                ),
            ]).lower()
            if q_lower in searchable:
                filtered.append(r)
        recipes = filtered

    # Filter by uploader
    if uploader:
        recipes = [r for r in recipes if r.get("uploader_nickname") == uploader]

    # Filter by tag
    if tag:
        recipes = [r for r in recipes if tag in (r.get("tags") or [])]

    # Sort by created_at descending
    recipes.sort(key=lambda r: r.get("created_at", ""), reverse=True)

    # Remove sensitive fields for non-admin
    result = []
    for r in recipes:
        item = {k: v for k, v in r.items() if k != "edit_token"}
        result.append(item)

    return JSONResponse(result)


@router.get("/api/baking/recipes/{recipe_id}")
async def get_recipe(recipe_id: str, request: Request):
    """Get a single recipe by ID."""
    recipes = _read_jsonl(RECIPES_PATH)
    is_admin = _verify_admin(request)

    for r in recipes:
        if r.get("recipe_id") == recipe_id:
            if r.get("status") != "public" and not is_admin:
                raise HTTPException(404, "Recipe not found")
            item = {k: v for k, v in r.items() if k != "edit_token"}
            return JSONResponse(item)

    raise HTTPException(404, "Recipe not found")


@router.post("/api/baking/recipes")
async def create_recipe(request: Request):
    """Create a new recipe."""
    if not _rate_check(_client_ip(request), "recipe_write", WRITE_RATE_LIMIT_SEC):
        raise HTTPException(429, "提交太频繁，请稍后再试")
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(400, "需要 JSON 格式的请求体")

    # Validate required fields
    title = body.get("title", "").strip()
    uploader = body.get("uploader_nickname", "").strip()

    if not title:
        raise HTTPException(400, "标题不能为空")
    if not uploader:
        raise HTTPException(400, "上传者昵称不能为空")

    now = datetime.now().isoformat()

    recipe = {
        "recipe_id": _short_id(),
        "title": title,
        "description": body.get("description", ""),
        "cover_image": body.get("cover_image", ""),
        "source_url": body.get("source_url", ""),
        "source_type": body.get("source_type", "manual"),
        "ingredients": body.get("ingredients") or [],
        "steps": body.get("steps") or [],
        "temperature": body.get("temperature", ""),
        "time": body.get("time", ""),
        "servings": body.get("servings", ""),
        "tips": body.get("tips") or [],
        "tags": body.get("tags") or [],
        "uploader_nickname": uploader,
        "status": "public",
        "created_at": now,
        "updated_at": now,
    }

    _append_jsonl(RECIPES_PATH, recipe)
    return JSONResponse({
        "recipe_id": recipe["recipe_id"],
        "message": "配方提交成功！",
    })


@router.patch("/api/baking/recipes/{recipe_id}")
async def update_recipe(recipe_id: str, request: Request):
    """Update a recipe (anyone can edit; admin can change status)."""
    if not _rate_check(_client_ip(request), f"recipe_update:{recipe_id}", WRITE_RATE_LIMIT_SEC):
        raise HTTPException(429, "编辑太频繁，请稍后再试")
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(400, "需要 JSON 格式的请求体")

    recipes = _read_jsonl(RECIPES_PATH)
    target = None
    for r in recipes:
        if r.get("recipe_id") == recipe_id:
            target = r
            break

    if not target:
        raise HTTPException(404, "Recipe not found")
    is_admin = _verify_admin(request)

    # Allowed fields to update
    allowed_fields = [
        "title", "description", "cover_image", "source_url", "source_type",
        "ingredients", "steps", "temperature", "time", "servings", "tips", "tags",
        "uploader_nickname",
    ]
    if is_admin:
        allowed_fields.append("status")

    updates = {k: v for k, v in body.items() if k in allowed_fields}
    if not updates:
        raise HTTPException(400, "没有可更新的字段")

    updated = _update_recipe(recipe_id, updates)
    _append_recipe_history(recipe_id, target, updated, "update", "admin" if is_admin else "public")
    return JSONResponse({
        "recipe_id": recipe_id,
        "message": "配方已更新",
        "recipe": _public_recipe(updated or {}),
    })


@router.delete("/api/baking/recipes/{recipe_id}")
async def delete_recipe(recipe_id: str, request: Request):
    """Soft-delete a recipe (admin only)."""
    if not _verify_admin(request):
        raise HTTPException(403, "需要管理员权限")

    recipes = _read_jsonl(RECIPES_PATH)
    before = next((r for r in recipes if r.get("recipe_id") == recipe_id), None)
    updated = _update_recipe(recipe_id, {"status": "deleted"})
    if not updated:
        raise HTTPException(404, "Recipe not found")
    _append_recipe_history(recipe_id, before, updated, "delete", "admin")

    return JSONResponse({"message": "配方已删除（软删除）", "recipe_id": recipe_id})


@router.post("/api/baking/recipes/{recipe_id}/restore")
async def restore_recipe(recipe_id: str, request: Request):
    """Restore a soft-deleted recipe (admin only)."""
    if not _verify_admin(request):
        raise HTTPException(403, "需要管理员权限")

    recipes = _read_jsonl(RECIPES_PATH)
    before = next((r for r in recipes if r.get("recipe_id") == recipe_id), None)
    updated = _update_recipe(recipe_id, {"status": "public"})
    if not updated:
        raise HTTPException(404, "Recipe not found")
    _append_recipe_history(recipe_id, before, updated, "restore", "admin")
    return JSONResponse({"message": "配方已恢复", "recipe_id": recipe_id})


@router.get("/api/baking/recipes/{recipe_id}/history")
async def recipe_history(recipe_id: str, request: Request):
    """List recipe versions for admin rollback."""
    if not _verify_admin(request):
        raise HTTPException(403, "需要管理员权限")
    history = [
        h for h in _read_jsonl(HISTORY_PATH)
        if h.get("recipe_id") == recipe_id
    ]
    history.sort(key=lambda h: h.get("created_at", ""), reverse=True)
    return JSONResponse([
        {
            "history_id": h.get("history_id"),
            "recipe_id": recipe_id,
            "action": h.get("action"),
            "actor": h.get("actor"),
            "created_at": h.get("created_at"),
            "before_title": (h.get("before") or {}).get("title", ""),
            "after_title": (h.get("after") or {}).get("title", ""),
        }
        for h in history
    ])


@router.post("/api/baking/recipes/{recipe_id}/rollback/{history_id}")
async def rollback_recipe(recipe_id: str, history_id: str, request: Request):
    """Roll back a recipe to the state before a recorded edit/delete."""
    if not _verify_admin(request):
        raise HTTPException(403, "需要管理员权限")

    history = _read_jsonl(HISTORY_PATH)
    target_history = next(
        (h for h in history if h.get("recipe_id") == recipe_id and h.get("history_id") == history_id),
        None,
    )
    if not target_history or not target_history.get("before"):
        raise HTTPException(404, "没有可回滚的历史版本")

    recipes = _read_jsonl(RECIPES_PATH)
    current = next((r for r in recipes if r.get("recipe_id") == recipe_id), None)
    restored = dict(target_history["before"])
    restored["updated_at"] = datetime.now().isoformat()
    updated = _update_recipe(recipe_id, restored)
    if not updated:
        raise HTTPException(404, "Recipe not found")
    _append_recipe_history(recipe_id, current, updated, "rollback", "admin")
    return JSONResponse({"message": "已回滚到所选版本", "recipe": _public_recipe(updated)})


@router.post("/api/baking/parse-link")
async def parse_link(request: Request):
    """Parse a recipe link (WeChat / Xiaohongshu / other) into a draft."""
    if not _rate_check(_client_ip(request), "parse_link", HEAVY_RATE_LIMIT_SEC):
        raise HTTPException(429, "解析太频繁，请稍后再试")
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(400, "需要 JSON 格式的请求体")

    url = body.get("url", "").strip()
    if not url:
        raise HTTPException(400, "请提供链接")

    result = await _parse_link_content(url)
    return JSONResponse(result)


@router.post("/api/baking/upload-image")
async def upload_image(request: Request, file: UploadFile = File(...)):
    """Upload a recipe image. Returns the relative path."""
    if not _rate_check(_client_ip(request), "upload_image", WRITE_RATE_LIMIT_SEC):
        raise HTTPException(429, "上传太频繁，请稍后再试")
    if file.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(400, "仅支持 JPG、PNG、WebP 格式")

    content = await file.read()
    if len(content) > MAX_IMAGE_SIZE:
        raise HTTPException(400, "图片大小不能超过 5MB")

    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in (file.filename or "") else "jpg"
    if ext not in ("jpg", "jpeg", "png", "webp"):
        ext = "jpg"

    filename = f"{_short_id()}.{ext}"
    filepath = IMAGES_DIR / filename
    filepath.write_bytes(content)

    return JSONResponse({
        "path": f"workstation/baking/images/{filename}",
        "filename": filename,
        "message": "图片上传成功",
    })


@router.post("/api/baking/ocr-image")
async def ocr_image(request: Request):
    """OCR an uploaded image (by path) and return text."""
    if not _rate_check(_client_ip(request), "ocr_image", HEAVY_RATE_LIMIT_SEC):
        raise HTTPException(429, "识别太频繁，请稍后再试")
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(400, "需要 JSON 格式的请求体")

    image_path = body.get("path", "").strip()
    if not image_path:
        raise HTTPException(400, "请提供图片路径")

    full_path = _safe_image_path(image_path)

    ocr_text = _ocr_image(str(full_path))
    return JSONResponse({"text": ocr_text, "path": image_path})


# ─── Comment API ───────────────────────────────────────

@router.get("/api/baking/recipes/{recipe_id}/comments")
async def list_comments(recipe_id: str, request: Request):
    """List comments for a recipe."""
    comments = _read_jsonl(COMMENTS_PATH)
    is_admin = _verify_admin(request)

    recipe_comments = [c for c in comments if c.get("recipe_id") == recipe_id]

    if not is_admin:
        recipe_comments = [c for c in recipe_comments if c.get("status") == "public"]

    recipe_comments.sort(key=lambda c: c.get("created_at", ""))
    return JSONResponse(recipe_comments)


@router.post("/api/baking/recipes/{recipe_id}/comments")
async def create_comment(recipe_id: str, request: Request):
    """Create a comment on a recipe. Anti-spam: rate limit, honeypot check."""
    # Verify recipe exists
    recipes = _read_jsonl(RECIPES_PATH)
    recipe_exists = any(r.get("recipe_id") == recipe_id for r in recipes)
    if not recipe_exists:
        raise HTTPException(404, "Recipe not found")

    try:
        body = await request.json()
    except Exception:
        raise HTTPException(400, "需要 JSON 格式的请求体")

    # Honeypot check
    if body.get("_website", ""):
        raise HTTPException(400, "检测到机器人行为，评论被拒绝")

    nickname = body.get("nickname", "").strip()
    content = body.get("content", "").strip()

    if not nickname:
        raise HTTPException(400, "昵称不能为空")
    if len(nickname) > NICKNAME_MAX_LENGTH:
        raise HTTPException(400, f"昵称不能超过 {NICKNAME_MAX_LENGTH} 个字符")
    if not content:
        raise HTTPException(400, "评论内容不能为空")
    if len(content) < COMMENT_MIN_LENGTH:
        raise HTTPException(400, f"评论内容至少 {COMMENT_MIN_LENGTH} 个字")
    if len(content) > COMMENT_MAX_LENGTH:
        raise HTTPException(400, f"评论内容不能超过 {COMMENT_MAX_LENGTH} 字")

    # Rate limit by IP
    client_ip = request.client.host if request.client else "unknown"
    if not _rate_check(client_ip):
        raise HTTPException(429, f"评论太频繁，请 {COMMENT_RATE_LIMIT_SEC} 秒后再试")

    now = datetime.now().isoformat()
    comment = {
        "comment_id": _short_id(),
        "recipe_id": recipe_id,
        "nickname": nickname,
        "content": content,
        "status": "public",
        "created_at": now,
        "updated_at": now,
    }

    _append_jsonl(COMMENTS_PATH, comment)
    return JSONResponse({"comment_id": comment["comment_id"], "message": "评论发布成功"})


@router.delete("/api/baking/comments/{comment_id}")
async def delete_comment(comment_id: str, request: Request):
    """Soft-delete a comment (admin only)."""
    if not _verify_admin(request):
        raise HTTPException(403, "需要管理员权限")

    updated = _update_comment(comment_id, {"status": "deleted"})
    if not updated:
        raise HTTPException(404, "Comment not found")

    return JSONResponse({"message": "评论已删除", "comment_id": comment_id})


@router.patch("/api/baking/comments/{comment_id}")
async def update_comment(comment_id: str, request: Request):
    """Update a comment's status (admin only, e.g. hide/show)."""
    if not _verify_admin(request):
        raise HTTPException(403, "需要管理员权限")

    try:
        body = await request.json()
    except Exception:
        raise HTTPException(400, "需要 JSON 格式的请求体")

    new_status = body.get("status", "").strip()
    if new_status not in ("public", "hidden", "deleted"):
        raise HTTPException(400, "状态值无效，可选：public / hidden / deleted")

    updated = _update_comment(comment_id, {"status": new_status})
    if not updated:
        raise HTTPException(404, "Comment not found")

    return JSONResponse({"message": "评论状态已更新", "comment_id": comment_id})


# ─── AI Endpoints ──────────────────────────────────────

@router.post("/api/baking/ai-parse-text")
async def ai_parse_text(request: Request):
    """Parse raw text (from OCR or manual paste) into structured recipe using AI."""
    if not _rate_check(_client_ip(request), "ai_parse_text", HEAVY_RATE_LIMIT_SEC):
        raise HTTPException(429, "AI 整理太频繁，请稍后再试")
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(400, "需要 JSON 格式的请求体")

    text = body.get("text", "").strip()
    if not text:
        raise HTTPException(400, "请提供文本内容")

    result = await _ai_parse_recipe(text)
    if not result:
        return JSONResponse({"has_recipe": False, "message": "AI 未能识别出配方内容"})
    return JSONResponse(result)


@router.post("/api/baking/ai-reintegrate")
async def ai_reintegrate(request: Request):
    """Take current parsed recipe + user supplement, use AI to produce final integrated recipe."""
    if not _rate_check(_client_ip(request), "ai_reintegrate", HEAVY_RATE_LIMIT_SEC):
        raise HTTPException(429, "AI 整合太频繁，请稍后再试")
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(400, "需要 JSON 格式的请求体")

    current = body.get("current", {})
    supplement = body.get("supplement", "").strip()
    if not supplement:
        return JSONResponse(current)

    result = await _ai_reintegrate(current, supplement)
    return JSONResponse(result)


@router.get("/api/baking/random")
async def random_recipe():
    """Return a random public recipe for the '今天做什么' feature."""
    import random as _random
    recipes = _read_jsonl(RECIPES_PATH)
    public = [r for r in recipes if r.get("status") == "public"]
    if not public:
        return JSONResponse(None)
    recipe = _random.choice(public)
    return JSONResponse({k: v for k, v in recipe.items() if k != "edit_token"})


# ─── Admin Misc ────────────────────────────────────────

@router.post("/api/baking/admin/verify")
async def verify_admin(request: Request):
    """Verify admin PIN and return a session token."""
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(400, "需要 JSON 格式的请求体")

    pin = body.get("pin", "").strip()
    if pin == ADMIN_PIN and pin:
        return JSONResponse({
            "valid": True,
            "token": _issue_admin_token(),
            "message": "管理员验证成功",
            "expires_in": ADMIN_TOKEN_TTL_SEC,
        })
    return JSONResponse({"valid": False, "message": "密码错误"}, status_code=403)


# ─── Uploader Leaderboard ──────────────────────────────

@router.get("/api/baking/leaderboard")
async def uploader_leaderboard():
    """Get uploader leaderboard sorted by public recipe count."""
    recipes = _read_jsonl(RECIPES_PATH)
    public_recipes = [r for r in recipes if r.get("status") == "public"]

    counts: dict[str, int] = {}
    for r in public_recipes:
        name = r.get("uploader_nickname", "匿名")
        counts[name] = counts.get(name, 0) + 1

    leaderboard = sorted(counts.items(), key=lambda x: x[1], reverse=True)
    return JSONResponse([
        {"nickname": name, "count": count} for name, count in leaderboard
    ])
