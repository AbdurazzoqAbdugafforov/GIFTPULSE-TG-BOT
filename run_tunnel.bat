@echo off
title GiftPulse Mini App HTTPS Tunnel
echo ========================================================
echo   GiftPulse Telegram Mini App - Bepul HTTPS Tunnel
echo ========================================================
echo.
echo 1. FastAPI serveringiz (run.bat) ishlab turganiga ishonch hosil qiling (Port 8000).
echo 2. Hozir sizga bepul HTTPS havola beriladi...
echo.
npx localtunnel --port 8000
pause
