@echo off
title Bozok Roket Takımı - Yer İstasyonu
cd /d "%~dp0"
call .venv\Scripts\activate.bat
python app.py
if errorlevel 1 pause
