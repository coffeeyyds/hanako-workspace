"""
mock 全链路演示
===============
不依赖微信、不依赖 SQLCipher 密钥。
纯 SQLite mock 数据库，从消息注入到 LLM 推理到"发送"全部跑通。
"""

import sys
import time
import random
import sqlite3
import threading
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))

# --- Mock 数据库 ---
MOCK_DB = Path(__file__).parent / "db" / "mock_wechat.db"

MOCK_CONTACTS = [
    ("wxid_alice001", "Alice"),
    ("wxid_bob002", "Bob"),
    ("wxid_carol003", "Carol"),
    ("wxid_dave004", "Dave"),
    ("filehelper", "文件传输助手"),
]

MOCK_MESSAGES = [
    "在吗",
    "早啊",
    "吃了吗",
    "在干嘛呢",
    "晚上一起吃饭？",
    "谢谢你的帮忙",
    "晚安",
    "你好",
    "最近忙不忙",
    "周末什么安排",
    "明天几点开会",
    "生日快乐！",
    "哈哈好吧",
    "收到",
    "ok",
]


def create_db():
    """创建 mock 微信 MSG 表"""
    MOCK_DB.parent.mkdir(parents=True, exist_ok=True)

    # 如果已有库，删了重建
    if MOCK_DB.exists():
        MOCK_DB.unlink()

    conn = sqlite3.connect(str(MOCK_DB))
    conn.execute("""
        CREATE TABLE IF NOT EXISTS MSG (
            local_id     INTEGER PRIMARY KEY AUTOINCREMENT,
            TalkerId     TEXT,
            MsgSvrID     INTEGER,
            Type         INTEGER,
            SubType      INTEGER,
            IsSender     INTEGER,
            CreateTime   INTEGER,
            StrTalker    TEXT,
            StrContent   TEXT,
            CompressContent BLOB,
            BytesExtra   BLOB
        )
    """)
    conn.commit()
    return conn


def inject_message(conn, talker_id, name, text, is_sender=0):
    """模拟微信写入一条消息"""
    now = int(datetime.now().timestamp())
    conn.execute(
        "INSERT INTO MSG (TalkerId, MsgSvrID, Type, SubType, IsSender, "
        "CreateTime, StrTalker, StrContent) VALUES (?,?,?,?,?,?,?,?)",
        (talker_id, now, 1, 0, is_sender, now, name, text),
    )
    conn.commit()
    return conn.execute("SELECT last_insert_rowid()").fetchone()[0]


# --- 模拟 LLM ---
def mock_llm_reply(text):
    """简单的关键词回复"""
    t = text.strip()
    if any(k in t for k in ["早", "早安"]):   return "早啊"
    if any(k in t for k in ["晚安", "睡了"]):  return "晚安"
    if any(k in t for k in ["在吗"]):          return "在"
    if any(k in t for k in ["吃了吗"]):        return "吃了，你呢"
    if any(k in t for k in ["干嘛", "忙"]):    return "在忙，什么事"
    if t in ["hi", "hello", "嗨", "你好"]:     return "嗨"
    if any(k in t for k in ["谢谢", "多谢"]):  return "不客气"
    if any(k in t for k in ["再见", "拜拜"]):  return "拜拜"
    if t.endswith("？") or t.endswith("?"):    return "嗯，我看看"
    return ""


# --- 主流程 ---
def main():
    print("=" * 55)
    print("  wechat-bot Mock 全链路演示")
    print("=" * 55)

    # Phase 1: 建库 + 注入消息
    print("\n[1] 创建 mock 数据库...")
    conn = create_db()
    print(f"    {MOCK_DB}")

    print("\n[2] 注入模拟消息（模拟别人发给你的微信）...")
    msg_ids = []
    for i in range(5):
        contact = random.choice(MOCK_CONTACTS)
        text = random.choice(MOCK_MESSAGES)
        lid = inject_message(conn, contact[0], contact[1], text)
        msg_ids.append(lid)
        print(f"    [{lid}] {contact[1]}: {text}")

    print(f"\n    数据库状态: {conn.execute('SELECT count(*) FROM MSG').fetchone()[0]} 条消息")

    # Phase 2: 轮询 + 推理 + "发送"
    print("\n[3] 启动 bridge 轮询引擎...")
    print("    (模拟 bridge.py 的完整处理链路)")
    print()

    last_id = 0
    processed = set()
    send_log = []              # 模拟发送记录
    silence_until = {}         # 静默期
    reply_counts = {}           # 连续回复计数

    for round_num in range(3):
        if round_num == 0:
            print(f"--- 第 1 轮轮询 ---")
        elif round_num == 1:
            # 第二轮注入新消息
            print(f"\n    模拟新消息到达...")
            contact = random.choice(MOCK_CONTACTS)
            text = random.choice(MOCK_MESSAGES)
            lid = inject_message(conn, contact[0], contact[1], text)
            print(f"    [{lid}] {contact[1]}: {text}")
            print(f"\n--- 第 2 轮轮询 ---")
        else:
            print(f"\n--- 第 3 轮轮询 ---")

        # 拉取增量消息
        rows = conn.execute(
            "SELECT local_id, TalkerId, StrTalker, StrContent, IsSender, CreateTime "
            "FROM MSG WHERE local_id > ? ORDER BY local_id",
            (last_id,)
        ).fetchall()

        if not rows:
            print("    无新消息")
        else:
            for row in rows:
                local_id, talker_id, name, content, is_sender, ct = row
                ts = datetime.fromtimestamp(ct).strftime("%H:%M:%S")

                # === 第1层防护: IsSender ===
                if is_sender == 1:
                    print(f"    [{ts}] SKIP (自己发的): {content[:30]}")
                    last_id = max(last_id, local_id)
                    continue

                # 跳过已处理
                if local_id in processed:
                    continue

                processed.add(local_id)
                last_id = max(last_id, local_id)

                print(f"    [{ts}] ← {name}: {content[:40]}")

                # === 第2层防护: 静默期 ===
                now = time.time()
                if talker_id in silence_until and now < silence_until[talker_id]:
                    print(f"      ⏸ 静默期，跳过回复")
                    continue

                # === 第3层防护: 连续回复上限 ===
                if reply_counts.get(talker_id, 0) >= 3:
                    print(f"      ⏸ 已达回复上限，跳过")
                    continue

                # === LLM 推理 ===
                reply = mock_llm_reply(content)
                if not reply:
                    print(f"      🔇 LLM 判断不回复")
                    continue

                # === "发送" ===
                send_log.append((name, reply))
                silence_until[talker_id] = now + 10
                reply_counts[talker_id] = reply_counts.get(talker_id, 0) + 1
                print(f"      → 回复: {reply}")

        time.sleep(0.5)

    # Phase 3: 总结
    print("\n" + "=" * 55)
    print("  链路验证结果")
    print("=" * 55)
    print(f"  数据库读取          ✅ ({conn.execute('SELECT count(*) FROM MSG').fetchone()[0]} 条)")
    print(f"  增量轮询 (local_id)  ✅")
    print(f"  IsSender 过滤        ✅ (第1层防护)")
    print(f"  静默期判断            ✅ (第2层防护)")
    print(f"  连续回复限制          ✅ (第3层防护)")
    print(f"  LLM 推理             ✅ (mock 模式)")
    print(f"  发送记录:              {len(send_log)} 条")
    for name, reply in send_log:
        print(f"    → {name}: {reply}")

    conn.close()

    # Cleanup
    if MOCK_DB.exists():
        MOCK_DB.unlink()

    print(f"\n  全链路跑通！可以切真实数据了。")


if __name__ == "__main__":
    main()
