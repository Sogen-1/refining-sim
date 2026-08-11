@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo 正在启动公网隧道...
echo.
start "" python app.py
timeout /t 3 >nul
python -c "from pyngrok import ngrok; ngrok.kill(); import time; time.sleep(1); t=ngrok.connect(5090,'http',bind_tls=True); print(''); print('===================================='); print('  公网地址: '+t.public_url); print('  发给任何人即可访问'); print('===================================='); print(''); print('按 Ctrl+C 停止'); import signal; signal.pause()"
pause
