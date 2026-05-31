"""
Mori 每日文摘生成器 v2
从全球中英文信息源拉取优质内容 → 拉取全文 → DeepSeek翻译 → 生成图文日报

v2 更新（2026-05-29）：
  - 文章全文拉取（从 link 提取正文）
  - 全文翻译（body_cn）
  - 图片提取修复（RSS enclosure + og:image + 正文首图）
  - 来源标签强化
"""
import json, os, re, hashlib, html as html_mod, urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / 'data' / 'daily'
OUT_DIR = BASE_DIR / 'daily'
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(OUT_DIR, exist_ok=True)

# ── 加载 .env ──
def _load_env():
    env_path = BASE_DIR / '.env'
    if env_path.exists():
        for line in env_path.read_text(encoding='utf-8').splitlines():
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                k, v = line.split('=', 1)
                os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))
_load_env()

# DeepSeek API
DS_API_KEY = os.environ.get('DS_API_KEY', '')
DS_API_URL = 'https://api.deepseek.com/chat/completions'

# 代理
PROXY = os.environ.get('HTTP_PROXY') or 'http://127.0.0.1:7890'

# ── 财新 Cookie ──
_caixin_cookie_path = BASE_DIR / 'data' / 'caixin_cookies.json'
CAIXIN_COOKIES = {}
if _caixin_cookie_path.exists():
    try:
        CAIXIN_COOKIES = json.loads(_caixin_cookie_path.read_text(encoding='utf-8'))
    except Exception:
        pass

# ==================== 信息源矩阵 ====================
# 备选源（当主源失效时替换）:
#   经济金融备选: MarketWatch (feeds.marketwatch.com/marketwatch/marketpulse/)
#   精品吃喝备选: bonappetit.com/feed
SOURCES = {
    "商业科技": [
        # 财新科技：不通过RSS，直接在 generate_daily 中单独抓取
        {"url": "https://techcrunch.com/feed/", "label": "TechCrunch", "lang": "en"},
        {"url": "https://www.theverge.com/rss/index.xml", "label": "The Verge", "lang": "en"},
        {"url": "https://feeds.arstechnica.com/arstechnica/index", "label": "Ars Technica", "lang": "en"},
        {"url": "https://www.wired.com/feed/rss", "label": "Wired", "lang": "en"},
        {"url": "https://36kr.com/feed", "label": "36氪", "lang": "zh"},
        {"url": "https://hnrss.org/best", "label": "Hacker News", "lang": "en"},
    ],
    "经济金融": [
        # 财新财经：通过 caixin_cookies.json 单独抓取
        {"url": "https://www.scmp.com/rss/91/feed", "label": "SCMP", "lang": "en"},
        {"url": "https://feeds.bloomberg.com/markets/news.rss", "label": "Bloomberg", "lang": "en"},
        {"url": "https://feeds.a.dj.com/rss/RSSMarketsMain.xml", "label": "WSJ", "lang": "en"},
        {"url": "https://www.ft.com/rss/home", "label": "FT", "lang": "en"},
        {"url": "https://www.economist.com/finance-and-economics/rss.xml", "label": "The Economist", "lang": "en"},
        {"url": "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=100003114", "label": "CNBC", "lang": "en"},
    ],
    "精品吃喝": [
        {"url": "https://sprudge.com/feed", "label": "Sprudge", "lang": "en"},
        {"url": "https://www.thefreshloaf.com/rss.xml", "label": "The Fresh Loaf", "lang": "en"},
        # 下厨房：直接网页抓取，不做RSS（见 fetch_xiachufang_articles）
        {"url": "https://www.seriouseats.com/feed", "label": "Serious Eats", "lang": "en"},
        {"url": "https://www.eater.com/rss/index.xml", "label": "Eater", "lang": "en"},
    ],
    "文艺影视": [
        {"url": "https://aeon.co/feed", "label": "Aeon", "lang": "en"},
        {"url": "https://longreads.com/feed/", "label": "Longreads", "lang": "en"},
    ],
}

# ==================== 全文拉取 ====================
def _make_request(url, timeout=15):
    """发起 HTTP 请求（走代理）"""
    req = urllib.request.Request(url, headers={
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9,zh-CN;q=0.8',
    })
    if PROXY:
        opener = urllib.request.build_opener(
            urllib.request.ProxyHandler({'http': PROXY, 'https': PROXY}))
        return opener.open(req, timeout=timeout)
    return urllib.request.urlopen(req, timeout=timeout)


def _extract_body_text(html_text, url=''):
    """从 HTML 提取正文（无需外部依赖的简单算法）"""
    try:
        # 去掉 script / style / nav / footer / header
        for tag in ['script', 'style', 'nav', 'footer', 'header', 'aside',
                     'noscript', 'iframe', 'svg', 'form']:
            html_text = re.sub(
                rf'<{tag}[^>]*>.*?</{tag}>', '', html_text,
                flags=re.DOTALL | re.IGNORECASE)
        html_text = re.sub(r'<[^>]+>', ' ', html_text)
        html_text = html_mod.unescape(html_text)
        # 压缩空白
        html_text = re.sub(r'\n\s*\n', '\n\n', html_text)
        html_text = re.sub(r'[ \t\r]+', ' ', html_text)
        lines = [l.strip() for l in html_text.splitlines() if l.strip()]
        text = '\n'.join(lines)
        return text[:6000] if len(text) > 6000 else text
    except Exception as e:
        return ''


def _clean_caixin_body(text):
    """清洗财新文章 body：移除导航/热榜/广告/版权声明等非正文内容"""
    if not text:
        return text

    # 财新文章的正文标识：正文从这些标记开始，到这些标记之前结束
    content_start_markers = [
        '文｜',      # 财新周刊标志性开头
        '■',        # 文章结尾标记（找到这个标记后往前找正文开头）
    ]
    # 常见的财新正文起始句式
    content_start_sentences = ['【财新网】']
    # 正文结束标记
    content_end_markers = [
        '责任编辑', '版面编辑', '推荐进入', '更多更快',
        'In Depth:', 'Read More',
        '本文仅代表作者', '风险提示',
        '版权声明', '版权所有', '未经许可', '不得转载',
        '京ICP备', '京公网安备',
        '相关报道', '【财新周刊】',
        '推荐进入', '财新数据库',
    ]
    # 检测到这些关键字后，继续向下扫描直至退出页脚区域
    footer_enter_keywords = [
        '小鹅通', '财新与小鹅通', '推荐进入',
        '更多更快财经资讯',
    ]

    lines = text.split('\n')
    n = len(lines)

    # ── 第一步：找到正文开始行 ──
    content_start = -1
    # 优先找【财新网】（正文真正起始），其次找文｜
    for i, line in enumerate(lines):
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith('【财新网】'):
            content_start = i
            break
    
    if content_start == -1:
        for i, line in enumerate(lines):
            stripped = line.strip()
            if not stripped:
                continue
            if any(stripped.startswith(m) for m in content_start_markers):
                content_start = i
                break

    # 如果没找到精确标记，用启发式规则：找第一个长度>30且含中文的正文句
    if content_start == -1:
        for i, line in enumerate(lines):
            stripped = line.strip()
            if len(stripped) >= 30:
                _nav_keywords = ['商城', '我闻', '周刊', 'English', 'mini+', '登录', '注册',
                                '订阅', '财新', 'APP', '应用下载', '机构订阅']
                has_chinese = any('\u4e00' <= c <= '\u9fff' for c in stripped)
                has_punct = any(c in stripped for c in '，。？！、')
                is_nav = any(kw in stripped for kw in _nav_keywords)
                if has_chinese and (has_punct or len(stripped) >= 40) and not is_nav:
                    content_start = i
                    break

    if content_start == -1:
        return ''

    # ── 第二步：找到正文结束行 ──
    content_end = n
    in_footer = False
    for i in range(content_start, n):
        stripped = lines[i].strip()
        if not stripped:
            if in_footer:
                content_end = i
                break
            continue
        # 检测页脚区域入口
        if any(kw in stripped for kw in footer_enter_keywords):
            in_footer = True
            content_end = i
            break
        # 正文结束标记
        if any(stripped.startswith(m) for m in content_end_markers):
            content_end = i
            break
        lower = stripped.lower()
        _copyright_kw = ['版权声明', 'copyright', '京icp', '京公网安', '未经许可', '不得转载']
        if any(kw in lower for kw in _copyright_kw):
            content_end = i
            break
        # 页脚短行模式：行首为 '-->' 或单行长度<10的页脚文案
        if stripped in ['-->', '-->-->'] or (len(stripped) < 8 and any(kw in stripped for kw in ['订阅', '下载', '指数', '我闻', '周刊'])):
            # 检查前后文是否都是类似页脚行
            content_end = i
            break

    # ── 第三步：提取正文 ──
    result_lines = lines[content_start:content_end]
    while result_lines and not result_lines[0].strip():
        result_lines = result_lines[1:]
    while result_lines and not result_lines[-1].strip():
        result_lines = result_lines[:-1]

    result = '\n'.join(result_lines).strip()
    return result


def _extract_image(html_text, url=''):
    """提取文章主图：og:image > 正文首张 > None"""
    # og:image
    m = re.search(r'<meta\s+property=["\']og:image["\']\s+content=["\']([^"\']+)["\']', html_text, re.I)
    if not m:
        m = re.search(r'<meta\s+content=["\']([^"\']+)["\']\s+property=["\']og:image["\']', html_text, re.I)
    if not m:
        m = re.search(r'<meta\s+name=["\']twitter:image["\']\s+content=["\']([^"\']+)["\']', html_text, re.I)
    if m:
        img = m.group(1)
        if img.startswith('//'): img = 'https:' + img
        return img

    # 正文首图（跳过 icon/logo/tracker）
    imgs = re.findall(r'<img[^>]+src=["\']([^"\']+)["\']', html_text, re.I)
    for img in imgs:
        low = img.lower()
        skip = any(k in low for k in ['icon', 'logo', 'avatar', 'pixel', 'track', '1x1', 'blank', 'spacer', 'badge', 'button'])
        if not skip:
            if img.startswith('//'): img = 'https:' + img
            return img
    return None


def fetch_article_body(url, timeout=12, cookies=None):
    """拉取文章页 HTML，提取正文 + 图片（财新域名自动使用 Cookie）"""
    try:
        # 财新域名自动使用已加载的 Cookie
        if not cookies and 'caixin.com' in url and CAIXIN_COOKIES:
            cookies = CAIXIN_COOKIES
        if cookies and 'caixin.com' in url:
            cookie_str = '; '.join(f'{k}={v}' for k, v in cookies.items())
            req = urllib.request.Request(url, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9,zh-CN;q=0.8',
                'Cookie': cookie_str,
            })
            if PROXY:
                opener = urllib.request.build_opener(
                    urllib.request.ProxyHandler({'http': PROXY, 'https': PROXY}))
                resp = opener.open(req, timeout=timeout)
            else:
                resp = urllib.request.urlopen(req, timeout=timeout)
        else:
            resp = _make_request(url, timeout=timeout)
        raw = resp.read()
        # 尝试解码
        charset = 'utf-8'
        content_type = resp.headers.get('Content-Type', '')
        m = re.search(r'charset=([^\s;]+)', content_type)
        if m: charset = m.group(1)
        try:
            html_text = raw.decode(charset, errors='ignore')
        except:
            html_text = raw.decode('utf-8', errors='ignore')

        body = _extract_body_text(html_text, url)
        # 财新文章专用清洗
        if 'caixin.com' in url:
            body = _clean_caixin_body(body)
        image = _extract_image(html_text, url)
        return body, image
    except Exception as e:
        return '', None


# ==================== RSS 模板文案清洗 ====================
_rss_boilerplate_re = re.compile(
    r'^This article (?:is from|originally appeared on).+?This is the RSS feed version\.\s*',
    re.I
)

def _strip_rss_boilerplate(desc):
    """移除 RSS 摘要中的模板文案，仅保留真正的文章导语。
    例如 Sprudge 的 'This article is from the coffee website Sprudge... This is the RSS feed version.' 前缀。
    """
    if not desc:
        return ''
    cleaned = _rss_boilerplate_re.sub('', desc).strip()
    # 如果清理后为空或只剩极短片段，视为无效
    if len(cleaned) < 30:
        return ''
    return cleaned


# ==================== 翻译 ====================
def _call_deepseek(prompt, max_tokens=2000, temperature=0.3):
    """通用 DeepSeek API 调用"""
    if not DS_API_KEY:
        return None

    data = json.dumps({
        'model': 'deepseek-chat',
        'messages': [{'role': 'user', 'content': prompt}],
        'temperature': temperature,
        'max_tokens': max_tokens,
    }).encode()

    txn = urllib.request.Request(DS_API_URL, data=data, headers={
        'Authorization': f'Bearer {DS_API_KEY}',
        'Content-Type': 'application/json',
    })
    if PROXY:
        opener = urllib.request.build_opener(
            urllib.request.ProxyHandler({'http': PROXY, 'https': PROXY}))
        resp = opener.open(txn, timeout=60)
    else:
        resp = urllib.request.urlopen(txn, timeout=60)

    result = json.loads(resp.read().decode())
    return result['choices'][0]['message']['content'].strip()


def translate_deepseek(text, target='zh'):
    """翻译短文本（标题/摘要）"""
    if not text or len(text.strip()) < 20:
        return text
    if not DS_API_KEY:
        return text

    prompt = f'将以下英文翻译成流畅自然的中文，保留原文风格和信息密度。只返回翻译结果，不要加任何解释：\n\n{text[:4000]}'

    try:
        return _call_deepseek(prompt, max_tokens=2000)
    except Exception as e:
        print(f'  翻译失败: {e}')
        return text[:200] + '... [翻译失败]'


def translate_long(text):
    """翻译长文本（全文），分块处理"""
    if not text or len(text.strip()) < 30:
        return text
    if not DS_API_KEY:
        return text

    # 如果文本较短，直接翻译
    if len(text) <= 3500:
        prompt = f'将以下英文文章翻译成流畅自然的中文，保留原文风格、信息密度和段落结构。只返回翻译结果，不要加任何解释：\n\n{text}'
        try:
            return _call_deepseek(prompt, max_tokens=4096)
        except Exception as e:
            print(f'  全文翻译失败: {e}')
            return text[:200] + '... [翻译失败]'

    # 长文本分块翻译
    # 按段落分割
    paragraphs = [p.strip() for p in text.split('\n') if p.strip()]
    # 合并小段
    chunks = []
    current = ''
    for p in paragraphs:
        if len(current) + len(p) < 2500:
            current = (current + '\n\n' + p).strip()
        else:
            if current:
                chunks.append(current)
            current = p
    if current:
        chunks.append(current)

    # 限制最多翻译 3 个块（约 7500 字）
    chunks = chunks[:3]

    translated = []
    for i, chunk in enumerate(chunks):
        try:
            prompt = f'将以下英文文章片段翻译成流畅自然的中文（第{i+1}/{len(chunks)}部分）。保留原文风格和信息密度。只返回翻译结果：\n\n{chunk[:3500]}'
            result = _call_deepseek(prompt, max_tokens=4096)
            if result:
                translated.append(result)
            else:
                translated.append(f'[第{i+1}段翻译失败]')
        except Exception as e:
            print(f'  分块翻译{i+1}失败: {e}')
            translated.append(chunk[:100] + '... [翻译失败]')

    return '\n\n'.join(translated)


# ==================== RSS 拉取 ====================
def fetch_rss(url, label):
    """拉取 RSS/Atom feed（支持代理 + 自定义 UA）"""
    import xml.etree.ElementTree as ET
    try:
        req = urllib.request.Request(url, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/rss+xml, application/xml, text/xml, */*',
        })
        if PROXY:
            opener = urllib.request.build_opener(
                urllib.request.ProxyHandler({'http': PROXY, 'https': PROXY}))
            resp = opener.open(req, timeout=15)
        else:
            resp = urllib.request.urlopen(req, timeout=15)
        text = resp.read().decode('utf-8', errors='ignore')
        root = ET.fromstring(text)

        # 命名空间
        ns = {'media': 'http://search.yahoo.com/mrss/',
              'dc': 'http://purl.org/dc/elements/1.1/',
              'atom': 'http://www.w3.org/2005/Atom',
              'content': 'http://purl.org/rss/1.0/modules/content/'}

        items = []

        # RSS 2.0
        for item in root.iter('item'):
            title = item.find('title')
            link = item.find('link')
            desc = item.find('description')
            pub = item.find('pubDate')
            img = None

            # 图片提取：1) media:content 2) enclosure 3) description 内 img
            media_content = item.find('media:content', ns)
            if media_content is not None:
                img = media_content.get('url', '')
            if not img:
                enclosure = item.find('enclosure')
                if enclosure is not None:
                    img = enclosure.get('url', '')
            if not img and desc is not None and desc.text:
                m = re.search(r'<img[^>]+src=["\']([^"\']+)["\']', desc.text, re.I)
                if m: img = m.group(1)
            if img and img.startswith('//'):
                img = 'https:' + img

            # 保留完整描述（用于备选），但先截断显示用
            desc_raw = (desc.text or '') if desc is not None else ''
            # 去掉 HTML 标签得到纯文本摘要
            desc_clean = re.sub(r'<[^>]+>', ' ', desc_raw)
            desc_clean = html_mod.unescape(desc_clean)
            desc_clean = re.sub(r'\s+', ' ', desc_clean).strip()

            items.append({
                'title': title.text.strip() if title is not None and title.text else '',
                'link': link.text.strip() if link is not None and link.text else '',
                'desc': desc_clean[:500],
                'image': img,
                'pub': pub.text.strip() if pub is not None and pub.text else '',
                'source': label,
            })

        # Atom
        if not items:
            atom_ns = {'atom': 'http://www.w3.org/2005/Atom'}
            for entry in root.findall('atom:entry', atom_ns):
                title = entry.find('atom:title', atom_ns)
                link = entry.find('atom:link', atom_ns)
                summary = entry.find('atom:summary', atom_ns)
                updated = entry.find('atom:updated', atom_ns)
                img = None
                if summary is not None and summary.text:
                    m = re.search(r'<img[^>]+src=["\']([^"\']+)["\']', summary.text, re.I)
                    if m: img = m.group(1)
                if img and img.startswith('//'):
                    img = 'https:' + img
                summary_text = (summary.text or '') if summary is not None else ''
                summary_clean = re.sub(r'<[^>]+>', ' ', summary_text)
                summary_clean = html_mod.unescape(summary_clean)
                summary_clean = re.sub(r'\s+', ' ', summary_clean).strip()

                items.append({
                    'title': title.text.strip() if title is not None else '',
                    'link': link.get('href', '') if link is not None else '',
                    'desc': summary_clean[:500],
                    'image': img,
                    'pub': updated.text.strip() if updated is not None else '',
                    'source': label,
                })

        return items
    except Exception as e:
        print(f'  RSS {label} 失败: {e}')
        return []


def is_recent(date_str, days=3):
    """判断是否在最近 N 天内"""
    if not date_str: return True
    try:
        from email.utils import parsedate_to_datetime
        dt = parsedate_to_datetime(date_str)
        return (datetime.now(timezone.utc) - dt).days < days
    except:
        return False


def _fetch_caixin():
    """用 Playwright 抓取财新付费内容（统一入口：caixin_scraper.py）"""
    import subprocess
    script = BASE_DIR / 'caixin_scraper.py'
    if not script.exists():
        print(f'    [SKIP] caixin_scraper.py 不存在')
        return []
    try:
        result = subprocess.run(
            ['python', str(script), 'list'],
            capture_output=True, text=True, timeout=60, cwd=str(BASE_DIR)
        )
        stdout = result.stdout.strip()
        if stdout:
            try:
                return json.loads(stdout)
            except json.JSONDecodeError:
                return []
        return []
    except subprocess.TimeoutExpired:
        print('    [TIMEOUT] 财新 Playwright 超时')
        return []
    except Exception as e:
        print(f'    [ERROR] 财新抓取失败: {e}')
        return []


def fetch_caixin_articles(cookies, count=15):
    """用已登录 Cookie 抓取财新文章，返回文章列表"""
    if not cookies:
        print('  [SKIP] 无财新 Cookie，跳过')
        return []

    cookie_str = '; '.join(f'{k}={v}' for k, v in cookies.items())
    articles = []

    try:
        # 1. 抓取财新移动首页获取文章链接
        req = urllib.request.Request('https://m.caixin.com/', headers={
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1',
            'Cookie': cookie_str,
            'Accept': 'text/html,application/xhtml+xml',
        })
        if PROXY:
            opener = urllib.request.build_opener(
                urllib.request.ProxyHandler({'http': PROXY, 'https': PROXY}))
            resp = opener.open(req, timeout=20)
        else:
            resp = urllib.request.urlopen(req, timeout=20)
        html_text = resp.read().decode('utf-8', errors='ignore')

        # 2. 提取文章链接（去重保序）
        links = re.findall(
            r'href=["\']([^"\']*caixin\.com/\d{4}-\d{2}-\d{2}/\d+\.html)["\']',
            html_text, re.I)
        links = [l if l.startswith('http') else 'https:' + l if l.startswith('//') else 'https://' + l for l in links]
        links = list(dict.fromkeys(links))[:count]
        print(f'  财新首页: 发现 {len(links)} 篇文章')

        # 3. 逐篇抓取正文
        for i, link in enumerate(links):
            try:
                body, image = fetch_article_body(link, timeout=15, cookies=cookies)
                # 从正文第一行提取标题
                title = ''
                if body:
                    lines = [l.strip() for l in body.split('\n') if l.strip() and len(l.strip()) > 4]
                    title = lines[0][:100] if lines else ''
                if not title:
                    m = re.search(r'(\d+)\.html', link)
                    title = f'财新文章 {m.group(1)}' if m else '财新文章'

                articles.append({
                    'title': title,
                    'link': link,
                    'desc': body[:300] if body else '',
                    'image': image,
                    'pub': datetime.now().strftime('%Y-%m-%d'),
                    'source': '财新',
                    'body': body,
                    'body_cn': body,  # 中文源，body_cn 直接等于 body
                    'lang': 'zh',
                })
                print(f'    [{i+1}/{len(links)}] ✅ {title[:50]}')
            except Exception as e:
                print(f'    [{i+1}/{len(links)}] ❌ {e}')
    except Exception as e:
        print(f'  ❌ 财新首页抓取失败: {e}')

    return articles


def fetch_xiachufang_articles():
    """直接网页抓取下厨房热门菜谱"""
    articles = []
    try:
        req = urllib.request.Request('https://www.xiachufang.com/explore/', headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml',
        })
        if PROXY:
            opener = urllib.request.build_opener(
                urllib.request.ProxyHandler({'http': PROXY, 'https': PROXY}))
            resp = opener.open(req, timeout=15)
        else:
            resp = urllib.request.urlopen(req, timeout=15)
        html_text = resp.read().decode('utf-8', errors='ignore')

        # 提取菜谱卡片
        recipe_blocks = re.findall(
            r'<a[^>]+href=["\'](/recipe/\d+)["\'][^>]*>(.*?)</a>',
            html_text, re.DOTALL | re.I)

        seen = set()
        for href, block in recipe_blocks:
            name_m = re.search(r'class=["\']name["\'][^>]*>(.*?)</(?:p|div|span|h)', block, re.I | re.DOTALL)
            if not name_m:
                name_m = re.search(r'<h\d[^>]*>(.*?)</h\d>', block, re.I | re.DOTALL)
            title = re.sub(r'<[^>]+>', '', name_m.group(1)).strip() if name_m else ''
            if not title or title in seen:
                continue
            seen.add(title)

            img_m = re.search(r'<img[^>]+src=["\']([^"\']+)["\']', block, re.I)
            image = img_m.group(1) if img_m else None

            desc_m = re.search(r'class=["\']ing["\'][^>]*>(.*?)</(?:p|div)', block, re.I | re.DOTALL)
            desc = re.sub(r'<[^>]+>', '', desc_m.group(1)).strip() if desc_m else ''

            link = f'https://www.xiachufang.com{href}'
            articles.append({
                'title': title,
                'link': link,
                'desc': desc[:300],
                'image': image,
                'pub': datetime.now().strftime('%Y-%m-%d'),
                'source': '下厨房',
                'body': '',
                'body_cn': '',
                'lang': 'zh',
            })

        print(f'  下厨房: 抓取 {len(articles)} 道菜谱')
    except Exception as e:
        print(f'  ❌ 下厨房抓取失败: {e}')

    return articles


def _load_local_entertainment():
    """从本地 movies.json + books.json 加载文艺影视板块数据"""
    articles = []
    for fname, source_label in [('movies.json', '电影'), ('books.json', '书籍')]:
        fpath = BASE_DIR / 'data' / 'personal' / fname
        if not fpath.exists():
            print(f'    [SKIP] {fname} 不存在')
            continue
        try:
            data = json.loads(fpath.read_text(encoding='utf-8'))
            items = data if isinstance(data, list) else data.get('items', data.get('articles', []))
            for item in items:
                title = item.get('title') or item.get('name', '')
                desc_parts = []
                if item.get('director'): desc_parts.append(f"导演: {item['director']}")
                if item.get('year'): desc_parts.append(f"{item['year']}年")
                if item.get('duration'): desc_parts.append(item['duration'])
                if item.get('my_rating'): desc_parts.append(f"我的评分: {item['my_rating']}")
                if item.get('watch_date'): desc_parts.append(f"观看于 {item['watch_date']}")
                body_text = item.get('review') or item.get('comment') or item.get('body') or ''
                articles.append({
                    'title': title,
                    'link': item.get('douban_url', item.get('url', '')),
                    'desc': ' | '.join(desc_parts) if desc_parts else title,
                    'image': '',
                    'pub': item.get('watch_date', item.get('pub', item.get('date', ''))),
                    'source': source_label,
                    'body': body_text,
                    'body_cn': body_text,
                    'lang': 'zh',
                })
            print(f'    {fname}: 加载 {len(items)} 条')
        except Exception as e:
            print(f'    {fname} 读取失败: {e}')
    return articles


def _index_to_fts(daily):
    """将日报文章录入 SQLite FTS5 全文索引"""
    try:
        import db
        db.init_db()
        count = 0
        for category, articles in daily.get('categories', {}).items():
            for a in articles:
                title = a.get('title_cn') or a.get('title', '')
                content = a.get('body_cn') or a.get('body') or a.get('desc_cn') or a.get('desc', '')
                url = a.get('link', '')
                source = a.get('source', '')
                if title and content:
                    db.index_article(url, title, content, source, category)
                    count += 1
                # Also cache in feed_cache for dedup
                if url:
                    db.cache_article(
                        url=url, title=title, source=source, category=category,
                        body=a.get('body', ''), body_cn=a.get('body_cn', ''),
                        lang=a.get('lang', 'en')
                    )
        if count:
            print(f'  📚 FTS5 索引完成: {count} 篇文章')
    except Exception as e:
        print(f'  [WARN] FTS5 索引失败: {e}')


# ==================== 主流程 ====================
def generate_daily(fetch_full=True, max_full=15):
    """
    生成日报。
    - fetch_full: 是否拉取全文
    - max_full: 每个品类最多拉取多少篇全文（默认15）
    """
    today = datetime.now().strftime('%Y-%m-%d')
    daily = {'date': today, 'categories': {}}

    # ── 预加载财新文章（供商业科技 + 经济金融使用）──
    caixin_all = fetch_caixin_articles(CAIXIN_COOKIES, count=15)
    # 简单分流：标题含科技/AI/芯片等关键词的归商业科技，其余归经济金融
    _tech_kw = re.compile(r'科技|AI|芯片|编程|技术|互联网|算法|大模型|数据|机器人|半导体|5G|量子|自动驾驶|新能源', re.I)
    caixin_tech = [a for a in caixin_all if _tech_kw.search(a.get('title', '') + a.get('desc', ''))]
    caixin_fin = [a for a in caixin_all if a not in caixin_tech]

    for category, sources in SOURCES.items():
        print(f'\n📂 {category}')
        articles = []

        # ── 文艺影视：RSS + 本地文件合并 ──
        if category == '文艺影视':
            local = _load_local_entertainment()
            articles.extend(local)
            # 继续走下面的 RSS 抓取流程

        # ── 精品吃喝：额外抓取下厨房 ──
        if category == '精品吃喝':
            xiachufang = fetch_xiachufang_articles()
            articles.extend(xiachufang)

        for src in sources:
            url, label, lang = src['url'], src['label'], src['lang']
            print(f'  拉取 {label}...')
            items = fetch_rss(url, label)

            # 筛选最近3天
            items = [i for i in items if is_recent(i.get('pub', ''))]
            print(f'    → {len(items)} 篇（3天内）')

            # 英文源：翻译标题（摘要延迟到选文后再翻，减少API调用）
            if lang == 'en':
                for item in items:
                    if item.get('title'):
                        print(f'    翻译标题: {item["title"][:40]}...')
                        item['title_cn'] = translate_deepseek(item['title'])

            # 初始化 body/body_cn + 记录 lang
            for item in items:
                item.setdefault('body', '')
                item.setdefault('body_cn', '')
                item.setdefault('lang', lang)

            articles.extend(items)

        # ── 注入财新文章 ──
        if category == '商业科技' and caixin_tech:
            for ca in caixin_tech:
                ca.setdefault('body', '')
                ca.setdefault('body_cn', '')
                articles.append(ca)
            print(f'  → 财新科技: +{len(caixin_tech)} 篇')
        elif category == '经济金融' and caixin_fin:
            for ca in caixin_fin:
                ca.setdefault('body', '')
                ca.setdefault('body_cn', '')
                articles.append(ca)
            print(f'  → 财新财经: +{len(caixin_fin)} 篇')

        # ── 双键去重：title[:40] + link ──
        seen = set()
        unique = []
        for a in articles:
            t = a.get('title', '')[:40].lower().replace(' ', '')
            l = a.get('link', '').split('?')[0]
            key = (t, l)
            if key not in seen:
                seen.add(key)
                unique.append(a)

        # ── 两阶段混选 ──
        # 阶段1：按来源分组，每源限流
        articles_by_source = {}
        for a in unique:
            src = a.get('source', 'unknown')
            articles_by_source.setdefault(src, []).append(a)
        per_source_cap = max(3, 15 // max(len(articles_by_source), 1))
        pooled = []
        for src_name, src_arts in articles_by_source.items():
            top = sorted(src_arts, key=lambda x: x.get('pub', ''), reverse=True)[:per_source_cap]
            pooled.extend(top)

        # 阶段2：全局排序 + 深度优先
        pooled.sort(key=lambda x: x.get('pub', ''), reverse=True)
        deep = [a for a in pooled if len(a.get('body', '')) >= 1500 or a.get('lang') == 'zh']
        shallow = [a for a in pooled if a not in deep]
        unique = deep[:15]
        unique.extend(shallow[:15 - len(unique)])

        # ── 翻译被选中文章的摘要（延迟至此以节省API调用）──
        for item in unique:
            if item.get('lang') == 'en' and item.get('desc') and not item.get('desc_cn'):
                print(f'    翻译摘要: {item["title"][:40]}...')
                item['desc_cn'] = translate_deepseek(item['desc'][:500])

        # ── 全文拉取（所有源，前 max_full 篇）──
        if fetch_full and max_full > 0:
            full_count = 0
            for item in unique:
                if full_count >= max_full:
                    break
                link = item.get('link', '')
                if not link:
                    continue
                # 跳过已有完整 body 的（如财新已抓取全文）
                if item.get('body') and len(item['body']) > 500:
                    continue

                is_en = bool(item.get('title_cn'))  # 有翻译 = 英文源

                print(f'    拉全文 [{full_count+1}/{max_full}]: {item.get("title","")[:50]}...')
                body_text, page_image = fetch_article_body(link, timeout=12)

                if body_text:
                    item['body'] = body_text
                    print(f'      正文 {len(body_text)} 字')

                    # 英文源：保留原文，跳过 DeepSeek 全文翻译（只翻译标题+摘要）
                    if is_en:
                        item['body_cn'] = body_text
                        print(f'      ✅ 保留英文原文 ({len(body_text)} 字)')
                    else:
                        item['body_cn'] = body_text
                else:
                    # fetch 失败：用 desc 降级保留
                    fallback = item.get('desc', '')
                    if fallback:
                        fallback = _strip_rss_boilerplate(fallback)
                        if fallback:
                            item['body'] = fallback
                            print(f'      ⚠️ fetch 失败，降级用 desc ({len(fallback)} 字)')

                # 如果 RSS 没抓到图，用页面提取的
                if page_image and not item.get('image'):
                    item['image'] = page_image

                full_count += 1

        # ── --no-full 降级：未拉全文的文章用 desc 兜底 ──
        if not fetch_full:
            for item in unique:
                if not item.get('body', '').strip() and item.get('desc', ''):
                    desc = _strip_rss_boilerplate(item['desc'])
                    if not desc:
                        continue
                    item['body'] = desc
                    if item.get('desc_cn'):
                        item['body_cn'] = item['desc_cn']

        # ── body=0 硬过滤：空正文或仅空白的文章直接拒绝 ──
        body0_before = len(unique)
        unique = [a for a in unique if a.get('body', '').strip()]
        body0_rejected = body0_before - len(unique)
        if body0_rejected:
            print(f'  🚫 body=0 过滤: 拒绝 {body0_rejected} 篇空正文文章')

        # ── 质量过滤：body太短的文章不入选 ──
        min_body_len = 100 if not fetch_full else 300
        unique = [a for a in unique
                  if len(a.get('body', '').strip()) >= min_body_len
                  or len(a.get('body_cn', '').strip()) >= min_body_len]

        # ── 重试：板块 < 6 篇时，对未入选文章重拉全文（仅 full 模式）──
        if fetch_full and len(unique) < 6:
            retry_candidates = [a for a in pooled if a not in unique]
            for retry_item in retry_candidates:
                if len(unique) >= 6:
                    break
                rlink = retry_item.get('link', '')
                if not rlink:
                    continue
                if retry_item.get('body') and len(retry_item['body']) >= 300:
                    unique.append(retry_item)
                    continue
                try:
                    print(f'    🔄 重试拉全文: {retry_item.get("title","")[:50]}...')
                    body_text, page_image = fetch_article_body(rlink, timeout=12)
                    if body_text and len(body_text) >= 300:
                        retry_item['body'] = body_text
                        is_en_retry = bool(retry_item.get('title_cn'))
                        # 英文源保留原文，不翻译
                        if is_en_retry:
                            retry_item['body_cn'] = body_text
                        else:
                            retry_item['body_cn'] = body_text
                        if page_image and not retry_item.get('image'):
                            retry_item['image'] = page_image
                        unique.append(retry_item)
                        print(f'      ✅ 重试成功: {len(body_text)} 字')
                    else:
                        # 重试也失败，降级用 desc
                        fallback = retry_item.get('desc', '')
                        if fallback and len(fallback) >= 100:
                            retry_item['body'] = fallback
                            unique.append(retry_item)
                            print(f'      ⚠️ 重试降级用 desc ({len(fallback)} 字)')
                except Exception as e:
                    print(f'      重试失败: {e}')

        daily['categories'][category] = unique
        print(f'  ✅ {category}: {len(unique)} 篇')

    # ── 验证层：内容质量统计（在保存 JSON 前执行，确保 quality_pass 落盘）──
    quality_result = _print_quality_report(daily)
    daily['quality_pass'] = quality_result['pass']

    # ── 保存数据（含 quality_pass）──
    data_path = DATA_DIR / f'{today}.json'
    with open(data_path, 'w', encoding='utf-8') as f:
        json.dump(daily, f, ensure_ascii=False, indent=2)

    # ── FTS5 索引自动填充 ──
    _index_to_fts(daily)

    # 生成独立 HTML（备用）
    html = render_html(daily)
    html_path = OUT_DIR / 'index.html'
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(html)

    # 状态文案：根据 quality_pass 区分
    if daily['quality_pass']:
        print(f'\n✨ 日报生成完毕: {html_path}')
    else:
        print(f'\n📄 日报已生成 · 质量异常待排查: {html_path}')
    print(f'   数据: {data_path}')

    return daily


def _print_quality_report(daily):
    """验证层：输出内容质量统计（body=0率 / 污染率 / 每源贡献）"""
    all_articles = []
    for cat, arts in daily.get('categories', {}).items():
        for a in arts:
            a['_category'] = cat
            all_articles.append(a)

    total = len(all_articles)
    if total == 0:
        print('\n⚠️ 验证层: 无文章可统计')
        return {'pass': False, 'body0_rate': 1.0, 'pollution_rate': 0.0, 'source_stats': {}}

    # body=0 率
    body0_count = sum(1 for a in all_articles if not a.get('body', '').strip())

    # 污染率：body 含导航/热榜/广告/版权声明等非正文结构
    _pollution_patterns = re.compile(
        r'热门文章|热榜|推荐阅读|广告|推广|赞助内容|'
        r'版权声明|未经.*许可|不得转载|财新传媒|'
        r'关于我们|联系我们|广告服务|加入我们|'
        r'用户协议|隐私政策|意见反馈|网站导航|'
        r'京ICP备|京公网安备|网站底栏|'
        r'条评论 »|查看更多评论|复制链接|微信分享|微博分享',
        re.IGNORECASE
    )
    polluted_count = 0
    for a in all_articles:
        body = a.get('body', '')
        if body and _pollution_patterns.search(body):
            polluted_count += 1

    # 每源贡献：有正文的篇数，按 source 分组
    source_stats = {}
    for a in all_articles:
        src = a.get('source', 'unknown')
        has_body = 1 if a.get('body', '').strip() else 0
        if src not in source_stats:
            source_stats[src] = {'total': 0, 'with_body': 0}
        source_stats[src]['total'] += 1
        source_stats[src]['with_body'] += has_body

    body0_rate = body0_count / total
    pollution_rate = polluted_count / total
    quality_pass = body0_rate < 0.05 and pollution_rate < 0.10

    print(f'\n{'='*50}')
    print(f'📊 验证层 — 内容质量报告')
    print(f'{'='*50}')
    print(f'  body=0 率:  {body0_count}/{total} = {body0_rate*100:.1f}%')
    print(f'  污染率:     {polluted_count}/{total} = {pollution_rate*100:.1f}%')
    print(f'  每源贡献:')
    for src, stats in sorted(source_stats.items(), key=lambda x: -x[1]['with_body']):
        print(f'    {src}: {stats["with_body"]}/{stats["total"]} 篇有正文')
    if quality_pass:
        print(f'  ✅ 质量通过')
    else:
        print(f'  ❌ 质量异常，需排查')
    print(f'{'='*50}\n')

    return {
        'pass': quality_pass,
        'body0_rate': body0_rate,
        'pollution_rate': pollution_rate,
        'source_stats': source_stats,
    }


def render_html(daily):
    """渲染独立 HTML 日报（备用）"""
    cats = daily['categories']

    def article_html(a):
        title = a.get('title_cn') or a.get('title', '')
        link = a.get('link', '#')
        body = a.get('body_cn') or a.get('body') or a.get('desc_cn') or a.get('desc', '')
        img = a.get('image', '')
        source = a.get('source', '')

        img_tag = ''
        if img:
            img_tag = f'<img src="{html_mod.escape(img)}" style="max-width:100%;border-radius:6px;margin:12px 0;display:block;" loading="lazy" onerror="this.style.display=\'none\'" />'

        return f'''
        <article style="padding:24px 0;border-bottom:1px solid #E8E4DC;">
          <div style="display:inline-block;background:#F0EBE0;color:#6B5F52;font-size:0.7rem;padding:3px 10px;border-radius:3px;margin-bottom:8px;font-weight:600;letter-spacing:.03em;">{html_mod.escape(source)}</div>
          <a href="{html_mod.escape(link)}" target="_blank" style="font-size:1.1rem;color:#3C3C3C;text-decoration:none;display:block;margin-bottom:10px;font-weight:600;">{html_mod.escape(title)}</a>
          {img_tag}
          <div style="font-size:0.92rem;color:#5C5C5C;line-height:1.8;">{html_mod.escape(body[:600])}</div>
          <a href="{html_mod.escape(link)}" target="_blank" style="font-size:0.8rem;color:#0F4C81;margin-top:10px;display:inline-block;">阅读原文 →</a>
        </article>'''

    cats_html = ''
    for cat_name, articles in cats.items():
        if not articles: continue
        cats_html += f'<section style="margin-bottom:40px"><h2 style="font-weight:400;font-size:1.2rem;color:#3C3C3C;border-bottom:2px solid #E8E4DC;padding-bottom:8px;margin-bottom:16px">{html_mod.escape(cat_name)}</h2>'
        cats_html += ''.join(article_html(a) for a in articles)
        cats_html += '</section>'

    return f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>Mori 日报 · {daily['date']}</title>
<style>
  body {{ background:#FBF7F0; color:#3C3C3C; font-family:'Noto Serif SC',Georgia,serif; line-height:1.8; max-width:740px; margin:0 auto; padding:48px 24px 80px; }}
  h1 {{ font-weight:400; font-size:1.5rem; margin-bottom:4px; }}
  .date {{ color:#8C8C8C; font-size:0.9rem; margin-bottom:40px; }}
  a:hover {{ opacity:0.7; }}
</style>
</head>
<body>
<h1>Mori 日报</h1>
<div class="date">{daily['date']} · {sum(len(v) for v in cats.values())} 篇精选</div>
{cats_html}
</body>
</html>'''


if __name__ == '__main__':
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument('--no-full', action='store_true', help='跳过全文拉取（仅翻译标题+摘要）')
    p.add_argument('--max-full', type=int, default=15, help='每个品类最多拉几篇全文（默认15）')
    args = p.parse_args()
    generate_daily(fetch_full=not args.no_full, max_full=args.max_full)
