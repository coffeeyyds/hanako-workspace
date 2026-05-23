"""
LLM 推理层
=========
支持两种模式：
  - "mock": 本地模拟回复（测试用）
  - "api":  调用真实大模型 API
"""

import json
from config import (
    LLM_MODE, LLM_API_URL, LLM_API_KEY, LLM_MODEL, SYSTEM_PROMPT
)


def call_llm(message_text, chat_context=None):
    """
    调用 LLM 生成回复。

    Args:
        message_text: 对方发来的消息文本
        chat_context: 最近几条聊天上下文（list of dict）

    Returns:
        回复文本字符串，空字符串表示不回复
    """
    if LLM_MODE == "mock":
        return _mock_reply(message_text)

    if LLM_MODE == "api":
        return _api_reply(message_text, chat_context)

    return ""


def _mock_reply(text):
    """模拟回复：基于关键词匹配的简单规则"""
    text = text.strip()

    # 寒暄
    if any(kw in text for kw in ["早", "早安", "早上好", "morning"]):
        return "早啊"
    if any(kw in text for kw in ["晚安", "睡了", "night"]):
        return "晚安"
    if any(kw in text for kw in ["在吗", "在么", "在不在"]):
        return "在"
    if any(kw in text for kw in ["吃了吗", "吃饭没", "吃了没"]):
        return "吃了，你呢"

    # 询问状态
    if any(kw in text for kw in ["在干嘛", "干嘛呢", "做什么", "忙吗", "忙不忙"]):
        return "在忙，什么事"

    # 问好
    if text in ["hi", "hello", "嗨", "哈喽", "你好"]:
        return "嗨"

    # 感谢
    if any(kw in text for kw in ["谢谢", "多谢", "感谢", "thx"]):
        return "不客气"

    # 再见
    if any(kw in text for kw in ["再见", "拜拜", "bye", "88", "回聊"]):
        return "拜拜"

    # 问问题（关键词结尾）
    if text.endswith("？") or text.endswith("?") or text.endswith("吗"):
        return "嗯，我看看"

    # 无法判断 → 沉默
    return ""


def _api_reply(text, chat_context=None):
    """调用真实大模型 API"""
    try:
        import httpx
    except ImportError:
        print("[LLM] httpx 未安装，退回 mock 模式")
        return _mock_reply(text)

    if not LLM_API_KEY:
        print("[LLM] API Key 未配置，退回 mock 模式")
        return _mock_reply(text)

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    # 添加上下文
    if chat_context:
        for ctx in chat_context[-6:]:  # 最近6条
            role = "assistant" if ctx.get("from_bot") else "user"
            messages.append({"role": role, "content": ctx["content"]})

    # 当前消息
    messages.append({"role": "user", "content": text})

    try:
        resp = httpx.post(
            LLM_API_URL,
            headers={
                "Authorization": f"Bearer {LLM_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": LLM_MODEL,
                "messages": messages,
                "max_tokens": 80,
                "temperature": 0.7,
            },
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()
        reply = data["choices"][0]["message"]["content"].strip()
        return reply
    except Exception as e:
        print(f"[LLM] API 调用失败: {e}")
        return ""
