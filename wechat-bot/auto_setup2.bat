@echo off
cd /d D:\Hanako\wechat-bot
echo === wechat-bot setup v2 ===
echo.
echo [1] Trying alternative SQLCipher packages...
echo.

:: Try sqlcipher3 (different package name)
C:\Python314\python.exe -m pip install sqlcipher3 --quiet 2>&1
if %errorlevel% equ 0 (
    echo sqlcipher3 installed OK
    goto :check
)

:: Try older pysqlcipher3 from GitHub
echo Trying pysqlcipher3 from git...
C:\Python314\python.exe -m pip install git+https://github.com/rigglemania/pysqlcipher3.git --quiet 2>&1

:: Try sqlite3 with built-in sqlcipher (sqlcipher3)
echo Trying standalone sqlcipher...
C:\Python314\python.exe -m pip install sqlcipher3-binary --quiet 2>&1

:check
echo.
echo [2] Verifying SQLCipher availability...
C:\Python314\python.exe -c "import importlib; [print(f'{m} OK') if importlib.util.find_spec(m) else print(f'{m} NOT FOUND') for m in ['pysqlcipher3', 'sqlcipher3']]" 2>&1

echo.
echo [3] Running enhanced key extraction...
echo.
C:\Python314\python.exe extract_key.py 2>&1

echo.
echo === Done ===
pause
