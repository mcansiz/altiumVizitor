# -*- mode: python ; coding: utf-8 -*-
# SchematicViz spec — build_exe.bat (Windows) ve build_linux.sh (Linux) bunu kullanır.
# PyQt5 için collect_all YOK (Designer/QML/çeviriler ~50 MB gömerdi);
# PyInstaller'ın PyQt5 hook'u QtWidgets çekirdeğini zaten toplar.
import re
import sys
from PyInstaller.utils.hooks import collect_all

IS_LINUX = sys.platform.startswith('linux')

datas = [('gui.ui', '.'), ('icon.ico', '.')]
binaries = []
hiddenimports = []
for _pkg in ('altium_monkey', 'openpyxl', 'cascadio', 'trimesh'):
    _d, _b, _h = collect_all(_pkg)
    datas += _d; binaries += _b; hiddenimports += _h


a = Analysis(
    ['gui.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    # Build ortamında başka projelerden kalma ağır paketler varsa trimesh'in
    # opsiyonel import'ları üzerinden pakete sürükleniyorlar. Bu uygulama
    # hiçbirini kullanmaz; temiz ortamda bu liste no-op'tur.
    # NOT: 'PIL' ve 'lxml' de trimesh'in opsiyonel bağımlılığıdır (~11 MB).
    # gui.py / altium_monkey bunları kullanmıyorsa aşağıdaki listeye ekle:
    #   'PIL', 'lxml'
    excludes=['PyQt6', 'numba', 'llvmlite', 'scipy', 'matplotlib',
              'pandas', 'IPython', 'tkinter', 'PySide2', 'PySide6',
              'readline'],
    noarchive=False,
    optimize=0,
)

# ---------------------------------------------------------------------------
# Qt hook'unun eklediği ama bu saf-QtWidgets uygulamasının kullanmadığı
# fazlalıklar.
#
# Her platform:
#   qwebgl platform eklentisi Qt5Qml/QmlModels/Quick/WebSockets'i sürüklüyor;
#   opengl32sw (20 MB) + d3dcompiler_47 yazılım-OpenGL yedeği — QtWidgets
#   raster ile çizer, OpenGL context hiç açılmaz.
#
# Linux'a özgü (~4 MB):
#   Wayland istemcisi + tüm wayland-* eklentileri (uygulama XWayland/xcb ile
#   çalışır), EglFS/linuxfb/vnc/offscreen/minimalegl platformları (gömülü
#   sistemler/headless), evdev/tuio giriş eklentileri (X11 altında gerekmez),
#   nadir resim formatları, Pillow'un AVIF/Tk uzantıları.
#
# KALMALI: libqxcb, libQt5XcbQpa, libQt5DBus, xcbglintegrations,
#   platforminputcontexts, platformthemes, iconengines, libqjpeg/libqgif/
#   libqico/libqsvg — xcb eklentisi ve ikon yükleme bunlara bağımlı.
# ---------------------------------------------------------------------------
_DROP_COMMON = (
    r'qwebgl|Qt5Qml|Qt5QmlModels|Qt5Quick|Qt5WebSockets|opengl32sw|d3dcompiler_47'
)
_DROP_LINUX = (
    r'|Qt5WaylandClient|Qt5EglFSDeviceIntegration'
    r'|plugins[/\\]wayland-'
    r'|plugins[/\\]generic[/\\]'
    r'|plugins[/\\]platforms[/\\]libq(vnc|linuxfb|eglfs|minimalegl|offscreen|wayland)'
    r'|plugins[/\\]imageformats[/\\]libq(tiff|webp|icns|tga|wbmp)'
    r'|PIL[/\\]_avif|libavif|PIL[/\\]_imagingtk'
)
_DROP = re.compile(
    '(' + _DROP_COMMON + (_DROP_LINUX if IS_LINUX else '') + ')', re.I,
)
a.binaries = [b for b in a.binaries if not _DROP.search(b[0])]

# Qt çevirileri (~1,6 MB; uygulama İngilizce/Türkçe kendi metinlerini kullanır)
# ve uic widget-plugin stub'ları (PyQt5.uic derleme zamanı yardımcıları).
_DROP_DATA = re.compile(r'(Qt5[/\\]translations[/\\]|uic[/\\]widget-plugins[/\\])', re.I)
a.datas = [d for d in a.datas if not _DROP_DATA.search(d[0])]

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='SchematicViz',
    debug=False,
    bootloader_ignore_signals=False,
    # Linux: .so sembol tablolarını soy (özellikle pyenv/kaynaktan derlenmiş
    # libpython 31 MB -> ~8 MB). `strip` komutu için: sudo apt install binutils
    # Windows'ta PE dosyalarına uygulanmaz, zararsız.
    strip=IS_LINUX,
    # onefile zaten her parçayı zlib ile sıkıştırıyor; UPX üstüne pek bir şey
    # eklemez, Qt ile nadiren sorun çıkarır — kapalı.
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['icon.ico'],   # Windows/macOS'ta gömülür; Linux'ta yok sayılır (.desktop dosyası kullan)
)
