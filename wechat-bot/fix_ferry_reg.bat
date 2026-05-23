@echo off
echo === Fix WeChatFerry: Add registry path ===
echo.
echo Adding WeChat install path to registry for WeChatFerry...
REG ADD "HKCU\Software\Tencent\WeChat" /v InstallPath /t REG_SZ /d "D:\WeChat\Weixin" /f
echo.
echo Verifying...
REG QUERY "HKCU\Software\Tencent\WeChat" /v InstallPath
echo.
echo Done! Now try running WeChatFerry again.
pause
