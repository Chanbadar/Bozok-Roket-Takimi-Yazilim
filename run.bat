@echo off
title Bozok Roket Takimi - Yer Istasyonu
cd /d "%~dp0"

if exist "2_Ground_Control\run.bat" (
    cd 2_Ground_Control
    call run.bat
) else (
    echo [HATA]: 2_Ground_Control klasoru bulunamadi!
    pause
)
