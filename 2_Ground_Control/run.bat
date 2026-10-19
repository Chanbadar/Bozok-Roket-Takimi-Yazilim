@echo off
title Bozok Roket Takımı - Yer İstasyonu
cd /d "%~dp0"

if not exist ".venv\Scripts\activate.bat" (
    echo ========================================================
    echo [.venv bulunamadi! Sanal ortam ilk kez hazirlaniyor...]
    echo ========================================================
    python -m venv .venv
    call .venv\Scripts\activate.bat
    echo [Gerekli kutuphaneler requirements.txt uzerinden kuruluyor...]
    python -m pip install --upgrade pip
    pip install -r requirements.txt
    echo [Kurulum tamamlandi! Yer Istasyonu baslatiliyor...]
) else (
    call .venv\Scripts\activate.bat
)

python app.py
if errorlevel 1 pause

