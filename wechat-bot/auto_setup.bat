@echo off
cd /d D:\Hanako\wechat-bot
echo === wechat-bot auto-setup ===
echo.
echo [1] Checking Python...
C:\Python314\python.exe --version
if %errorlevel% neq 0 (
    echo ERROR: Python not found at C:\Python314
    exit /b 1
)
echo.
echo [2] Installing dependencies...
C:\Python314\python.exe -m pip install --upgrade pip --quiet
C:\Python314\python.exe -m pip install httpx pyperclip pywinauto pymem --quiet
echo.
echo [3] Installing pysqlcipher3...
C:\Python314\python.exe -m pip install pysqlcipher3 --quiet 2>&1
if %errorlevel% neq 0 (
    echo pysqlcipher3 failed, trying binary...
    C:\Python314\python.exe -m pip install pysqlcipher3-binary --quiet 2>&1
)
echo.
echo [4] Verifying installs...
C:\Python314\python.exe -c "import httpx; print('httpx OK')"
C:\Python314\python.exe -c "import pyperclip; print('pyperclip OK')"
C:\Python314\python.exe -c "import pymem; print('pymem OK')"
C:\Python314\python.exe -c "import pywinauto; print('pywinauto OK')"
echo.
echo [5] Extracting WeChat key...
C:\Python314\python.exe extract_key.py
echo.
echo === Setup complete ===
pause
