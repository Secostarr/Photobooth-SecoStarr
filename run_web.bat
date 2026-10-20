@echo off
cd /d "%~dp0"
echo Starting Photobooth Local Web App...
echo Open in browser: http://127.0.0.1:5000
py web_app.py
pause
