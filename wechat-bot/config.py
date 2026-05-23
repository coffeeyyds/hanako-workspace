"""
wechat-bot 配置文件
===============
所有路径、密钥、LLM参数都在这里集中管理。
"""

# --- 微信数据路径（已自动检测） ---
WECHAT_DATA_DIR = r"D:\WeChat\WeChat Files\wxid_zr1epn7suow822"
MSG_DIR = WECHAT_DATA_DIR + r"\Msg\Multi"
MICROMSG_DB = WECHAT_DATA_DIR + r"\Msg\MicroMsg.db"

# MSG 分片数据库（MSG0.db ~ MSG12.db，按需扩展到更多分片）
MSG_DBS = [MSG_DIR + f"\\MSG{i}.db" for i in range(13)]

# --- 轮询参数 ---
POLL_INTERVAL_SEC = 2          # 轮询间隔（秒）
CHECKPOINT_FILE = "checkpoint.json"  # 记录上次处理到的 local_id

# --- 防自回复参数 ---
SILENCE_AFTER_SEND_SEC = 10    # 发完消息后静默 X 秒（同一聊天）
COOLDOWN_PER_CHAT_SEC = 5     # 同一聊天最短回复间隔
MAX_AUTO_REPLIES_PER_CHAT = 3  # 同一聊天连续自动回复上限

# --- LLM 配置 ---
# 设为 "mock" 使用内置模拟回复（测试用）
# 设为 "api" 使用真实大模型 API
LLM_MODE = "mock"

# 真实 API 配置（LLM_MODE = "api" 时生效）
LLM_API_URL = "https://api.openai.com/v1/chat/completions"
LLM_API_KEY = ""               # 在这里填你的 API Key
LLM_MODEL = "gpt-4o-mini"

# --- 系统指令（Prompt 工程核心） ---
SYSTEM_PROMPT = """你是肖任钺的微信助手，以肖任钺的身份回复消息。

回复规则：
1. 每次只回复一到两句，五十字以内，口语化。
2. 如果消息是寒暄（"在吗""早""晚安"之类），简单回应即可。
3. 如果消息问你在干嘛、忙不忙，如实简短回答。
4. 如果消息内容不确定怎么回、或者对方只是陈述不是提问，保持沉默（返回空字符串）。
5. 不要用表情符号堆砌，最多一个。
6. 不要用"～"结尾的句式。
7. 不要主动发起新话题。

回复风格：直接、不啰嗦、像真人聊天。
"""

# --- 群聊规则 ---
MONITOR_GROUPS_ONLY = True     # True=只监控不回复群聊

# --- 自然语言开关 ---
# 收到包含这些关键词的消息时切换开关状态
ENABLE_KEYWORDS = ["我回来了", "回来了", "开自动回复", "开启自动回复"]
DISABLE_KEYWORDS = ["我去开会了", "开会了", "关自动回复", "关闭自动回复", "先忙"]
