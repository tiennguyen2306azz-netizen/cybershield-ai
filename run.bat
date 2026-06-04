@echo off
title CYBERSHIELD AI RUNNER
color 0b

echo =========================================================================
echo  __________ ___________ ____   ___  _________ ___ ___ __________ ____  ___
echo ^|___    ___^|___     ___^|    \ ^|   ^|/   ______^|   ^|   ^|___    ___^|    \^|   ^|
echo     ^|    ^|       ^|    ^|   ^| \ \^|   ^|   ^|  ___ ^|   ^|   ^|   ^|    ^|   ^| \ \^|   ^|
echo     ^|    ^|       ^|    ^|   ^|  \    ^|   ^| ^|_  ^|^|   ^|   ^|   ^|    ^|   ^|  \    ^|
echo     ^|____^|   ____^|____^|___^|   \___^|\_________^|_______^|   ^|____^|   ^|___^|   \___^|
echo                               BY CYBERSHIELD AI TEAM
echo =========================================================================
echo.
echo [i] Dang kiem tra moi truong Python...

python --version >nul 2>&1
if errorlevel 1 (
    color 0c
    echo [!] LOI: Python chua duoc cai dat tren he thong cua ban!
    echo [!] Vui long tai va cai dat Python tai https://www.python.org/
    echo [!] Nho tich chon "Add Python to PATH" khi cai dat.
    pause
    exit
)

if not exist ".venv" (
    echo [i] Khong tim thay thu muc thu vien ao .venv. Dang khoi tao...
    python -m venv .venv
    echo [+] Da tao thanh cong moi truong ao tai .venv
)

echo [i] Dang kich hoat moi truong ao .venv...
call .venv\Scripts\activate

echo [i] Dang kiem tra va cap nhat cac thu vien (requirements.txt)...
pip install -r requirements.txt
if errorlevel 1 (
    color 0c
    echo [!] Canh bao: Co loi xay ra khi cai dat thu vien.
    echo [!] Vui long kiem tra lai ket noi Internet hoac phien ban Python.
)

echo.
echo =========================================================================
echo [+] KHOI DONG THANH CONG CYBERSHIELD AI LINK ANALYZER SERVER!
echo [+] Dia chi truy cap: http://localhost:5000/
echo =========================================================================
echo.
echo [i] Nhan Ctrl+C tren Console nay de dung may chu.
echo.

python app.py

pause
