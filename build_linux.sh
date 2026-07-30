#!/usr/bin/env bash
# SchematicViz — Linux paketleme betiği (build_exe.bat'ın Linux karşılığı).
# Aynı SchematicViz.spec dosyasını kullanır; çıktı: dist/SchematicViz (ELF).
# Kullanım:  bash build_linux.sh    (veya: chmod +x build_linux.sh && ./build_linux.sh)
#
# NOT: PyInstaller çıktısı, DERLENDİĞİ makinenin glibc'sine bağlanır —
# binary hangi dağıtımda çalışacaksa orada (veya daha eskisinde) paketle.
# wn-geometer nedeniyle zaten Ubuntu 24.04+ gerekiyor (bkz. requirements.txt).
#
# BOYUT NOTU: Paketlemeyi TEMİZ bir venv içinde yap — ortamda başka
# projelerden kalma paketler (numba/scipy vb.) varsa PyInstaller onları da
# gömer (450MB'lık çıktı böyle oluştu). Temiz venv:
#   python3 -m venv .venv-build && source .venv-build/bin/activate
#   pip install -r requirements.txt pyinstaller
#   bash build_linux.sh

set -u
cd "$(dirname "$(readlink -f "$0")")"

echo "============================================================"
echo "  SchematicViz - Linux paketleniyor (PyInstaller)"
echo "============================================================"
echo

PY=python3
echo "Kullanilan Python: $("$PY" -c 'import sys; print(sys.executable)')"
echo

if ! "$PY" -m pip --version >/dev/null 2>&1; then
  echo "HATA: pip yok. Kurulum:  sudo apt install python3-pip"
  exit 1
fi

# ÖN KONTROL: uygulama bağımlılıkları BU python'da kurulu mu?
# (PyInstaller eksik paketi yalnız UYARIyla geçer, build "başarılı" görünür
# ama binary açılışta ModuleNotFoundError verir — pyenv/sistem python
# karışıklığında yaşandı.)
if ! "$PY" -c "import altium_monkey, PyQt5, openpyxl, cascadio, trimesh, numpy" 2>/dev/null; then
  echo "HATA: Bagimliliklar yukaridaki Python'da kurulu degil."
  echo "Once kur:  $PY -m pip install -r requirements.txt"
  echo "(Eksik olanlar:)"
  for m in altium_monkey PyQt5 openpyxl cascadio trimesh numpy; do
    "$PY" -c "import $m" 2>/dev/null || echo "  - $m"
  done
  exit 1
fi

# PyInstaller kurulu mu? Değilse kur. Ubuntu 24.04'te sistem Python'u
# PEP 668 korumalı (externally-managed) — venv içinde değilsek normal
# kurulum reddedilir, --break-system-packages ile yeniden denenir.
if ! "$PY" -m PyInstaller --version >/dev/null 2>&1; then
  echo "PyInstaller bulunamadi - kuruluyor..."
  "$PY" -m pip install pyinstaller \
    || "$PY" -m pip install --break-system-packages pyinstaller
  echo
fi

# Derleme ayarları SchematicViz.spec'te (collect-all listesi, PyQt6 hariç
# tutma, kullanılmayan Qt kütüphanelerini kırpan _DROP filtresi — regex
# Linux'taki libQt5Qml.so vb. adları da yakalar). icon= Linux'ta yok sayılır.
"$PY" -m PyInstaller --noconfirm SchematicViz.spec
status=$?

echo
if [ "$status" -ne 0 ]; then
  echo "############################################################"
  echo "  HATA! Paketleme basarisiz oldu. Yukaridaki ciktiya bak."
  echo "############################################################"
  exit "$status"
fi

echo "============================================================"
echo "  BASARILI!  Cikti:  dist/SchematicViz"
echo "============================================================"
