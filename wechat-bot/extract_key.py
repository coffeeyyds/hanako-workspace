"""
SQLCipher 密钥提取模块 v3 — WeChat 4.x 专用
===========================================
微信 4.x 改变了密钥存储方式，不能用简单的 hex 扫描。
这个版本用增强策略：

  1. 全进程堆扫描 — 不只 WeChatWin.dll，扫整个进程空间
  2. 二进制模式匹配 — 不找 hex 字符串，找 32 字节随机二进制密钥  
  3. 子进程检查 — WeChat 4.x 可能把密钥放在子进程
  4. 直接用 sqlcipher3 库测试 — 更轻量
"""

import sys
import os
import re
import hashlib
import struct
import binascii
from pathlib import Path
from collections import Counter

sys.path.insert(0, str(Path(__file__).parent))
from config import MSG_DBS, MICROMSG_DB


def _is_likely_key(data):
    """判断 32 字节数据是否像随机密钥"""
    if len(data) != 32:
        return False
    # 不能是全0、全F、全相同字节
    if data == b'\x00' * 32:
        return False
    if data == b'\xFF' * 32:
        return False
    if len(set(data)) < 4:  # 太单调
        return False
    # 检查字节分布：真正的随机密钥应该有较好的熵
    counter = Counter(data)
    most_common = counter.most_common(1)[0][1]
    if most_common > 16:  # 同一字节出现超过一半，不太可能是密钥
        return False
    return True


def _extract_via_binary_scan(pm):
    """
    改进的内存扫描：搜索 32 字节的二进制密钥候选。
    
    微信 4.x 的密钥可能不是以 hex 字符串形式存储，
    而是以原始二进制（32 bytes）形式存储在进程内存中。
    
    策略：
    1. 扫描所有可读内存区域
    2. 对每个区域，滑动窗口取 32 字节
    3. 用熵检测过滤明显不是密钥的数据
    4. 用 sqlcipher3 库验证候选密钥
    """
    if pm is None:
        return None

    print("[extract_key] 增强二进制扫描...")
    print(f"  进程 PID: {pm.process_id}")

    # 也检查子进程
    import psutil
    try:
        parent = psutil.Process(pm.process_id)
        children = parent.children(recursive=True)
        if children:
            print(f"  发现 {len(children)} 个子进程: {[c.name() for c in children]}")
    except Exception:
        children = []

    candidates = set()

    # 先在主进程扫描
    try:
        regions = list(pm.list_memory_regions())
    except Exception:
        print("  无法枚举内存区域")
        return None

    total_regions = len(regions)
    scanned = 0
    checked_keys = 0

    for region in regions:
        scanned += 1
        if scanned % 500 == 0:
            print(f"  扫描进度: {scanned}/{total_regions} 区域, "
                  f"已检查 {checked_keys} 个密钥候选")

        # 跳过不合适的区域
        if region.size < 32 or region.size > 500 * 1024 * 1024:
            continue
        # 跳过只执行区域
        if not hasattr(region, 'protect'):
            continue

        try:
            # 只读小样本 (前1MB) 来测试
            chunk = pm.read_bytes(
                region.BaseAddress, 
                min(region.size, 1 * 1024 * 1024)
            )
        except Exception:
            continue

        # 滑动窗口扫描 32 字节
        for offset in range(0, len(chunk) - 31, 8):  # 步长8加速
            candidate = chunk[offset:offset + 32]
            if _is_likely_key(candidate):
                if candidate not in candidates:
                    candidates.add(candidate)
                    checked_keys += 1
                    
                    # 每找到 10 个候选就测试一批
                    if checked_keys % 10 == 0 and len(candidates) >= 10:
                        result = _test_candidates(candidates)
                        if result:
                            return result

        if len(candidates) > 200:
            break

    print(f"  扫描完成: {scanned} 区域, {len(candidates)} 候选密钥")

    # 最终批量测试
    result = _test_candidates(candidates)
    if result:
        return result

    # 也试子进程
    for child in children:
        try:
            child_pm = __import__('pymem').Pymem(child.pid)
            print(f"  检查子进程: {child.name()} (PID={child.pid})")
            regions = list(child_pm.list_memory_regions())
            for region in regions:
                if region.size < 32 or region.size > 200 * 1024 * 1024:
                    continue
                try:
                    chunk = child_pm.read_bytes(
                        region.BaseAddress,
                        min(region.size, 1 * 1024 * 1024)
                    )
                except Exception:
                    continue
                for offset in range(0, len(chunk) - 31, 8):
                    candidate = chunk[offset:offset + 32]
                    if _is_likely_key(candidate) and candidate not in candidates:
                        candidates.add(candidate)
                        if len(candidates) % 10 == 0:
                            result = _test_candidates(candidates)
                            if result:
                                return result
        except Exception:
            continue

    return _test_candidates(candidates)


def _extract_via_dbpath_enhanced(pm):
    """
    增强的数据库路径邻近搜索。
    
    不是只找 WeChatWin.dll，而是在整个进程空间搜索
    数据库文件路径字符串，然后在附近找密钥。
    """
    if pm is None:
        return None

    print("[extract_key] 数据库路径增强搜索...")

    target_paths = [
        b"MSG0.db",
        b"MicroMsg.db", 
        b"ChatMsg.db",
        # 完整路径片段
        b"WeChat Files",
        b"Msg\\Multi",
        # Unicode 编码
        "MSG0.db".encode("utf-16-le"),
        "MicroMsg.db".encode("utf-16-le"),
    ]

    try:
        regions = list(pm.list_memory_regions())
    except Exception:
        return None

    for target in target_paths:
        for region in regions:
            if region.size < 64 or region.size > 100 * 1024 * 1024:
                continue
            try:
                chunk = pm.read_bytes(
                    region.BaseAddress,
                    min(region.size, 5 * 1024 * 1024)
                )
            except Exception:
                continue

            idx = 0
            while True:
                idx = chunk.find(target, idx)
                if idx == -1:
                    break

                # 在前后 16KB 范围内找密钥
                search_start = max(0, idx - 16384)
                search_end = min(len(chunk), idx + 16384)
                window = chunk[search_start:search_end]

                # 找 32 字节可能的密钥
                for off in range(0, len(window) - 31, 1):
                    candidate = window[off:off + 32]
                    if _is_likely_key(candidate):
                        if _test_key(MSG_DBS[0], candidate):
                            abs_addr = region.BaseAddress + search_start + off
                            print(f"  ✓ 密钥找到！地址={hex(abs_addr)}, "
                                  f"邻近字符串={target}")
                            return candidate

                idx += len(target)

    return None


def _extract_via_wechat_child(pm):
    """方案3: 在微信子进程中搜索"""
    print("[extract_key] 方案3: 子进程搜索...")
    
    import psutil
    try:
        parent = psutil.Process(pm.process_id)
        children = parent.children(recursive=True)
    except Exception as e:
        print(f"  无法枚举子进程: {e}")
        return None

    if not children:
        print("  未发现子进程")
        return None

    import pymem
    for child in children:
        name = child.name()
        print(f"  检查: {name} (PID={child.pid})")
        try:
            child_pm = pymem.Pymem(child.pid)
        except Exception:
            continue

        # 在这个子进程中搜索
        result = _extract_via_dbpath_enhanced(child_pm)
        if result:
            return result

        result = _extract_via_binary_scan(child_pm)
        if result:
            return result

    return None


def _test_candidates(candidates, max_test=50):
    """批量测试候选密钥"""
    if not candidates:
        return None

    test_db = MSG_DBS[0]
    candidates_list = list(candidates)[:max_test]

    for i, key in enumerate(candidates_list):
        if _test_key(test_db, key):
            print(f"  ✓ 密钥验证成功！")
            return key

    return None


def _test_key(db_path, key_bytes):
    """用 sqlcipher3 测试密钥"""
    try:
        from sqlcipher3 import dbapi2 as sqlcipher
    except ImportError:
        try:
            from pysqlcipher3 import dbapi2 as sqlcipher
        except ImportError:
            # 两个都没有，跳过  
            return False

    if not Path(db_path).exists():
        return False

    try:
        conn = sqlcipher.connect(str(db_path))
        c = conn.cursor()
        
        key_hex = key_bytes.hex() if isinstance(key_bytes, bytes) else str(key_bytes)
        c.execute(f"PRAGMA key = \"x'{key_hex}'\"")

        # 快速测试
        c.execute("SELECT count(*) FROM sqlite_master")
        c.fetchone()
        conn.close()
        return True
    except Exception:
        return False


def get_db_key():
    """主入口"""
    print("=" * 50)
    print("[extract_key v3] 开始提取微信 SQLCipher 密钥")
    print("  目标: WeChat 4.x on Windows")

    # 获取微信进程
    try:
        import pymem
        pm = pymem.Pymem("Weixin.exe")
        print(f"\n  主进程: Weixin.exe (PID={pm.process_id})")
    except Exception:
        try:
            pm = pymem.Pymem("WeChat.exe")
        except Exception:
            print("  未找到微信进程")
            pm = None

    if pm is None:
        print("\n请确保微信已登录运行")
        return None

    # 确保 psutil 可用
    try:
        import psutil
    except ImportError:
        print("  正在安装 psutil...")
        os.system(f"{sys.executable} -m pip install psutil --quiet")

    # 方案1: 数据库路径增强搜索（最快）
    print("\n[1/3] 数据库路径邻近搜索...")
    key = _extract_via_dbpath_enhanced(pm)
    if key:
        return key

    # 方案2: 全进程二进制扫描
    print("\n[2/3] 全进程二进制密钥扫描...")
    key = _extract_via_binary_scan(pm)
    if key:
        return key

    # 方案3: 子进程检查
    print("\n[3/3] 子进程搜索...")
    key = _extract_via_wechat_child(pm)
    if key:
        return key

    print("\n[extract_key] ✗ 所有方案均失败")
    print("\n微信 4.x 的密钥存储方式发生了较大变化。")
    print("推荐使用以下工具获取密钥：")
    print("  1. WeChatMsg (留痕) GUI: https://github.com/LC044/WeChatMsg/releases")
    print("  2. WeChatFerry (DLL注入): https://github.com/lich0821/WeChatFerry")
    print("\n这些工具都已经适配了微信 4.x 版本。")
    return None


if __name__ == "__main__":
    key = get_db_key()
    if key:
        print(f"\n{'='*50}")
        print(f"密钥 (hex): {key.hex()}")
        print(f"密钥长度: {len(key)} 字节")
        print(f"{'='*50}")
    else:
        sys.exit(1)
