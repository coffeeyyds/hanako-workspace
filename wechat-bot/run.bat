@echo off
chcp 65001 >nul
title wechat-bot 微信自动回复

echo ============================================
echo   wechat-bot 微信自动回复机器人
echo ============================================
echo.
echo 请选择模式:
echo   [1] 演练模式 - 只读取消息，不发送回复
echo   [2] 正式模式 - 自动回复消息
echo   [3] 模拟测试 - 用 mock 消息测试链路
echo   [0] 退出
echo.
set /p mode="请输入选项 [1/2/3/0]: "

if "%mode%"=="1" (
    echo.
    echo 启动演练模式...
    python bridge.py --dry-run
)

if "%mode%"=="2" (
    echo.
    echo 启动正式模式...
    echo ⚠ 注意：将自动回复微信消息！
    set /p confirm="确认启动？[y/n]: "
    if /i "%confirm%"=="y" (
        python bridge.py
    ) else (
        echo 已取消
    )
)

if "%mode%"=="3" (
    echo.
    echo 启动模拟测试...
    start "wechat-bot-sim" cmd /c "python simulate_message.py --loop"
    timeout /t 2 >nul
    python bridge.py --dry-run
    taskkill /fi "WINDOWTITLE eq wechat-bot-sim*" >nul 2>&1
)

if "%mode%"=="0" (
    exit /b 0
)

pause
