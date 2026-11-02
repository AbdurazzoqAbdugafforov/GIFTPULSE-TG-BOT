@echo off
title GiftPulse Platform
echo ===================================================================
echo     🎁 GiftPulse — Telegram Gifts Analytics & Monitoring Platform
echo ===================================================================
echo.

if exist venv\Scripts\python.exe (
    set "PYTHON_EXE=venv\Scripts\python.exe"
) else (
    set "PYTHON_EXE=python"
)

echo [1/3] Tekshirilmoqda: Python muhiti...
%PYTHON_EXE% --version
if errorlevel 1 (
    echo Xatolik: Python topilmadi! Iltimos, Python 3.12+ o'rnating.
    pause
    exit /b 1
)

echo [2/3] Barcha xizmatlar birgalikda ishga tushirilmoqda:
echo       - 📱 Telegram Mini App API: http://localhost:8000
echo       - 🤖 Telegram Boti (Aiogram)
echo       - 📊 TG Gifts Data Ingestion Worker
echo.
echo [3/3] Dasturni to'xtatish uchun: Ctrl + C
echo ===================================================================
echo.

%PYTHON_EXE% run.py %*

pause
