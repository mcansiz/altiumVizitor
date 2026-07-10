# -*- mode: python ; coding: utf-8 -*-
# SchematicViz spec — build_exe.bat bunu kullanır.
# PyQt5 için collect_all YOK (Designer/QML/çeviriler ~50 MB gömerdi);
# PyInstaller'ın PyQt5 hook'u QtWidgets çekirdeğini zaten toplar.
import re
from PyInstaller.utils.hooks import collect_all

datas = [('gui.ui', '.'), ('icon.ico', '.')]
binaries = []
hiddenimports = []
tmp_ret = collect_all('altium_monkey')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]
tmp_ret = collect_all('openpyxl')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]
tmp_ret = collect_all('cascadio')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]
tmp_ret = collect_all('trimesh')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]


a = Analysis(
    ['gui.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['PyQt6'],
    noarchive=False,
    optimize=0,
)
# Qt hook'unun eklediği ama bu saf-QtWidgets uygulamasının kullanmadığı
# fazlalıklar (~13 MB): qwebgl platform eklentisi Qt5Qml/QmlModels/Quick/
# WebSockets'i sürüklüyor; opengl32sw (20 MB) + d3dcompiler_47 yazılım-OpenGL
# yedeği — QtWidgets raster ile çizer, OpenGL context hiç açılmaz.
_DROP = re.compile(
    r'(qwebgl|Qt5Qml|Qt5QmlModels|Qt5Quick|Qt5WebSockets|opengl32sw|d3dcompiler_47)',
    re.I,
)
a.binaries = [b for b in a.binaries if not _DROP.search(b[0])]

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
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['icon.ico'],
)
