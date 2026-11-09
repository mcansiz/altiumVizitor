"""
@file tools/build_appimage.py
@brief Linux AppImage üretir: PyInstaller klasör çıktısı + appimagetool.

@details
    python3 tools/build_appimage.py      # dist/AltiumVizitor-v<sürüm>-linux-x86_64.AppImage

Adımlar:
  1. `SCHVIZ_ONEDIR=1` ile PyInstaller → dist/AltiumVizitor/ (klasör çıktısı).
  2. AppDir: usr/lib/altiumvizitor/ (uygulama), AppRun, .desktop, ikon (PNG,
     icon.ico'nun en büyük katmanından Pillow ile — Pillow zaten bağımlılık).
  3. Sabit sürümlü appimagetool indirilir (SHA-256 denetlenir) ve paketlenir.

**glibc tabanı**: PyInstaller ikilisi derlendiği makinenin glibc'sine bağlıdır.
wn-geometer (altium_monkey bağımlılığı) zaten manylinux_2_35 olduğundan
Ubuntu 22.04 (glibc 2.35) altı desteklenemez; CI bu yüzden ubuntu-22.04'te
derler — daha yeni bir makinede derlemek eşiği gereksiz yere yükseltirdi.
Paketteki en yüksek glibc sembol sürümü ölçülüp basılır.

Gerekenler: Python bağımlılıkları + pyinstaller, `readelf` (binutils), ağ.

@author Mikail Cansız
@date 2026
"""
import hashlib
import os
import re
import shutil
import stat
import subprocess
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WORK = ROOT / ".tmp" / "appimage"
APPDIR = WORK / "AltiumVizitor.AppDir"

# Güncelleme: gh api repos/AppImage/appimagetool/releases/latest --jq \
#   '.tag_name, (.assets[] | select(.name=="appimagetool-x86_64.AppImage") | .digest)'
APPIMAGETOOL = ("appimagetool-x86_64.AppImage",
                "https://github.com/AppImage/appimagetool/releases/download/1.9.1/",
                "ed4ce84f0d9caff66f50bcca6ff6f35aae54ce8135408b3fa33abfc3cb384eb0")

DESKTOP = """[Desktop Entry]
Type=Application
Name=Altium Vizitor
GenericName=Altium schematic and PCB viewer generator
GenericName[tr]=Altium şematik ve PCB görüntüleyici üretici
Comment=Turn Altium projects into interactive HTML schematic, PCB and 3D viewers
Comment[tr]=Altium projelerini etkileşimli HTML şematik, PCB ve 3D görüntüleyicilere dönüştürür
Exec=AltiumVizitor %F
Icon=altiumvizitor
Terminal=false
Categories=Development;Electronics;
Keywords=altium;schematic;pcb;bom;netlist;
"""

APPRUN = """#!/bin/sh
# Altium Vizitor AppImage başlatıcısı.
HERE="$(dirname "$(readlink -f "$0")")"
exec "$HERE/usr/lib/altiumvizitor/AltiumVizitor" "$@"
"""


def log(msg: str) -> None:
    print(msg, flush=True)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def fetch_tool() -> Path:
    """@brief appimagetool'u indirir (önbellekte ve özeti tutuyorsa atlar).

    @return Çalıştırılabilir dosya yolu
    """
    name, base, digest = APPIMAGETOOL
    path = WORK / name
    if not path.is_file() or sha256(path) != digest:
        log(f"indiriliyor: {name}")
        WORK.mkdir(parents=True, exist_ok=True)
        with urllib.request.urlopen(base + name, timeout=120) as r:
            path.write_bytes(r.read())
    if sha256(path) != digest:
        raise SystemExit(f"HATA: {name} SHA-256 tutmuyor")
    path.chmod(path.stat().st_mode | stat.S_IXUSR)
    return path


def app_version() -> str:
    text = (ROOT / "viewer.py").read_text(encoding="utf-8")
    return re.search(r'^APP_VERSION = "([^"]+)"', text, re.M).group(1)


def max_glibc(tree: Path) -> str:
    """@brief Paketteki ELF dosyalarının istediği en yüksek GLIBC_x.y sürümü."""
    best = (0, 0)
    for p in tree.rglob("*"):
        if p.is_symlink() or not p.is_file():
            continue
        with open(p, "rb") as f:
            if f.read(4) != b"\x7fELF":
                continue
        out = subprocess.run(["readelf", "-VW", str(p)], capture_output=True,
                             text=True, errors="replace").stdout
        for a, b in re.findall(r"GLIBC_(\d+)\.(\d+)", out):
            best = max(best, (int(a), int(b)))
    return f"{best[0]}.{best[1]}"


def main() -> int:
    ver = app_version()
    target = ROOT / "dist" / f"AltiumVizitor-v{ver}-linux-x86_64.AppImage"

    log("== PyInstaller (klasör çıktısı)")
    env = dict(os.environ, SCHVIZ_ONEDIR="1")
    subprocess.run([sys.executable, "-m", "PyInstaller", "--noconfirm", "--clean",
                    "AltiumVizitor.spec"], cwd=ROOT, env=env, check=True)
    bundle = ROOT / "dist" / "AltiumVizitor"
    if not (bundle / "AltiumVizitor").is_file():
        raise SystemExit(f"HATA: {bundle}/AltiumVizitor yok")

    log("== AppDir")
    shutil.rmtree(APPDIR, ignore_errors=True)
    lib = APPDIR / "usr" / "lib" / "altiumvizitor"
    shutil.copytree(bundle, lib, symlinks=True)
    (APPDIR / "AppRun").write_text(APPRUN, encoding="utf-8")
    (APPDIR / "AppRun").chmod(0o755)
    (APPDIR / "altiumvizitor.desktop").write_text(DESKTOP, encoding="utf-8")
    from PIL import Image
    ico = Image.open(ROOT / "icon.ico")
    sizes = sorted(ico.info.get("sizes") or [ico.size])
    ico.size = sizes[-1]
    png = ico.convert("RGBA").resize((256, 256), Image.LANCZOS)
    icon_dir = APPDIR / "usr" / "share" / "icons" / "hicolor" / "256x256" / "apps"
    icon_dir.mkdir(parents=True)
    png.save(icon_dir / "altiumvizitor.png")
    png.save(APPDIR / "altiumvizitor.png")
    (APPDIR / ".DirIcon").symlink_to("altiumvizitor.png")

    log(f"paketteki en yüksek glibc sürümü: {max_glibc(APPDIR)}")

    log("== appimagetool")
    tool = fetch_tool()
    target.unlink(missing_ok=True)
    env = dict(os.environ, ARCH="x86_64", APPIMAGE_EXTRACT_AND_RUN="1")
    subprocess.run([str(tool), "--no-appstream", str(APPDIR), str(target)],
                   cwd=WORK, env=env, check=True)
    target.chmod(target.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    log(f"TAMAM: {target} ({target.stat().st_size / 1024 / 1024:.1f} MB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
