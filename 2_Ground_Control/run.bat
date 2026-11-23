@echo off
setlocal
chcp 65001 >nul 2>&1
title Bozok Roket Takimi - Yer Istasyonu
cd /d "%~dp0"

echo ===================================================================
echo           BOZOK ROKET TAKIMI - YER ISTASYONU BASLATICI
echo ===================================================================

REM 1. UTF-8 ve modul/telemetri yollarini ayarla
set "PYTHONUTF8=1"
set "PYTHONIOENCODING=utf-8"
set "PYTHONPATH=%~dp0;%~dp0telemetry;%PYTHONPATH%"

REM 2. Sistem Python kontrolu (Python 3.10+ zorunlu, Windows Store stub korumali)
set "SYSTEM_PY="
python -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)" >nul 2>&1
if not errorlevel 1 (
    set "SYSTEM_PY=python"
    goto :check_venv
)
py -3 -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)" >nul 2>&1
if not errorlevel 1 (
    set "SYSTEM_PY=py -3"
    goto :check_venv
)

:check_venv
REM 3. Sanal ortami belirle (once 2_Ground_Control\.venv, sonra kok .venv)
set "VENV_PY="
if exist ".venv\Scripts\python.exe" set "VENV_PY=.venv\Scripts\python.exe"
if not defined VENV_PY if exist "..\.venv\Scripts\python.exe" set "VENV_PY=..\.venv\Scripts\python.exe"

REM Mevcut sanal ortamin saglikli ve Python 3.10+ oldugunu test et
if defined VENV_PY (
    "%VENV_PY%" -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)" >nul 2>&1
    if not errorlevel 1 goto :check_packages
    echo [UYARI]: Mevcut sanal ortam bozuk veya eski Python surumu. Yeniden olusturulacak...
    if exist ".venv" rmdir /s /q ".venv"
    set "VENV_PY="
)

REM Sanal ortam yoksa olustur
if not defined SYSTEM_PY goto :python_missing

echo [1/4] Sanal ortam (.venv) olusturuluyor...
%SYSTEM_PY% -m venv .venv
if errorlevel 1 goto :venv_error
set "VENV_PY=.venv\Scripts\python.exe"

:check_packages
REM 4. Tum gerekli kutuphanelerin (3D WebEngine + Harita + Grafikler + Seri Port) kontrolu
echo [2/4] Kutuphaneler kontrol ediliyor (PySide6, WebEngine, PyQtGraph, PySerial, NumPy)...
"%VENV_PY%" -c "import PySide6, PySide6.QtWidgets, PySide6.QtWebEngineWidgets, PySide6.QtWebEngineCore, pyqtgraph, serial, numpy" >nul 2>&1
if not errorlevel 1 goto :check_assets

echo.
echo ===================================================================
echo Eksik kutuphaneler tespit edildi! Otomatik indiriliyor...
echo (3D Roket Gorunumu ve Harita icin PySide6 WebEngine dahildir.)
echo Bu islem ilk calistirmada bir defaya mahsustur, lutfen bekleyiniz.
echo ===================================================================
echo.

"%VENV_PY%" -m ensurepip --upgrade >nul 2>&1
"%VENV_PY%" -m pip install --upgrade pip

set "REQ_FILE=requirements.txt"
if not exist "%REQ_FILE%" if exist "..\requirements.txt" set "REQ_FILE=..\requirements.txt"

if exist "%REQ_FILE%" (
    echo [%REQ_FILE% uzerinden paketler kuruluyor...]
    "%VENV_PY%" -m pip install --upgrade -r "%REQ_FILE%"
)

REM Kurulum dogrulamasi
"%VENV_PY%" -c "import PySide6, PySide6.QtWidgets, PySide6.QtWebEngineWidgets, PySide6.QtWebEngineCore, pyqtgraph, serial, numpy" >nul 2>&1
if not errorlevel 1 goto :check_assets

echo [Eksik paketler dogrudan PyPI uzerinden tamamlaniyor...]
"%VENV_PY%" -m pip install --upgrade PySide6 pyqtgraph pyserial numpy

"%VENV_PY%" -c "import PySide6, PySide6.QtWidgets, PySide6.QtWebEngineWidgets, PySide6.QtWebEngineCore, pyqtgraph, serial, numpy" >nul 2>&1
if not errorlevel 1 goto :check_assets

goto :install_error

:check_assets
echo [3/4] 3D model ve arayuz varliklari kontrol ediliyor...
if not exist "assets\three.min.js" (
    echo [UYARI]: assets\three.min.js bulunamadi. Lutfen repoyu eksiksiz pull edin.
)
if not exist "assets\bozok_rocket.ork" (
    echo [UYARI]: assets\bozok_rocket.ork bulunamadi. Varsayilan 3D roket modeli kullanilacak.
)

:launch
REM 5. Uygulamayi baslat
echo [4/4] Yer Istasyonu baslatiliyor...
echo ===================================================================
echo.

"%VENV_PY%" app.py

if errorlevel 1 (
    echo.
    echo ===================================================================
    echo [BILGI]: Uygulama sonlandi veya bir hata olustu.
    echo ===================================================================
    pause
)
exit /b 0

:python_missing
echo.
echo ===================================================================
echo [HATA]: Bilgisayarda Python 3.10+ bulunamadi!
echo Lutfen https://www.python.org/downloads/ adresinden Python 3.10+ kurun.
echo Kurarken "Add Python to PATH" secenegini mutlaka isaretleyin!
echo ===================================================================
echo.
pause
exit /b 1

:venv_error
echo.
echo ===================================================================
echo [HATA]: Sanal ortam (.venv) olusturulamadi!
echo Python kurulumunda venv modulunun yuklu oldugundan emin olun.
echo ===================================================================
echo.
pause
exit /b 1

:install_error
echo.
echo ===================================================================
echo [HATA]: Kutuphaneler basariyla kurulamadi!
echo Lutfen internet baglantinizi, Python surumunuzu (3.10-3.13) ve
echo yazma izinlerinizi kontrol edip run.bat dosyasini yeniden calistirin.
echo ===================================================================
echo.
pause
exit /b 1
