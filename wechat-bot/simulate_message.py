"""
消息注入模拟器
==============
用于在没有真实微信消息的情况下测试 bridge.py 的完整链路。

它创建一个独立的 SQLite mock 数据库（与微信 MSG 表结构一致），
往里面插入模拟消息，然后 bridge.py 会发现并处理它们。

用法:
  python simulate_message.py              # 注入一条测试消息
  python simulate_message.py --loop        # 每10秒注入一条随机消息
  python simulate_message.py --chat "filehelper" --text "你好"  # 指定内容和对象
"""

import sys
import time
import random
import sqlite3
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))

# Mock 数据库路径
MOCK_DB = Path(__file__).parent / "db" / "mock_wechat.db"

# 模拟联系人
MOCK_CONTACTS = [
    ("wxid_alice001", "Alice", "Alice"),
    ("wxid_bob002", "Bob", "Bob"),
    ("wxid_carol003", "Carol", "Carol"),
    ("wxid_dave004", "Dave", "Dave"),
    ("filehelper", "文件传输助手", "filehelper"),
]

# 模拟消息模板（对方可能发来的）
MOCK_MESSAGES = [
    "在吗",
    "早啊",
    "吃了吗",
    "今天有空吗",
    "在干嘛呢",
    "晚上一起吃饭？",
    "谢谢你的帮忙",
    "晚安",
    "你好",
    "周末什么安排",
    "最近忙不忙",
    "看到个好玩的发你",
    "这个文件你收到了吗",
    "明天几点开会",
    "生日快乐！",
]


def create_mock_db():
    """创建 mock 微信数据库，schema 与真实 MSG 表一致"""
    MOCK_DB.parent.mkdir(parents=True, exist_ok=True)

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
            Sequence     INTEGER,
            StatusEx     INTEGER,
            FlagEx       INTEGER,
            Status       INTEGER,
            MsgServerSeq INTEGER,
            MsgSequence  INTEGER,
            StrTalker    TEXT,
            StrContent   TEXT,
            DisplayContent TEXT,
            CompressContent BLOB,
            BytesExtra   BLOB
        )
    """)
    conn.commit()
    return conn


def insert_message(conn, talker_id, str_talker, content, is_sender=0):
    """插入一条模拟消息"""
    now = int(datetime.now().timestamp())
    conn.execute(
        """INSERT INTO MSG
           (TalkerId, MsgSvrID, Type, SubType, IsSender,
            CreateTime, StrTalker, StrContent)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (talker_id, now, 1, 0, is_sender, now, str_talker, content),
    )
    conn.commit()
    local_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    print(f"  → 注入 MSG local_id={local_id}: [{str_talker}] {content}")
    return local_id


def main():
    import argparse
    parser = argparse.ArgumentParser(description="微信消息注入模拟器")
    parser.add_argument("--loop", action="store_true", help="循环注入模式")
    parser.add_argument("--chat", type=str, default=None, help="指定聊天对象")
    parser.add_argument("--text", type=str, default=None, help="指定消息内容")
    args = parser.parse_args()

    print("=== 微信消息注入模拟器 ===\n")
    print(f"Mock 数据库: {MOCK_DB}")

    conn = create_mock_db()

    if args.loop:
        print("\n循环注入模式，每 8-15 秒注入一条随机消息")
        print("按 Ctrl+C 停止\n")
        try:
            while True:
                contact = random.choice(MOCK_CONTACTS)
                msg = random.choice(MOCK_MESSAGES)
                insert_message(conn, contact[0], contact[1], msg)
                wait = random.randint(8, 15)
                time.sleep(wait)
        except KeyboardInterrupt:
            print("\n已停止")
    else:
        if args.chat and args.text:
            # 指定消息
            contact = next((c for c in MOCK_CONTACTS if c[0] == args.chat), None)
            if not contact:
                contact = (args.chat, args.chat, args.chat)
            insert_message(conn, contact[0], contact[1], args.text)
        else:
            # 默认：注入几条不同联系人的消息
            print("\n注入测试消息:\n")
            for i, (wxid, name, _) in enumerate(MOCK_CONTACTS[:3]):
                msg = MOCK_MESSAGES[i % len(MOCK_MESSAGES)]
                insert_message(conn, wxid, name, msg)

    conn.close()
    print("\n完成")


if __name__ == "__main__":
    main()
