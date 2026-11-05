"""
@file tests/test_variants.py
@brief Altium varyantı: takılmayan parçalar BOM, Pick&Place, JSON ve görüntüleyicilere yansıyor.

@details `m2_emmc` örneğinin PrjPcb'sinde gerçek bir varyant var: `A` seçili, R5 ve
R6 takılmıyor.
"""
import csv
import json
import re
import shutil
import unittest

from tests._support import OUT, assert_js_valid, combined_inner, sample_project

VARIANT = "A"
NOT_FITTED = ["R5", "R6"]


def _embedded_variants(html):
    """@brief HTML'e gömülü VARIANTS nesnesini döndürür."""
    m = re.search(r"const VARIANTS = (\{.*?\});\n", html, re.S)
    assert m, "VARIANTS bulunamadı"
    return json.loads(m.group(1).replace("<\\/", "</"))


class TestVariantView(unittest.TestCase):
    """project_variant_view: Altium kayıtları → görüntüleyici verisi (dosyasız)."""

    class _Project:
        variants = {"A": {"variations": [
            {"Designator": "C85_1", "UniqueId": "\\SYM\\S1\\UIDC", "Kind": "1"},
            {"Designator": "C85_2", "UniqueId": "\\SYM\\S2\\UIDC", "Kind": "1"},
            {"Designator": "R29", "UniqueId": "\\SYM\\UIDR", "Kind": "1"},
            {"Designator": "U7", "UniqueId": "\\SYM\\UIDU", "Kind": "2"},
            {"Designator": "R99", "UniqueId": "\\SYM\\YOK", "Kind": "1"},
        ]}, "B": {"variations": []}}

        @staticmethod
        def get_current_variant():
            return "a"

    def _view(self, **kw):
        import viewer
        args = {"uid_to_des": {"UIDC": "C85", "UIDR": "R29", "UIDU": "U7"},
                "phys_by_uid": {"UIDC": {f"C85_{i}" for i in range(1, 6)}, "UIDR": {"R29"}}}
        args.update(kw)
        return viewer.project_variant_view(self._Project, **args)

    def test_active_is_matched_case_insensitively(self):
        self.assertEqual(self._view()["cur"], 0)

    def test_none_means_no_variant_selected(self):
        view = self._view(variant=None)
        self.assertEqual(view["cur"], -1)
        self.assertEqual(len(view["list"]), 2, "seçici yine tüm varyantları sunmalı")

    def test_unknown_name_is_not_selected(self):
        logs = []
        self.assertEqual(self._view(variant="YOK", log=logs.append)["cur"], -1)
        self.assertTrue(any("YOK" in m for m in logs))

    def test_physical_and_logical_mapping(self):
        rec = self._view()["list"][0]
        self.assertEqual(rec["d"], ["C85_1", "C85_2", "R29", "R99"], "Kind=2 takılı parçadır")
        self.assertEqual(rec["c"]["C85"], {"p": ["C85_1", "C85_2"], "t": 5}, "kısmi kanal")
        self.assertEqual(rec["c"]["R29"], {"p": ["R29"], "t": 1})
        self.assertNotIn("R99", rec["c"], "şemada olmayan kayıt eşlenmemeli")

    def test_stale_record_is_reported(self):
        logs = []
        self._view(log=logs.append)
        self.assertEqual(sum("A" in m for m in logs), 1)

    def test_project_without_variants(self):
        import viewer

        class Empty:
            variants = {}
        self.assertEqual(viewer.project_variant_view(Empty), {"cur": -1, "list": []})


class TestVariantOutputs(unittest.TestCase):
    """Varyantlı projeden üretim: varsayılan seçili varyant, None = varyantsız."""

    @classmethod
    def setUpClass(cls):
        import viewer
        cls.viewer = viewer
        cls.prj = str(sample_project("m2_emmc"))
        cls.dir = OUT / "variant"
        shutil.rmtree(cls.dir, ignore_errors=True)
        cls.dir.mkdir(parents=True)

    def _csv(self, fn, name, **kw):
        path = self.dir / name
        getattr(self.viewer, fn)(self.prj, str(path), log=lambda _m: None, **kw)
        with open(path, encoding="utf-8-sig", newline="") as f:
            return list(csv.reader(f))

    def test_bom_marks_active_variant_by_default(self):
        rows = self._csv("generate_bom_csv", "bom.csv")
        col = rows[0].index("dnp")
        off = sorted(r[0] for r in rows[1:] if r[col] == "True")
        self.assertEqual(off, NOT_FITTED)
        plain = self._csv("generate_bom_csv", "bom0.csv", variant=None)
        self.assertEqual(len(plain), len(rows), "BOM satır atmamalı, yalnız işaretlemeli")
        self.assertFalse([r for r in plain[1:] if r[col] == "True"])

    def test_pnp_drops_not_fitted_by_default(self):
        rows = self._csv("generate_pnp_csv", "pnp.csv")
        plain = self._csv("generate_pnp_csv", "pnp0.csv", variant=None)
        self.assertEqual(len(plain) - len(rows), 2)
        self.assertFalse({r[0] for r in rows} & set(NOT_FITTED))
        self.assertTrue(set(NOT_FITTED) <= {r[0] for r in plain})

    def test_json(self):
        path = self.dir / "proje.json"
        self.viewer.generate_json(self.prj, str(path), log=lambda _m: None)
        data = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(data["active_variant"], VARIANT)
        self.assertEqual(data["summary"]["dnp_count"], 2)
        flagged = [c["designator"] for s in data["sheets"] for c in s["components"] if c.get("dnp")]
        self.assertEqual(sorted(flagged), NOT_FITTED)

        self.viewer.generate_json(self.prj, str(path), log=lambda _m: None, variant=None)
        data = json.loads(path.read_text(encoding="utf-8"))
        self.assertIsNone(data["active_variant"])
        self.assertEqual(data["summary"]["dnp_count"], 0)
        self.assertEqual(data["variants"], [VARIANT])

    def test_viewers_embed_variant(self):
        path = self.dir / "birlesik.html"
        self.viewer.generate_combined_viewer(self.prj, str(path), log=lambda _m: None)
        inner = combined_inner(path.read_text(encoding="utf-8"))
        for name, html in inner.items():
            with self.subTest(panel=name):
                self.assertNotIn("⟪", html)
                assert_js_valid(self, html, f"variant_{name}")
                view = _embedded_variants(html)
                self.assertEqual(view["cur"], 0)
                self.assertEqual(sorted(view["list"][0]["d"]), NOT_FITTED)
                self.assertIn('id="var-sel"', html)
                self.assertIn(f">{VARIANT}</option>", html)
        self.assertEqual(sorted(_embedded_variants(inner["SCH"])["list"][0]["c"]), NOT_FITTED)

    def test_viewer_without_variant_selected_keeps_selector(self):
        path = self.dir / "sematik0.html"
        self.viewer.generate_viewer(self.prj, str(path), log=lambda _m: None, variant=None)
        html = path.read_text(encoding="utf-8")
        self.assertEqual(_embedded_variants(html)["cur"], -1)
        self.assertIn('id="var-sel"', html)


class TestNoVariantProject(unittest.TestCase):
    """Varyantsız projede seçici yok, çıktılar eskisi gibi."""

    def test_no_selector(self):
        import viewer
        out = OUT / "no_variant"
        out.mkdir(parents=True, exist_ok=True)
        path = out / "sematik.html"
        viewer.generate_viewer(str(sample_project("simple_hierchical")), str(path),
                               log=lambda _m: None)
        html = path.read_text(encoding="utf-8")
        self.assertEqual(_embedded_variants(html), {"cur": -1, "list": []})
        self.assertNotIn('id="var-sel"', html)


if __name__ == "__main__":
    unittest.main()
