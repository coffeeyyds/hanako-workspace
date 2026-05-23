"""
bridge.py — 微信自动回复守护进程
================================
架构：
  1. 每2秒轮询 SQLCipher 加密数据库
  2. local_id 增量判断，不重不漏
  3. 解析消息体（解压），识别发送者
  4. 发 LLM 推理，生成回复
  5. GUI 自动化发送（通过 pywinauto/send_layer）
  6. 三层防护杜绝自回复

启动方式:
  python bridge.py              # 交互模式，需确认
  python bridge.py --daemon     # 守护进程模式
  python bridge.py --dry-run    # 只读不发，日志看效果
"""

import sys
import time
import json
import signal
import threading
from pathlib import Path
from datetime import datetime, timedelta

sys.path.insert(0, str(Path(__file__).parent))

from config import (
    MSG_DBS, POLL_INTERVAL_SEC, CHECKPOINT_FILE,
    SILENCE_AFTER_SEND_SEC, COOLDOWN_PER_CHAT_SEC,
    MAX_AUTO_REPLIES_PER_CHAT, MONITOR_GROUPS_ONLY,
    ENABLE_KEYWORDS, DISABLE_KEYWORDS,
)
from db_schema import WeChatDB
from mock_llm import call_llm


class AutoReplyBot:
    """微信自动回复机器人"""

    def __init__(self, key_hex, dry_run=False):
        self.db = WeChatDB(MSG_DBS, key_hex)
        self.dry_run = dry_run
        self.running = False

        # 状态追踪
        self.auto_reply_enabled = True          # 自动回复总开关
        self.last_sent_time = {}                # 每个聊天上次发消息时间 {talker_id: datetime}
        self.reply_count = {}                   # 每个聊天连续回复计数 {talker_id: int}
        self.processed_ids = set()              # 已处理的 local_id（防重）
        self.last_local_id = 0                  # 上次轮询到的 local_id
        self.checkpoint = {}                    # 检查点持久化

    def start(self):
        """启动守护进程"""
        self.db.connect()

        # 加载检查点
        self._load_checkpoint()

        # 从上次位置继续
        self.last_local_id = self.checkpoint.get("last_local_id", 0)
        # 初始化也从 DB 确认一下最大 ID
        db_max = self.db.get_last_local_id()
        if self.last_local_id < db_max - 10000:
            # 差距太大，可能数据被清理了，跳到最近
            print(f"[bridge] 检查点差距过大，跳过 {db_max - self.last_local_id} 条历史消息")
            self.last_local_id = db_max

        self.running = True
        print(f"[bridge] 启动完成，从 local_id={self.last_local_id} 开始轮询")
        print(f"[bridge] 轮询间隔: {POLL_INTERVAL_SEC}s")
        print(f"[bridge] 自动回复: {'开' if self.auto_reply_enabled else '关'}")
        print(f"[bridge] 群聊回复: {'关（只监控）' if MONITOR_GROUPS_ONLY else '开'}")
        print(f"[bridge] 模式: {'演练（不发消息）' if self.dry_run else '正式'}")
        print(f"[bridge] 按 Ctrl+C 停止\n")

        try:
            while self.running:
                self._poll_once()
                time.sleep(POLL_INTERVAL_SEC)
        except KeyboardInterrupt:
            print("\n[bridge] 收到停止信号，正在退出...")
        finally:
            self._save_checkpoint()
            self.db.close()
            print("[bridge] 已停止")

    def _poll_once(self):
        """单次轮询：从数据库拉取增量消息并处理"""
        new_msgs = self.db.fetch_new_messages(self.last_local_id)

        if not new_msgs:
            return

        for msg in new_msgs:
            local_id = msg["local_id"]

            # 跳过已处理的
            if local_id in self.processed_ids:
                continue

            # 更新追踪
            self.last_local_id = max(self.last_local_id, local_id)
            self.processed_ids.add(local_id)

            # 清理老旧的 processed_ids（保留最近 10000 条）
            if len(self.processed_ids) > 20000:
                cutoff = local_id - 10000
                self.processed_ids = {i for i in self.processed_ids if i > cutoff}

            # 处理消息
            self._handle_message(msg)

        # 每轮结束保存检查点
        if new_msgs:
            self._save_checkpoint()

    def _handle_message(self, msg):
        """处理单条消息"""
        talker_id = msg["talker_id"]
        content = msg["content"]
        is_sender = msg["is_sender"]

        # === 第1层防护: IsSender 字段 ===
        # is_sender=1 表示自己发出的消息，直接跳过
        if is_sender == 1:
            return

        # 群聊规则
        is_group = self.db.is_group_chat(talker_id)
        if is_group:
            if MONITOR_GROUPS_ONLY:
                # 只打印日志，不回复
                print(f"  [群聊] {msg['str_talker']}: {content[:40]}")
                return

        # 日志
        direction = "←" if is_sender == 0 else "→"
        chat_name = msg.get("str_talker", talker_id[:20])
        timestamp = datetime.fromtimestamp(msg.get("create_time", 0)).strftime("%H:%M:%S")
        print(f"  [{timestamp}] {direction} {chat_name}: {content[:50]}")

        # === 自然语言开关 ===
        if self._check_toggle_command(content):
            return

        if not self.auto_reply_enabled:
            return

        # === 第2层防护: 时间间隔 ===
        if talker_id in self.last_sent_time:
            elapsed = (datetime.now() - self.last_sent_time[talker_id]).total_seconds()
            if elapsed < SILENCE_AFTER_SEND_SEC:
                return  # 发完消息后的静默期内不回复
            if elapsed < COOLDOWN_PER_CHAT_SEC:
                return  # 同一聊天短时间内不重复回复

        # === 第3层防护: 回复次数限制 ===
        count = self.reply_count.get(talker_id, 0)
        if count >= MAX_AUTO_REPLIES_PER_CHAT:
            return

        # === 生成回复 ===
        reply = call_llm(content)

        # 空回复 = 不回复
        if not reply or not reply.strip():
            return

        # === 发送回复 ===
        success = self._send_reply(talker_id, reply)

        if success:
            # 更新防护状态
            self.last_sent_time[talker_id] = datetime.now()
            self.reply_count[talker_id] = count + 1

            # 定期重置回复计数（每24小时）
            if hasattr(self, "_last_reset_time"):
                if (datetime.now() - self._last_reset_time).total_seconds() > 86400:
                    self.reply_count.clear()
                    self._last_reset_time = datetime.now()
            else:
                self._last_reset_time = datetime.now()

            print(f"    → 已回复: {reply[:40]}")

    def _check_toggle_command(self, text):
        """检查是否自然语言开关指令"""
        text_lower = text.strip().lower()

        for kw in DISABLE_KEYWORDS:
            if kw in text_lower:
                if self.auto_reply_enabled:
                    self.auto_reply_enabled = False
                    print(f"  [bridge] 🔕 自动回复已关闭")
                return True

        for kw in ENABLE_KEYWORDS:
            if kw in text_lower:
                if not self.auto_reply_enabled:
                    self.auto_reply_enabled = True
                    print(f"  [bridge] 🔔 自动回复已开启")
                return True

        return False

    def _send_reply(self, talker_id, text):
        """
        发送回复。
        真实模式调用 pywinauto GUI 自动化；
        dry-run 模式只打印日志。
        """
        if self.dry_run:
            print(f"    [DRY-RUN] 发往 {talker_id}: {text}")
            return True  # 演练模式模拟发送成功

        try:
            from send_layer import send_wechat_message
            return send_wechat_message(talker_id, text)
        except ImportError:
            print(f"    [ERROR] send_layer 模块未就绪")
            return False
        except Exception as e:
            print(f"    [ERROR] 发送失败: {e}")
            return False

    def _load_checkpoint(self):
        """从文件加载检查点"""
        path = Path(CHECKPOINT_FILE)
        if path.exists():
            try:
                self.checkpoint = json.loads(path.read_text(encoding="utf-8"))
                self.last_local_id = self.checkpoint.get("last_local_id", 0)
            except Exception:
                self.checkpoint = {}
        else:
            self.checkpoint = {}

    def _save_checkpoint(self):
        """将检查点写入文件"""
        self.checkpoint["last_local_id"] = self.last_local_id
        self.checkpoint["last_update"] = datetime.now().isoformat()
        Path(CHECKPOINT_FILE).write_text(
            json.dumps(self.checkpoint, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )


def main():
    import argparse
    parser = argparse.ArgumentParser(description="微信自动回复机器人")
    parser.add_argument("--daemon", action="store_true", help="守护进程模式")
    parser.add_argument("--dry-run", action="store_true", help="演练模式（只读不发）")
    args = parser.parse_args()

    # --- 获取密钥 ---
    key_hex = None
    
    # 优先读缓存文件（save_key.bat 管理员运行后生成）
    key_file = Path(__file__).parent / "db_key.txt"
    if key_file.exists():
        key_hex = key_file.read_text().strip()
        print(f"\n✓ 从缓存读取密钥")
    
    # 回退到实时提取（需要管理员权限）
    if not key_hex:
        from extract_key import get_db_key
        key = get_db_key()
        if not key:
            print("\n✗ 无法提取微信数据库密钥")
            print("请右键 save_key.bat → 以管理员身份运行，然后再启动 bridge")
            sys.exit(1)
        key_hex = key.hex()
        print(f"\n✓ 密钥提取成功")
    
    # --- 启动 ---
    bot = AutoReplyBot(key_hex, dry_run=args.dry_run)

    if not args.daemon:
        print(f"\n{'='*50}")
        print("即将启动微信自动回复机器人")
        print(f"模式: {'演练（不发消息）' if args.dry_run else '正式'}")
        print("请确保微信客户端已打开并处于前台")
        print(f"{'='*50}")
        resp = input("\n按 Enter 启动，输入 q 退出: ")
        if resp.lower() == "q":
            print("已取消")
            sys.exit(0)

    bot.start()


if __name__ == "__main__":
    main()
