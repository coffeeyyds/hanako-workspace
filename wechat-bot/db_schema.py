"""
微信消息数据库读取层
==================
封装 SQLCipher 数据库连接、消息体解压、增量查询。

MSG 表核心字段（微信 Windows 版）:
  local_id         INTEGER PRIMARY KEY AUTOINCREMENT  自增ID，轮询锚点
  TalkerId         TEXT                                聊天对象 wxid（发送者或群ID）
  MsgSvrID         INTEGER                             服务端消息ID
  Type             INTEGER                             消息类型（1=文本, 3=图片, 34=语音, 47=表情...）
  SubType          INTEGER                             子类型
  IsSender         INTEGER                             0=收到, 1=发出
  CreateTime       INTEGER                             Unix时间戳
  Sequence         INTEGER                             消息序号
  StrTalker        TEXT                                聊天对象显示名
  StrContent       TEXT                                消息文本内容
  CompressContent  BLOB                                压缩的消息体
  BytesExtra       BLOB                                额外数据（含发送者信息等）
"""

import zlib
import struct
import re
from pathlib import Path
# 优先用 sqlcipher3，回退到 pysqlcipher3
try:
    from sqlcipher3 import dbapi2 as sqlcipher
except ImportError:
    from pysqlcipher3 import dbapi2 as sqlcipher


class WeChatDB:
    """微信消息数据库操作封装"""

    def __init__(self, db_paths, key_hex):
        """
        db_paths: MSG*.db 文件路径列表
        key_hex: 十六进制密钥字符串（64字符）
        """
        self.db_paths = [Path(p) for p in db_paths]
        self.key_hex = key_hex
        self.connections = {}

    def connect(self):
        """建立所有分片数据库的连接"""
        for db_path in self.db_paths:
            if not db_path.exists():
                continue

            db_name = db_path.stem  # MSG0, MSG1, ...

            # 复制一份到临时文件，避免和微信主进程抢锁
            # （对于只读查询，PRAGMA query_only 也可以，但复制更安全）
            tmp_path = db_path.parent / f"_tmp_{db_name}.db"

            # 如果已有临时文件且源文件更新了，重新复制
            do_copy = True
            if tmp_path.exists():
                if tmp_path.stat().st_mtime >= db_path.stat().st_mtime:
                    do_copy = False

            if do_copy:
                import shutil
                shutil.copy2(db_path, tmp_path)

            conn = sqlcipher.connect(str(tmp_path))
            conn.execute(f"PRAGMA key = \"x'{self.key_hex}'\"")
            conn.execute("PRAGMA cipher_compatibility = 3")

            # 验证连接
            try:
                conn.execute("SELECT count(*) FROM MSG")
            except Exception as e:
                print(f"[DB] 无法解密 {db_name}: {e}")
                conn.close()
                continue

            self.connections[db_name] = conn
            print(f"[DB] ✓ {db_name} 连接成功")

        if not self.connections:
            raise RuntimeError("无法连接任何消息数据库，密钥可能错误")

    def get_last_local_id(self):
        """获取所有分片中最大的 local_id"""
        max_id = 0
        for conn in self.connections.values():
            try:
                row = conn.execute("SELECT MAX(local_id) FROM MSG").fetchone()
                if row and row[0]:
                    max_id = max(max_id, row[0])
            except Exception:
                pass
        return max_id

    def fetch_new_messages(self, since_local_id, limit=200):
        """
        获取所有分片中 local_id > since_local_id 的消息。
        返回按 local_id 排序的消息列表。
        """
        all_msgs = []

        for db_name, conn in self.connections.items():
            try:
                rows = conn.execute(
                    "SELECT local_id, TalkerId, MsgSvrID, Type, SubType, "
                    "IsSender, CreateTime, StrTalker, StrContent, "
                    "CompressContent, BytesExtra "
                    "FROM MSG WHERE local_id > ? "
                    "ORDER BY local_id ASC LIMIT ?",
                    (since_local_id, limit)
                ).fetchall()
            except Exception as e:
                print(f"[DB] 查询 {db_name} 失败: {e}")
                continue

            for row in rows:
                msg = self._parse_row(row)
                if msg:
                    all_msgs.append(msg)

        # 跨分片全局排序
        all_msgs.sort(key=lambda m: m["local_id"])
        return all_msgs

    def _parse_row(self, row):
        """解析一行 MSG 记录，提取明文消息体"""
        local_id, talker_id, svr_id, msg_type, sub_type, \
            is_sender, create_time, str_talker, str_content, \
            compress_content, bytes_extra = row

        # 只处理文本消息
        content = ""

        # 1. 优先用 StrContent（纯文本消息）
        if str_content:
            content = str_content

        # 2. 如果 CompressContent 有数据，解压
        if compress_content and not content:
            content = self._decompress(compress_content)

        # 3. 如果都没有，跳过
        if not content:
            return None

        return {
            "local_id": local_id,
            "talker_id": talker_id,         # 发送者的 wxid
            "msg_svr_id": svr_id,
            "type": msg_type,
            "sub_type": sub_type,
            "is_sender": is_sender,         # 0=收到, 1=发出
            "create_time": create_time,
            "str_talker": str_talker,       # 聊天对象备注/昵称
            "content": content,             # 明文消息体
        }

    @staticmethod
    def _decompress(data):
        """解压微信压缩消息体"""
        if not data:
            return ""
        try:
            # 微信使用 zlib 压缩（可能带自定义头部）
            # 尝试纯 zlib 解压
            return zlib.decompress(data).decode("utf-8", errors="replace")
        except zlib.error:
            try:
                # 尝试跳过头部（某些版本有2字节头部）
                return zlib.decompress(data[2:]).decode("utf-8", errors="replace")
            except Exception:
                pass
        except Exception:
            pass
        return ""

    def is_group_chat(self, talker_id):
        """判断一个 talker_id 是否是群聊"""
        # 微信群的 talker_id 以 @chatroom 结尾
        if not talker_id:
            return False
        return talker_id.endswith("@chatroom") or "@chatroom" in talker_id

    def close(self):
        """关闭所有数据库连接，清理临时文件"""
        for db_name, conn in self.connections.items():
            try:
                conn.close()
            except Exception:
                pass

            # 清理临时文件
            for db_path in self.db_paths:
                tmp = db_path.parent / f"_tmp_{db_path.stem}.db"
                if tmp.exists():
                    try:
                        tmp.unlink()
                    except Exception:
                        pass

        self.connections.clear()


# --- 独立测试 ---
if __name__ == "__main__":
    from config import MSG_DBS
    from extract_key import get_db_key

    print("=== 微信消息数据库测试 ===\n")

    # 1. 提取密钥
    key = get_db_key()
    if not key:
        print("密钥提取失败，无法继续")
        exit(1)

    key_hex = key.hex()
    print(f"密钥: {key_hex}\n")

    # 2. 连接数据库
    db = WeChatDB(MSG_DBS, key_hex)
    db.connect()

    # 3. 查看统计
    total = db.get_last_local_id()
    print(f"\n总消息数: {total}")

    # 4. 读取最新 10 条
    recent = db.fetch_new_messages(max(0, total - 10))
    print(f"\n最新 {len(recent)} 条消息:")
    for msg in recent:
        direction = "←" if msg["is_sender"] == 0 else "→"
        print(f"  [{msg['local_id']}] {direction} {msg['str_talker']}: {msg['content'][:60]}")

    db.close()
