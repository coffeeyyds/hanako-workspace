@echo off
cd /d D:\Hanako\wechat-bot
echo === Running enhanced key extraction v3 ===
echo.
echo Step 1: Ensure psutil is installed...
C:\Python314\python.exe -m pip install psutil --quiet 2>&1
echo.
echo Step 2: Extract key...
echo.
C:\Python314\python.exe extract_key.py 2>&1
echo.
pause
