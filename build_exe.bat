@echo off
chcp 65001 >nul
title SchematicViz - EXE Paketleme
cd /d "D:\pythonProjeler\altium-monley"

echo ============================================================
echo   SchematicViz - EXE paketleniyor (PyInstaller)
echo ============================================================
echo.

REM ON KONTROL: uygulamanin bagimliliklari BU python'da kurulu mu?
REM (PyInstaller eksik paketi yalniz UYARIyla gecer; exe "basarili" uretilir
REM ama acilista ModuleNotFoundError verir.) Liste deps.py'de - uygulamanin
REM kendi baslangic denetimiyle ayni kaynak; eksik varsa deps.py 1 dondurur.
py -3.12 deps.py
if errorlevel 1 (
  echo.
  echo ############################################################
  echo   HATA! Bagimliliklar eksik - paketleme durduruldu.
  echo   Kur:  py -3.12 -m pip install -r requirements.txt
  echo ############################################################
  echo.
  pause ^>nul
  exit /b 1
)
echo.

REM PyInstaller kurulu mu? Degilse Python 3.12'ye kur.
py -3.12 -m PyInstaller --version >nul 2>&1
if errorlevel 1 (
  echo PyInstaller bulunamadi - kuruluyor...
  py -3.12 -m pip install pyinstaller
  echo.
)

REM Derleme ayarlari SchematicViz.spec dosyasinda (collect-all listesi,
REM PyQt6 haric tutma, kullanilmayan Qt DLL'lerini kirpan _DROP filtresi).
REM PyQt5 icin collect-all YOK: QML/Designer/ceviriler ~50MB gomuyordu;
REM PyInstaller'in PyQt5 hook'u gerekli cekirdegi zaten toplar.
py -3.12 -m PyInstaller --noconfirm "D:\pythonProjeler\altium-monley\SchematicViz.spec"

echo.
if errorlevel 1 (
  echo ############################################################
  echo   HATA! Paketleme basarisiz oldu. Yukaridaki ciktiya bak.
  echo ############################################################
) else (
  echo ============================================================
  echo   BASARILI!  Cikti:  dist\SchematicViz.exe
  echo ============================================================
)

echo.
echo Pencereyi kapatmak icin bir tusa basin...
pause >nul
