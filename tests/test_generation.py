"""
@file tests/test_generation.py
@brief Uçtan uca üretim: örnek projelerden TÜM çıktı türleri üretilip denetlenir.

@details Örnekler altium_monkey deposundan sabit commit'le iner
(tools/fetch_samples.py). Her proje için çıktılar `setUpClass`'ta BİR kez
üretilir; bir çıktının hatası diğerlerini gizlemesin diye hatalar saklanıp
ilgili testte raporlanır. Çıktılar `.tmp/test-out/<proje>/` altında kalır
(CI başarısız olursa artifact olarak yüklenir).
"""
import csv
import json
import shutil
import traceback
import unittest

from tests._support import OUT, assert_js_valid, combined_inner, sample_project


class _ProjectBase:
    """Proje başına test kümesi (alt sınıf PROJECT/HAS_PCB/MCU belirler)."""
    PROJECT = None
    HAS_PCB = False
    MCU = None          # MCU pin listesi için designator (None = test atlanır)
    MIN_SHEETS = 1
    MIN_COMPONENTS = 1

    @classmethod
    def setUpClass(cls):
        import viewer
        cls.viewer = viewer
        cls.prj = str(sample_project(cls.PROJECT))
        cls.dir = OUT / cls.PROJECT
        shutil.rmtree(cls.dir, ignore_errors=True)
        cls.dir.mkdir(parents=True)
        cls.logs = []
        cls.errors = {}
        cls.out = {}
        log = cls.logs.append
        jobs = {
            "json": ("generate_json", "proje.json", {}),
            "sch": ("generate_viewer", "sematik.html", {}),
            "pcb": ("generate_pcb_canvas_viewer", "pcb.html", {}),
            "combined": ("generate_combined_viewer", "birlesik.html", {}),
            "bom": ("generate_bom_csv", "bom.csv", {}),
            "pnp": ("generate_pnp_csv", "pnp.csv", {}),
            "icmap": ("generate_ic_map_xlsx", "ic_harita.xlsx", {}),
        }
        # Renk temaları: hazır + HTML'e zararlı adlı bir kullanıcı teması,
        # açılış temaları seçili (themes.py / v2.40.0)
        import themes
        user = themes.parse_pack(
            {"meta": {"name": 'Zehir</script><b>"x"'},
             "schematic": {"background": "#101010", "wire": "#00ff00",
                           "component_body": "#202020", "note": "#ffffff"},
             "board": {"background": "#ffffff", "copper": {"f": "#ff0000"}}}, "u-zehir")
        cls.theme_set = {"packs": themes.builtin_packs() + [user],
                         "sch": "u-zehir", "pcb": "u-zehir",
                         "fonts": {"sch": "Courier New", "pcb": "Arial",
                                   "ui": 'Georgia"</style>'}}   # ui: geçersiz → atılır
        jobs["sch_theme"] = ("generate_viewer", "sematik_tema.html",
                             {"theme_set": cls.theme_set})
        jobs["pcb_theme"] = ("generate_pcb_canvas_viewer", "pcb_tema.html",
                             {"theme_set": cls.theme_set})
        if cls.MCU:
            jobs["mcupin"] = ("generate_mcu_pinout_xlsx", "mcu_pin.xlsx",
                              {"mcu_designator": cls.MCU})
        for key, (fn, fname, kw) in jobs.items():
            path = cls.dir / fname
            try:
                getattr(viewer, fn)(cls.prj, str(path), log=log, **kw)
                cls.out[key] = path
            except Exception:
                cls.errors[key] = traceback.format_exc()
        (cls.dir / "uretim.log").write_text("\n".join(map(str, cls.logs)), encoding="utf-8")

    def output(self, key):
        """@brief Üretilmiş çıktının yolunu döndürür; üretim patladıysa testi düşürür."""
        if key in self.errors:
            self.fail(f"{key} üretimi başarısız:\n{self.errors[key]}")
        path = self.out[key]
        self.assertTrue(path.is_file() and path.stat().st_size > 0, f"{path} boş/yok")
        return path

    def html(self, key):
        text = self.output(key).read_text(encoding="utf-8")
        self.assertNotIn("⟪", text, "çeviri işareti kalmış")
        self.assertNotIn("⟫", text, "çeviri işareti kalmış")
        return text

    # --- JSON ---------------------------------------------------------------
    def test_json(self):
        data = json.loads(self.output("json").read_text(encoding="utf-8"))
        s = data["summary"]
        self.assertGreaterEqual(s["sheet_count"], self.MIN_SHEETS)
        self.assertGreaterEqual(s["component_count"], self.MIN_COMPONENTS)
        self.assertTrue(s["has_netlist"], "netlist derlenemedi")
        self.assertGreater(s["pin_connection_count"], 0)
        self.assertEqual(s["has_pnp"], self.HAS_PCB)
        conns = [c for n in data["nets"] for c in n.get("connections", [])]
        self.assertTrue(conns, "hiçbir net'te pin bağlantısı yok")
        # Altium'un dolaylı metni ('=Value') parametreden çözülmeli: çözülmezse
        # BOM · Montaj paneli 0.1µF ile 2.2µF'ı tek grupta topluyordu.
        vals = [c.get("value", "") for sh in data["sheets"] for c in sh["components"]]
        unresolved = [v for v in vals if v.startswith("=")]
        self.assertEqual(unresolved, [], "çözülmemiş dolaylı değer")

    # --- HTML görüntüleyiciler ----------------------------------------------
    def test_schematic_viewer(self):
        text = self.html("sch")
        for marker in ("const DRAW_GZ", "SHEET_TREE", 'id="anno-embed"'):
            self.assertIn(marker, text)
        assert_js_valid(self, text, f"{self.PROJECT}_sch")

    EXPECT_ROLES = {"wire", "pin", "pin_number", "reference", "worksheet",
                    "component_outline"}

    def test_schematic_theme_roles(self):
        """Renk temaları: draw-list stillerinde KiCad rolleri var, bilinmeyen az."""
        import base64, gzip, re
        text = self.html("sch")
        m = re.search(r'const DRAW_GZ = "([^"]+)"', text)
        self.assertIsNotNone(m, "DRAW_GZ bulunamadı")
        dl = json.loads(gzip.decompress(base64.b64decode(m.group(1))))["s"]
        roles, n_all, n_unknown = set(), 0, 0
        for sid, d in dl.items():
            self.assertIn("sx", d, f"{sid}: rol tablosu yok")
            self.assertIn("tsx", d, f"{sid}: yazı rol tablosu yok")
            for _base, fr, sr in d["sx"]:
                roles.update(r for r in (fr, sr) if r)
            roles.update(r for _base, r in d["tsx"] if r)
            # yazıların rol kapsaması (sayfa çerçevesi dahil hepsi bilinmeli)
            for t in d["tx"]:
                n_all += 1
                n_unknown += not d["tsx"][t[0]][1]
        missing = self.EXPECT_ROLES - roles
        self.assertFalse(missing, f"eksik roller: {missing}")
        self.assertLess(n_unknown, max(1, n_all * 0.05),
                        f"rolsüz yazı çok: {n_unknown}/{n_all}")
        # Tema tablosu: her temada tüm anahtarlar dolu; seçicide hepsi var
        keys = set(self.viewer._SCH_THEMES[0][3])
        for tid, _name, _dark, colors in self.viewer._SCH_THEMES:
            self.assertEqual(set(colors), keys, tid)
            self.assertTrue(all(colors.values()), tid)
            self.assertIn(f'<option value="{tid}">', text)
        self.assertIn('<option value="altium">', text)
        # Okunurluk uyarlaması: blok dolgusu = gövde, tüm çizgi/yazı rolleri
        # zemine (gövde içindekiler gövdeye de) karşı eşiği geçiyor.
        # Yarı saydam renkler (shirokuma) zemine karıştırılmış ETKİN renkle ölçülür.
        import themes
        v = self.viewer
        for tid, _name, _dark, colors in v._SCH_THEMES:
            c = v.sch_theme_readable(colors)
            bg = v._th_rgb(c["background"])
            body = themes._th_over(c["component_body"], bg)
            sheet = themes._th_over(c["sheet_background"], bg)
            for k in v._TH_ON_BG:
                refs = ([bg] + ([body] if k in v._TH_ON_BODY else [])
                        + ([sheet] if k in themes._TH_ON_SHEET else []))
                worst = min(v._th_contrast(themes._th_over(c[k], bg), r) for r in refs)
                self.assertGreaterEqual(worst, v._TH_MIN_CONTRAST - 1e-6, f"{tid}.{k}")

    def test_schematic_viewer_english(self):
        """İngilizce üretim: dil etiketi `en`, işaret kalıntısı yok, JS geçerli."""
        import i18n
        path = self.dir / "sematik_en.html"
        i18n.set_language("en")
        try:
            self.viewer.generate_viewer(self.prj, str(path), log=lambda _m: None)
        finally:
            i18n.set_language("tr")
        text = path.read_text(encoding="utf-8")
        self.assertIn('lang="en"', text)
        self.assertNotIn("⟪", text)
        self.assertIn("Hierarchy", text)
        assert_js_valid(self, text, f"{self.PROJECT}_sch_en")

    def test_pcb_viewer(self):
        if not self.HAS_PCB:
            self.skipTest("projede PCB yok")
        text = self.html("pcb")
        self.assertIn("const GEO_GZ", text)
        assert_js_valid(self, text, f"{self.PROJECT}_pcb")

    def _js_const(self, text, name):
        """@brief Satır-içi script'teki `const AD = <JSON>;` değerini çözer."""
        import re
        m = re.search(r"const " + name + r" = (.+?);[ \t]*(?://[^\n]*)?\n", text)
        self.assertIsNotNone(m, name)
        return json.loads(m.group(1))

    def test_theme_embedding(self):
        """Renk temaları: kullanıcı teması gömülü, açılış teması seçili, ad kaçışlı."""
        text = self.html("sch_theme")
        assert_js_valid(self, text, f"{self.PROJECT}_sch_theme")
        self.assertEqual(self._js_const(text, "SCH_THEME_DEF"), "u-zehir")
        table = self._js_const(text, "SCH_THEMES")
        self.assertEqual([t[0] for t in table][-1], "u-zehir")
        self.assertEqual(len(table), len(self.viewer._SCH_THEMES) + 1)
        self.assertTrue(table[-1][2], "koyu zemin → koyu grup")
        self.assertIn('<option value="u-zehir">Zehir&lt;/script&gt;&lt;b&gt;&quot;x&quot;</option>',
                      text)
        self.assertNotIn("Zehir</script>", text)
        # yazı tipleri: şematik açılış yazı tipi gömülü, geçersiz arayüz adı atıldı
        self.assertEqual(self._js_const(text, "SCH_FONT_DEF"), "Courier New")
        self.assertIn('<option value="Courier New">Courier New</option>', text)
        self.assertNotIn('id="ui-font"', text)
        self.assertNotIn('Georgia"</style>', text)
        # varsayılan üretim: açılış teması özgün Altium, yazı tipi özgün
        self.assertEqual(self._js_const(self.html("sch"), "SCH_THEME_DEF"), "altium")
        self.assertEqual(self._js_const(self.html("sch"), "SCH_FONT_DEF"), "")
        if not self.HAS_PCB:
            return
        import base64, gzip, re
        pcb = self.html("pcb_theme")
        assert_js_valid(self, pcb, f"{self.PROJECT}_pcb_theme")
        self.assertEqual(self._js_const(pcb, "PCB_THEME_DEF"), "u-zehir")
        pt = self._js_const(pcb, "PCB_THEMES")
        import themes
        self.assertEqual([t[0] for t in pt],
                         [p["id"] for p in themes.builtin_packs() if p["board"]] + ["u-zehir"])
        geo = json.loads(gzip.decompress(base64.b64decode(
            re.search(r'const GEO_GZ = "([^"]+)"', pcb).group(1))))
        for t in pt:
            self.assertEqual(len(t[3]["c"]), len(geo["layers"]), t[0])
        top = [i for i, L in enumerate(geo["layers"]) if L["k"] == "TOP"][0]
        self.assertEqual(pt[-1][3]["c"][top], "#ff0000")
        self.assertFalse(pt[-1][2], "açık zemin → açık grup")
        self.assertIn('id="pcb-theme-sel"', pcb)
        self.assertEqual(self._js_const(self.html("pcb"), "PCB_THEME_DEF"), "altium")
        self.assertEqual(self._js_const(pcb, "LBL_FONT"), '"Arial", Consolas,monospace')
        self.assertEqual(self._js_const(self.html("pcb"), "LBL_FONT"), "Consolas,monospace")

    def test_ui_font(self):
        """Arayüz yazı tipi: `</head>`'den önce tek kural; seçilmediyse HTML'e dokunulmaz."""
        v = self.viewer
        html = "<html><head><title>x</title></head><body></body></html>"
        self.assertEqual(v._apply_ui_font(html, None), html)
        out = v._apply_ui_font(html, {"fonts": {"ui": "Segoe UI"}})
        self.assertIn('<style id="ui-font">body, body :not(.tl):not(.tl > span)', out)
        self.assertIn('font-family: "Segoe UI", "Segoe UI", system-ui, sans-serif !important', out)
        self.assertLess(out.index('id="ui-font"'), out.index("</head>"))

    def test_combined_viewer(self):
        text = self.html("combined")
        assert_js_valid(self, text, f"{self.PROJECT}_shell")
        inner = combined_inner(text)
        self.assertIn("SCH", inner)
        if self.HAS_PCB:
            self.assertEqual(set(inner), {"SCH", "PCB", "TD"})
        for name, html in inner.items():
            with self.subTest(panel=name):
                self.assertNotIn("⟪", html)
                if name == "PCB" and not self.HAS_PCB:
                    continue    # "PCB bulunamadı" yer tutucusu: script içermez
                assert_js_valid(self, html, f"{self.PROJECT}_{name}")

    def test_annotations_roundtrip(self):
        """Not taşıma: şematik ve birleşik HTML'e yazılan notlar geri okunuyor."""
        items = [{"id": "t1", "k": "note", "x": 10, "y": 20, "t": "deneme </script> <b>",
                  "fs": 14, "color": "#c62828"},
                 {"id": "t2", "k": "box", "x": 1, "y": 2, "w": 30, "h": 40, "sw": 0.5}]
        for key, where in (("sch", "html"), ("combined", "combined")):
            with self.subTest(target=key):
                src = self.output(key)
                dst = self.dir / f"notlu_{src.name}"
                shutil.copy(src, dst)
                self.assertEqual(self.viewer.write_annotations(dst, items), where)
                self.assertEqual(self.viewer.read_annotations(dst), items)

    # --- Veri çıktıları -----------------------------------------------------
    def test_bom_csv(self):
        with open(self.output("bom"), encoding="utf-8-sig", newline="") as f:
            rows = list(csv.reader(f))
        self.assertGreater(len(rows), 1, "BOM'da satır yok")

    def test_pnp_csv(self):
        if not self.HAS_PCB:
            self.skipTest("projede PCB yok")
        with open(self.output("pnp"), encoding="utf-8-sig", newline="") as f:
            rows = list(csv.reader(f))
        self.assertGreater(len(rows), 1, "Pick&Place'te satır yok")

    def test_ic_map_xlsx(self):
        import openpyxl
        wb = openpyxl.load_workbook(self.output("icmap"))
        self.assertGreater(wb.active.max_row, 1)

    def test_mcu_pinout_xlsx(self):
        if not self.MCU:
            self.skipTest("projede MCU yok")
        import openpyxl
        wb = openpyxl.load_workbook(self.output("mcupin"))
        self.assertGreater(wb.active.max_row, 2)


class TestM2Emmc(_ProjectBase, unittest.TestCase):
    """Tek sayfa şematik + PcbDoc: PCB, 3D, BOM/PnP, IC haritası yolu."""
    PROJECT = "m2_emmc"
    HAS_PCB = True
    MCU = "U1"
    MIN_COMPONENTS = 20


class TestSimpleHierarchical(_ProjectBase, unittest.TestCase):
    """PCB'siz hiyerarşik proje: sheet symbol → alt sayfa ağacı yolu."""
    PROJECT = "simple_hierchical"
    HAS_PCB = False
    MIN_SHEETS = 2
    EXPECT_ROLES = _ProjectBase.EXPECT_ROLES | {"sheet", "sheet_label",
                                                "sheet_name", "sheet_filename"}

    def test_hierarchy_tree(self):
        """Hiyerarşi ağacında bir kök ve en az bir alt düğüm var."""
        import re
        text = self.html("sch")
        m = re.search(r"const SHEET_TREE = (\{.*?\});\n", text, re.S)
        self.assertIsNotNone(m, "SHEET_TREE bulunamadı")
        tree = json.loads(m.group(1))
        nodes = tree["nodes"]
        self.assertTrue(tree["roots"], "kök yok")
        self.assertTrue(any(n["p"] != -1 for n in nodes), "alt sayfa yok")


if __name__ == "__main__":
    unittest.main()
