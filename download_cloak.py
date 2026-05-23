"""手动下载 CloakBrowser 二进制文件（200MB+，需要较长时间）"""
import os
import sys
import zipfile
import shutil
import tempfile
from pathlib import Path
import httpx

# 配置
VERSION = "146.0.7680.177.5"
PLATFORM_TAG = "windows-x64"
ARCHIVE_NAME = f"cloakbrowser-{PLATFORM_TAG}.zip"
CACHE_DIR = Path.home() / ".cloakbrowser"
BINARY_DIR = CACHE_DIR / f"chromium-{VERSION}"
BINARY_PATH = BINARY_DIR / "chrome.exe"

# 下载源（优先 GitHub Releases）
DOWNLOADS = [
    f"https://cloakbrowser.dev/chromium-v{VERSION}/{ARCHIVE_NAME}",
    f"https://github.com/CloakHQ/cloakbrowser/releases/download/chromium-v{VERSION}/{ARCHIVE_NAME}",
]

# 超长超时（10 分钟连接 + 30 分钟读取，200MB 文件）
TIMEOUT = httpx.Timeout(connect=30.0, read=1800.0, write=30.0, pool=30.0)

def download_file(url, dest):
    """带进度条的下载"""
    print(f"尝试下载: {url}")
    with httpx.stream("GET", url, follow_redirects=True, timeout=TIMEOUT) as resp:
        resp.raise_for_status()
        total = int(resp.headers.get("content-length", 0))
        downloaded = 0
        with open(dest, "wb") as f:
            for chunk in resp.iter_bytes(chunk_size=65536):
                f.write(chunk)
                downloaded += len(chunk)
                if total > 0:
                    pct = downloaded / total * 100
                    mb_done = downloaded / (1024 * 1024)
                    mb_total = total / (1024 * 1024)
                    sys.stdout.write(f"\r  进度: {pct:.0f}% ({mb_done:.0f}/{mb_total:.0f} MB)")
                    sys.stdout.flush()
        print()
    print(f"下载完成: {dest.stat().st_size // (1024*1024)} MB")

def main():
    # 检查是否已存在
    if BINARY_PATH.exists():
        print(f"✓ 二进制已存在: {BINARY_PATH}")
        print(f"  大小: {BINARY_PATH.stat().st_size // (1024*1024)} MB")
        return

    print(f"目标: {BINARY_PATH}")
    print(f"缓存目录: {CACHE_DIR}")
    print()

    # 准备缓存目录
    BINARY_DIR.parent.mkdir(parents=True, exist_ok=True)

    # 清理旧的不完整下载
    if BINARY_DIR.exists():
        print("清理旧的缓存目录...")
        shutil.rmtree(BINARY_DIR)

    # 尝试下载
    tmp = tempfile.NamedTemporaryFile(suffix=".zip", delete=False)
    tmp_path = Path(tmp.name)
    tmp.close()

    try:
        for url in DOWNLOADS:
            try:
                download_file(url, tmp_path)
                break
            except Exception as e:
                print(f"  失败: {e}")
                # 重新创建临时文件
                tmp_path.unlink(missing_ok=True)
                tmp = tempfile.NamedTemporaryFile(suffix=".zip", delete=False)
                tmp_path = Path(tmp.name)
                tmp.close()
        else:
            print("\n所有下载源均失败。")
            print("可以手动下载后设置环境变量:")
            print(f"  CLOAKBROWSER_BINARY_PATH=<你的 chrome.exe 路径>")
            return

        # 解压
        print(f"\n正在解压到 {BINARY_DIR}...")
        BINARY_DIR.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(tmp_path, "r") as zf:
            zf.extractall(BINARY_DIR)
        print("解压完成")

        if BINARY_PATH.exists():
            print(f"\n✓ 安装成功!")
            print(f"  路径: {BINARY_PATH}")
            print(f"  大小: {BINARY_PATH.stat().st_size // (1024*1024)} MB")
        else:
            print(f"\n⚠ 解压后未找到 chrome.exe")
            print(f"  目录内容: {list(BINARY_DIR.iterdir())[:10]}")

    finally:
        tmp_path.unlink(missing_ok=True)

if __name__ == "__main__":
    main()
