@echo off
cd /d D:\Hanako\wechat-bot
echo === Save WeChat DB Key ===
echo.
C:\Python314\python.exe -c "from extract_key import get_db_key; k = get_db_key(); open('db_key.txt','w').write(k.hex()) if k else exit(1); print('KEY SAVED:', k.hex()[:16]+'...')"
if %errorlevel% equ 0 (
    echo.
    echo Key saved to db_key.txt
) else (
    echo.
    echo Failed to extract key
)
pause
