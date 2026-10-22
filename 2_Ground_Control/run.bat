@echo off
title Bozok Roket Takimi - Yer Istasyonu
cd /d "%~dp0"

echo ===================================================================
echo           BOZOK ROKET TAKIMI - YER ISTASYONU BASLATICI
echo ===================================================================

REM 1. Modul ve telemetri yollarini ekle
set "PYTHONPATH=%~dp0;%~dp0telemetry;%PYTHONPATH%"

REM 2. Sistem Python kontrolu
set "SYSTEM_PY="
python --version >nul 2>&1
if not errorlevel 1 (
    set "SYSTEM_PY=python"
    goto :check_venv
)
py -3 --version >nul 2>&1
if not errorlevel 1 (
    set "SYSTEM_PY=py -3"
    goto :check_venv
)

:check_venv
REM 3. Sanal ortami belirle
set "VENV_PY="
if exist ".venv\Scripts\python.exe" set "VENV_PY=.venv\Scripts\python.exe"
if not defined VENV_PY if exist "..\.venv\Scripts\python.exe" set "VENV_PY=..\.venv\Scripts\python.exe"

REM Sanal ortam varsa test et
if defined VENV_PY (
    "%VENV_PY%" -c "import sys" >nul 2>&1
    if not errorlevel 1 goto :check_packages
    echo [UYARI: Mevcut .venv calismadi. Yeniden olusturulacak.]
    if exist ".venv" rmdir /s /q ".venv"
    set "VENV_PY="
)

REM Sanal ortam yoksa olustur
if not defined SYSTEM_PY goto :python_missing

echo [1/3] Sanal ortam hazirlaniyor...
%SYSTEM_PY% -m venv .venv
if errorlevel 1 goto :venv_error
set "VENV_PY=.venv\Scripts\python.exe"

:check_packages
REM 4. Kutuphane kontrolu
echo [2/3] Kutuphaneler kontrol ediliyor...
"%VENV_PY%" -c "import PySide6, pyqtgraph, serial, numpy" >nul 2>&1
if not errorlevel 1 goto :launch

echo.
echo ===================================================================
echo Eksik kutuphaneler tespit edildi! Otomatik yukleniyor...
echo Bu islem ilk calistirmada bir defaya mahsustur, lutfen bekleyiniz.
echo ===================================================================
echo.

"%VENV_PY%" -m pip install --upgrade pip

set "REQ_FILE=requirements.txt"
if not exist "%REQ_FILE%" if exist "..\requirements.txt" set "REQ_FILE=..\requirements.txt"

if exist "%REQ_FILE%" (
    echo [%REQ_FILE% uzerinden paketler kuruluyor...]
    "%VENV_PY%" -m pip install -r "%REQ_FILE%"
)

REM Saglamlastirma
"%VENV_PY%" -c "import PySide6, pyqtgraph, serial, numpy" >nul 2>&1
if not errorlevel 1 goto :launch

echo [PySide6-Essentials ve gerekli paketler dogrudan kuruluyor...]
"%VENV_PY%" -m pip install PySide6-Essentials pyqtgraph pyserial numpy

"%VENV_PY%" -c "import PySide6, pyqtgraph, serial, numpy" >nul 2>&1
if not errorlevel 1 goto :launch

goto :install_error

:launch
REM 5. Uygulamayi baslat
echo [3/3] Yer Istasyonu baslatiliyor...
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
echo [HATA]: Bilgisayarda Python bulunamadi!
echo Lutfen https://www.python.org adresinden Python 3.10+ kurun.
echo Kurarken "Add Python to PATH" secenegini mutlaka isaretleyin!
echo ===================================================================
echo.
pause
exit /b 1

:venv_error
echo.
echo ===================================================================
echo [HATA]: Sanal ortam olusturulamadi!
echo ===================================================================
echo.
pause
exit /b 1

:install_error
echo.
echo ===================================================================
echo [HATA]: Kutuphaneler basariyla kurulamadi!
echo Lutfen internet baglantinizi ve izinlerinizi kontrol ediniz.
echo ===================================================================
echo.
pause
exit /b 1
