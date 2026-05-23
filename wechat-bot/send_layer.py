"""
Windows 微信 GUI 自动化发送层
===========================
替代 Mac 版 AppleScript，用 pywinauto 驱动微信客户端发送消息。

发送流程:
  1. 激活微信窗口
  2. Ctrl+F 打开搜索
  3. 输入联系人备注名搜索
  4. 回车进入聊天
  5. Ctrl+V 粘贴回复文本
  6. 回车发送

注意事项:
  - 微信窗口必须可见（不能最小化）
  - 联系人搜索依赖备注名精确匹配
  - 微信 UI 用 Duilib 自绘，不能用标准控件定位，走快捷键链
"""

import time
import pyperclip

# 尝试导入 pywinauto
try:
    from pywinauto.application import Application
    from pywinauto.keyboard import send_keys
    PYWIINAUTO_AVAILABLE = True
except ImportError:
    PYWIINAUTO_AVAILABLE = False
    print("[send_layer] pywinauto 未安装，发送功能不可用")
    print("[send_layer] 请运行: pip install pywinauto pyperclip")


def send_wechat_message(talker_id, text):
    """
    通过 GUI 自动化发送微信消息。

    Args:
        talker_id: 接收者的 wxid（如 wxid_xxx）
        text: 要发送的文本

    Returns:
        bool: 是否发送成功
    """
    if not PYWIINAUTO_AVAILABLE:
        print("[send_layer] ✗ pywinauto 不可用")
        return False

    # 将文本复制到剪贴板
    try:
        pyperclip.copy(text)
    except Exception as e:
        print(f"[send_layer] 剪贴板复制失败: {e}")
        return False

    try:
        # 方案A: 尝试用 pywinauto UIA backend
        app = Application(backend="uia").connect(
            title_re=".*微信.*", timeout=5
        )
        win = app.top_window()
        win.set_focus()
        time.sleep(0.3)

        # Ctrl+F 打开微信搜索
        send_keys("^f")
        time.sleep(0.4)

        # 输入联系人备注名搜索
        # 注意：这里需要的是一个可搜索的备注名或昵称
        send_keys(talker_id)
        time.sleep(0.4)

        # 回车选中第一个搜索结果
        send_keys("{ENTER}")
        time.sleep(0.3)

        # Ctrl+V 粘贴文本
        send_keys("^v")
        time.sleep(0.2)

        # 回车发送
        send_keys("{ENTER}")

        return True

    except Exception as e:
        print(f"[send_layer] UIA 方案失败: {e}")

    try:
        # 方案B: 用 win32 backend
        app = Application(backend="win32").connect(
            title_re=".*微信.*", timeout=5
        )
        win = app.top_window()
        win.set_focus()
        time.sleep(0.3)

        send_keys("^f")
        time.sleep(0.4)
        send_keys(talker_id)
        time.sleep(0.4)
        send_keys("{ENTER}")
        time.sleep(0.3)
        send_keys("^v")
        time.sleep(0.2)
        send_keys("{ENTER}")

        return True

    except Exception as e:
        print(f"[send_layer] Win32 方案也失败: {e}")
        return False


def get_wechat_contacts():
    """
    获取微信联系人列表（用于备注名到 wxid 的映射）。
    这是发送层的一个辅助功能，实际使用时可以从数据库的
    MicroMsg.db 中读取 Contact 表来获取映射。
    """
    # TODO: 从 MicroMsg.db 的 Contact 表读取联系人映射
    pass


# --- 独立测试 ---
if __name__ == "__main__":
    print("=== 发送层测试 ===\n")
    print("将发送一条测试消息到「文件传输助手」")

    test_text = "这是一条来自 bridge.py 的测试消息"
    success = send_wechat_message("filehelper", test_text)

    if success:
        print("✓ 发送成功")
    else:
        print("✗ 发送失败")
