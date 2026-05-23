@echo off
chcp 65001 >nul
echo =========================================
echo   wechat-bot 依赖安装
echo =========================================
echo.

:: 检查 Python
echo [1/4] 检查 Python...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ✗ 未找到 Python，请先安装 Python 3.10+
    echo   下载地址: https://www.python.org/downloads/
    pause
    exit /b 1
)
python --version
echo ✓ Python 就绪
echo.

:: 升级 pip
echo [2/4] 升级 pip...
python -m pip install --upgrade pip --quiet
echo.
echo [3/4] 安装核心依赖...
pip install pymem --quiet
pip install httpx --quiet
pip install pyperclip --quiet
echo.

:: pysqlcipher3 需要编译工具，试试预编译版本
echo [4/4] 安装 pysqlcipher3...
echo   注意: pysqlcipher3 可能需要 Visual C++ Build Tools
echo   如果安装失败，可以尝试:
echo     pip install pysqlcipher3-binary
echo   或从 https://github.com/rigglemania/pysqlcipher3 获取
pip install pysqlcipher3 --quiet 2>&1
if %errorlevel% neq 0 (
    echo   pysqlcipher3 安装失败，尝试二进制版本...
    pip install pysqlcipher3-binary --quiet 2>&1
)

:: pywinauto (发送层)
echo   安装 pywinauto...
pip install pywinauto --quiet

echo.
echo =========================================
echo   安装完成！
echo =========================================
echo.
echo 使用方法:
echo   1. 确保微信已登录并打开
echo   2. python bridge.py --dry-run    （演练模式，只读不发）
echo   3. python bridge.py              （正式模式）
echo   4. python simulate_message.py    （注入模拟消息测试）
echo.
pause
