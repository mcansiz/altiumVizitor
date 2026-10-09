"""
@file tests/test_static.py
@brief Üretim yapmayan hızlı denetimler: bağımlılıklar, sürüm, çeviriler, sözdizimi.
"""
import py_compile
import re
import subprocess
import sys
import unittest

from tests._support import ROOT


class TestStatic(unittest.TestCase):
    def test_dependencies_installed(self):
        """deps.py tablosundaki her paket kurulu ve yeterince yeni."""
        import deps
        problems = deps.check(force=True)
        self.assertEqual(problems, [], deps.format_report(problems) if problems else "")

    def test_requirements_match_deps_table(self):
        """requirements.txt'in doğrudan bağımlılıkları deps.py tablosuyla aynı."""
        import deps
        want = set(deps.requirements_lines())
        have = set()
        for line in (ROOT / "requirements.txt").read_text(encoding="utf-8").splitlines():
            line = line.split("#", 1)[0].strip()
            if line:
                have.add(line)
        self.assertEqual(have, want)

    def test_version_format(self):
        """APP_VERSION semver biçiminde (release iş akışı etiketle karşılaştırır)."""
        text = (ROOT / "viewer.py").read_text(encoding="utf-8")
        m = re.search(r'^APP_VERSION = "([^"]+)"', text, re.M)
        self.assertIsNotNone(m, "viewer.py'de APP_VERSION yok")
        self.assertRegex(m.group(1), r"^\d+\.\d+\.\d+$")

    def test_html_i18n_catalog(self):
        """Her ⟪metin⟫ işaretinin çevirisi var, yasak karakter yok, ölü anahtar yok."""
        r = subprocess.run([sys.executable, str(ROOT / "tools" / "check_html_i18n.py")],
                           capture_output=True, text=True, encoding="utf-8",
                           errors="replace", cwd=ROOT)
        self.assertEqual(r.returncode, 0, r.stdout[-3000:] + r.stderr[-2000:])

    def test_resolve_indirect_text(self):
        """'=Param' Altium dolaylı metni: harf duyarsız, zincir, döngü, eksik parametre."""
        from viewer import resolve_indirect_text as r
        self.assertEqual(r("=Value", {"Value": "0.1µF"}), "0.1µF")
        self.assertEqual(r("=value", {"VALUE": "10k"}), "10k")
        self.assertEqual(r("=A", {"A": "=B", "B": "1nF"}), "1nF")
        self.assertEqual(r("=A", {"A": "=A"}), "=A")              # döngü
        self.assertEqual(r("=Value", {}), "=Value")               # parametre yok
        self.assertEqual(r("100nF", {"Value": "x"}), "100nF")     # dolaysız
        self.assertEqual(r("=", {"": "x"}), "=")

    def test_python_sources_compile(self):
        """Depodaki her .py dosyası derleniyor (sözdizimi hatası yok)."""
        files = [p for p in ROOT.glob("*.py")] + list((ROOT / "tools").glob("*.py")) \
            + list((ROOT / "tests").glob("*.py"))
        self.assertTrue(files)
        for p in files:
            with self.subTest(file=p.name):
                py_compile.compile(str(p), doraise=True)


if __name__ == "__main__":
    unittest.main()
