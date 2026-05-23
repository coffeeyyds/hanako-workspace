@echo off
cd /d D:\Hanako\wechat-bot
echo === Plan B: Install WeChatFerry ===
echo.
echo WeChatFerry uses DLL injection (no memory scanning needed)
echo It can read AND send messages directly.
echo.
echo Installing wcferry...
C:\Python314\python.exe -m pip install wcferry --quiet 2>&1
echo.
echo Testing import...
C:\Python314\python.exe -c "from wcferry import Wcf; print('WeChatFerry OK'); wcf=Wcf(); print('WCF client created')" 2>&1
echo.
echo === Done ===
pause
