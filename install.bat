@echo off
title PHOTOBOOTH - Setup
echo ============================================
echo     PHOTOBOOTH - Setup & Install
echo ============================================
echo.

REM Check Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python tidak ditemukan!
    echo.
    echo Silakan install Python dari:
    echo   https://www.python.org/downloads/
    echo.
    echo Pastikan centang "Add Python to PATH" saat install!
    pause
    exit /b 1
)

echo Python found:
python --version
echo.

echo Installing required packages...
echo.
pip install --upgrade pip
pip install -r requirements.txt

echo.
echo ============================================
echo Setup selesai!
echo.
echo Untuk menjalankan aplikasi:
echo   1. Klik kanan run.bat
echo   2. Pilih "Run as Administrator" (opsional)
echo   3. Atau jalankan: python main.py
echo ============================================
echo.
pause
