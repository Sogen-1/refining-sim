@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo.
echo  油脂精炼工艺模拟引擎 v3.1
echo  浏览器访问: http://127.0.0.1:5090
echo  按 Ctrl+C 停止
echo.
start "" http://127.0.0.1:5090
python app.py
pause
