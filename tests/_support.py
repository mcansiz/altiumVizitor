"""
@file tests/_support.py
@brief Testlerin ortak yardımcıları: örnek projeler, çıktı klasörü, JS denetimi.

@details
Ortam değişkenleri (CI ikisini de 1 yapar; yerelde eksiklik testi ATLATIR):
  SCHVIZ_REQUIRE_SAMPLES=1  örnek projeler indirilemezse testler BAŞARISIZ
  SCHVIZ_REQUIRE_NODE=1     node yoksa JS sözdizimi testleri BAŞARISIZ

@author Mikail Cansız
@date 2026
"""
import base64
import gzip
import os
import re
import shutil
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / ".tmp" / "test-out"
SAMPLES = ROOT / ".tmp" / "samples"

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(ROOT / "tools") not in sys.path:
    sys.path.insert(0, str(ROOT / "tools"))

_projects = None


def _required(var: str) -> bool:
    return os.environ.get(var) == "1"


def sample_project(name: str) -> Path:
    """@brief Örnek projenin .PrjPcb yolunu döndürür (gerekirse indirir).

    @param name tools/fetch_samples.PROJECTS anahtarı
    @return Proje dosyası yolu
    @throws unittest.SkipTest İndirilemezse ve SCHVIZ_REQUIRE_SAMPLES yoksa
    """
    global _projects
    if _projects is None:
        try:
            import fetch_samples
            _projects = fetch_samples.fetch(SAMPLES)
        except Exception as exc:  # ağ yok vb.
            if _required("SCHVIZ_REQUIRE_SAMPLES"):
                raise
            _projects = {}
            print(f"[uyarı] örnek projeler indirilemedi: {exc}", file=sys.stderr)
    if name not in _projects:
        raise unittest.SkipTest(f"örnek proje yok: {name}")
    return _projects[name]


_SCRIPT_RE = re.compile(r"<script\b([^>]*)>(.*?)</script>", re.S | re.I)
_GZ_RE = re.compile(r'const (SCH|PCB|TD)_GZ\s*=\s*"([A-Za-z0-9+/=]*)"')


def inline_scripts(html: str) -> list:
    """@brief HTML'in satır-içi JavaScript bloklarını döndürür (JSON yuvaları hariç).

    @param html HTML metni
    @return Script gövdelerinin listesi
    """
    out = []
    for attrs, body in _SCRIPT_RE.findall(html):
        if "src=" in attrs or "application/json" in attrs or not body.strip():
            continue
        out.append(body)
    return out


def combined_inner(html: str) -> dict:
    """@brief Birleşik görünüm kabuğuna gzip+base64 gömülü iç HTML'leri çözer.

    @param html Kabuk HTML metni
    @return {"SCH"|"PCB"|"TD": iç HTML} (boş yuvalar dahil edilmez)
    """
    out = {}
    for name, b64 in _GZ_RE.findall(html):
        if b64:
            out[name] = gzip.decompress(base64.b64decode(b64)).decode("utf-8")
    return out


def assert_js_valid(test: unittest.TestCase, html: str, label: str) -> int:
    """@brief Satır-içi script'lerin hepsini `node --check` ile denetler.

    @param test Çağıran test (skip/fail için)
    @param html HTML metni
    @param label Hata mesajında görünecek ad
    @return Denetlenen script sayısı
    """
    node = shutil.which("node")
    if node is None:
        if _required("SCHVIZ_REQUIRE_NODE"):
            test.fail("node bulunamadı (SCHVIZ_REQUIRE_NODE=1)")
        test.skipTest("node yok — JS sözdizimi denetimi atlandı")
    scripts = inline_scripts(html)
    test.assertTrue(scripts, f"{label}: satır-içi script yok")
    tmp = OUT / "_js"
    tmp.mkdir(parents=True, exist_ok=True)
    safe = re.sub(r"\W+", "_", label)
    for i, body in enumerate(scripts):
        js = tmp / f"{safe}_{i}.js"
        js.write_text(body, encoding="utf-8")
        r = subprocess.run([node, "--check", str(js)], capture_output=True, text=True,
                           encoding="utf-8", errors="replace")
        test.assertEqual(r.returncode, 0, f"{label} script #{i}: {r.stderr[-1500:]}")
    return len(scripts)
