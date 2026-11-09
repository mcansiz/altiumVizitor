"""
@file tests/test_themes.py
@brief Renk teması paketleri (themes.py): renk doğrulama, KiCad biçimi,
       kullanıcı klasörü gidiş-dönüşü, PCB katman eşlemesi.

@details Örnek proje gerekmez. Kullanıcı klasörü her testte geçici bir
klasördür (gerçek tema klasörüne dokunulmaz).
"""
import json
import tempfile
import unittest
from pathlib import Path

import themes

# KiCad'in kendi yazdığı biçimde küçük bir tema (rgb()/rgba(), eski sürümde
# eksik anahtarlar, bizim kullanmadığımız bölüm ve anahtarlar)
KICAD_THEME = {
    "meta": {"name": "Deneme <b>\"x\"</b>", "filename": "deneme", "version": 2},
    "schematic": {
        "background": "rgb(30, 30, 30)", "wire": "rgb(0, 200, 0)",
        "component_outline": "rgb(200, 0, 0)", "component_body": "rgb(50, 50, 50)",
        "note": "rgba(100, 150, 255, 1.000)", "erc_error": "rgba(255, 0, 0, 0.800)",
        "override_item_colors": False,
    },
    "board": {
        "background": "rgb(0, 16, 35)", "f_silks": "rgb(242, 237, 161)",
        "f_mask": "rgba(216, 100, 255, 0.400)",
        "copper": {"f": "rgb(200, 52, 52)", "b": "rgb(77, 127, 196)", "in1": "rgb(1, 2, 3)"},
    },
    "3d_viewer": {"board": "rgb(51, 43, 23)"},
}


class TestColors(unittest.TestCase):
    def test_norm_color(self):
        n = themes.norm_color
        self.assertEqual(n("#ABC"), "#aabbcc")
        self.assertEqual(n("#a0b0c0"), "#a0b0c0")
        self.assertEqual(n("rgb(1, 2, 3)"), "#010203")
        self.assertEqual(n("rgba(216, 100, 255, 0.400)"), "rgba(216,100,255,0.4)")
        self.assertEqual(n("rgba(1,2,3,1.0)"), "#010203")
        self.assertEqual(n("rgba(255,255,255,0)"), "rgba(255,255,255,0)")
        self.assertEqual(n("#11223380"), "rgba(17,34,51,0.502)")
        # JS / CSS'e gömülür: tanınmayan her şey reddedilmeli
        for bad in ("red", "javascript:alert(1)", "rgb(1,2,300)", "'#fff'", "#fff;}",
                    "rgb(1,2,3)</script>", None, 12, ""):
            self.assertIsNone(n(bad), bad)
        self.assertEqual(themes.kicad_color("#010203"), "rgb(1, 2, 3)")
        self.assertEqual(themes.kicad_color("rgba(1,2,3,0.4)"), "rgba(1, 2, 3, 0.400)")

    def test_fonts(self):
        c = themes.clean_font
        self.assertEqual(c("Segoe UI"), "Segoe UI")
        self.assertEqual(c(" DejaVu Sans Mono "), "DejaVu Sans Mono")
        self.assertEqual(c("Noto Sans CJK JP"), "Noto Sans CJK JP")
        for bad in ('Arial", x', "a;b", "x</style>", "@MS Gothic", "a{b}", "a,b", None, ""):
            self.assertEqual(c(bad), "", bad)
        self.assertEqual(themes.css_font_stack("Arial", "Consolas,monospace"),
                         '"Arial", Consolas,monospace')
        self.assertEqual(themes.css_font_stack("monospace", "x"), "monospace, x")
        self.assertEqual(themes.css_font_stack("", "Consolas,monospace"), "Consolas,monospace")

    def test_clean_name(self):
        self.assertEqual(themes.clean_name("⟪Ad⟫\x00 __GEO_GZ__"), "Ad _GEO_GZ_")
        self.assertEqual(themes.clean_name(""), "?")
        self.assertEqual(len(themes.clean_name("x" * 200)), 60)


class TestBuiltins(unittest.TestCase):
    def test_builtin_schematic_complete_and_readable(self):
        packs = themes.builtin_packs()
        # v2.36.0'daki 11 tema başta ve sırası değişmedi
        self.assertEqual([p["id"] for p in packs[:11]],
                         ["kicad", "wlight", "sol-light", "nord", "blue-tone", "bw",
                          "sol-dark", "wdark", "behave", "monokai", "eagle"])
        self.assertEqual(len({p["id"] for p in packs}), len(packs), "kimlik çakışması")
        self.assertGreaterEqual(sum(1 for p in packs if p["schematic"]), 28)
        self.assertGreaterEqual(sum(1 for p in packs if p["board"]), 18)
        for p in packs:
            self.assertTrue(p["schematic"] or p["board"], p["id"])
            self.assertIn(p["license"], ("CC0-1.0", "MIT", "Apache-2.0"), p["id"])
            self.assertTrue(p["source"] and p["copyright"], p["id"])
            if p["schematic"]:
                self.assertEqual(set(p["schematic"]), set(themes.SCH_KEYS), p["id"])
                self.assertTrue(all(themes.norm_color(v) for v in p["schematic"].values()), p["id"])
                self.assertEqual(p["dark"], themes.is_dark(p["schematic"]["background"]), p["id"])
            if p["board"]:
                self.assertTrue(p["board"]["copper"].get("f") and p["board"]["copper"].get("b"),
                                p["id"])
                self.assertTrue(all(themes.norm_color(v) for k, v in p["board"].items()
                                    if k != "copper"), p["id"])
        # MIT / Apache temalarının telif satırı uygulama içindeki bildirimde
        text = themes.notices_text()
        for p in packs:
            if p["license"] != "CC0-1.0":
                self.assertIn(p["copyright"], text, p["id"])
        self.assertIn("Permission is hereby granted", text)

    def test_altium_board_matches_viewer(self):
        """ALTIUM_BOARD, görüntüleyicinin varsayılan katman renkleriyle aynı."""
        import viewer
        st = viewer._GEO_LAYER_STYLE
        b = themes.ALTIUM_BOARD
        self.assertEqual(st["TOP"][2], b["copper"]["f"])
        self.assertEqual(st["BOTTOM"][2], b["copper"]["b"])
        self.assertEqual(st["TOP_OVERLAY"][2], b["f_silks"])
        self.assertEqual(st["BOTTOM_OVERLAY"][2], b["b_silks"])
        self.assertEqual(st["TOP_SOLDER"][2], b["f_mask"])
        self.assertEqual(st["MULTI_LAYER"][2], b["pad_through_hole"])
        self.assertEqual(st["KEEPOUT"][2], b["margin"])
        # viewer'ın eski adı hazır temaların aynısını veriyor
        self.assertEqual(viewer._SCH_THEMES, themes.legacy_sch_table())


class TestSheetFill(unittest.TestCase):
    """Blok (sayfa sembolü) dolgusu gövde dolgusundan ayrı ve düzenlenebilir."""

    BASE = {"background": "#ffffff", "wire": "#008000", "component_body": "#ffffc0",
            "component_outline": "#800000", "note": "#0000c0", "sheet": "#800000",
            "sheet_label": "#006060", "sheet_name": "#006060"}

    def test_user_fill_kept_and_texts_readable(self):
        sch = themes.parse_pack({"schematic": dict(self.BASE, sheet_background="#c0e0ff")},
                                "u")["schematic"]
        self.assertEqual(sch["sheet_background"], "#c0e0ff", "opak blok rengi korunur")
        c = themes.sch_theme_readable(sch)
        self.assertEqual(c["sheet_background"], "#c0e0ff")
        self.assertEqual(c["component_body"], "#ffffc0")

    def test_dark_block_on_light_background(self):
        """Blok dolgusu zeminin öbür tarafında: blok içi yazılar ters yönde düzeltilir."""
        sch = themes.parse_pack({"schematic": dict(self.BASE, sheet_background="#202040")},
                                "u")["schematic"]
        c = themes.sch_theme_readable(sch)
        bg = themes._th_rgb(c["background"])
        fill = themes._th_rgb(c["sheet_background"])
        # zemin beyaz, blok lacivert: ilk yön (koyulaştırma) blok içinde yazıyı
        # kaybederdi; öbür yön hem zemine hem bloğa 3:1 sağlıyor (ölçüldü 3.24 / 3.01)
        for k in ("sheet_label", "sheet"):
            x = themes._th_rgb(c[k])
            self.assertGreaterEqual(min(themes._th_contrast(x, bg), themes._th_contrast(x, fill)),
                                    themes._TH_MIN_CONTRAST - 1e-6, k)

    def test_builtins(self):
        """Her hazır temada blok dolgusu zeminden ve sembol gövdesinden ayırt edilir."""
        for p in themes.builtin_packs():
            s = p["schematic"]
            if not s:
                continue
            bg = themes._th_rgb(s["background"])
            fill = themes._th_rgb(s["sheet_background"])
            body = themes._th_over(s["component_body"], bg)
            self.assertIsNotNone(fill, p["id"])
            self.assertGreaterEqual(themes._de(fill, bg), themes._SHEET_FILL_MIN_DE, p["id"])
            self.assertGreaterEqual(themes._de(fill, body), themes._SHEET_FILL_MIN_DE, p["id"])


class TestPacks(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_parse_kicad_theme(self):
        p = themes.parse_pack(KICAD_THEME, "u-x")
        self.assertEqual(set(p["schematic"]), set(themes.SCH_KEYS))
        sch = p["schematic"]
        self.assertEqual(sch["background"], "#1e1e1e")
        self.assertEqual(sch["worksheet"], sch["note"], "eksik worksheet ← note")
        self.assertEqual(sch["bus"], sch["wire"], "eksik bus ← wire")
        # saydam blok → zeminden ve gövdeden ayırt edilen türetilmiş dolgu
        bg, fill = themes._th_rgb(sch["background"]), themes._th_rgb(sch["sheet_background"])
        self.assertGreaterEqual(themes._de(fill, bg), themes._SHEET_FILL_MIN_DE)
        self.assertGreaterEqual(themes._de(fill, themes._th_rgb(sch["component_body"])),
                                themes._SHEET_FILL_MIN_DE)
        self.assertNotIn("erc_error", sch)
        self.assertTrue(p["dark"])
        self.assertEqual(p["board"]["f_mask"], "rgba(216,100,255,0.4)")
        self.assertEqual(p["board"]["copper"]["in1"], "#010203")
        self.assertIsNone(themes.parse_pack({"schematic": {"wire": "#000"}}, "u"), "zeminsiz")
        self.assertIsNone(themes.parse_pack([], "u"))
        only_board = themes.parse_pack({"board": KICAD_THEME["board"]}, "u-b")
        self.assertIsNone(only_board["schematic"])
        self.assertTrue(only_board["board"])

    def test_save_load_roundtrip_keeps_kicad_extras(self):
        src = self.dir / "src.json"
        src.write_text(json.dumps(KICAD_THEME), encoding="utf-8")
        pack = themes.import_file(src, dirpath=self.dir)
        pack["board"]["copper"]["f"] = "#0ac81e"
        path = themes.save_pack(pack, self.dir)
        raw = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(raw["board"]["copper"]["f"], "rgb(10, 200, 30)")
        self.assertIn("3d_viewer", raw, "KiCad'in diğer bölümleri korunmalı")
        self.assertEqual(raw["schematic"]["erc_error"], "rgba(255, 0, 0, 0.800)")
        self.assertIs(raw["schematic"]["override_item_colors"], False)
        packs, errors = themes.load_user_packs(self.dir)
        mine = [p for p in packs if p["path"] == path]
        self.assertEqual(len(mine), 1)
        self.assertEqual(mine[0]["id"], themes.user_id(path.stem))
        self.assertEqual(mine[0]["board"]["copper"]["f"], "#0ac81e")
        self.assertEqual(mine[0]["name"], KICAD_THEME["meta"]["name"])

    def test_load_errors_and_import_errors(self):
        (self.dir / "bozuk.json").write_text("{bozuk", encoding="utf-8")
        (self.dir / "bos.json").write_text('{"meta": {}}', encoding="utf-8")
        packs, errors = themes.load_user_packs(self.dir)
        self.assertEqual(packs, [])
        self.assertEqual(sorted(errors), [("bos.json", "empty"), ("bozuk.json", "json")])
        with self.assertRaisesRegex(ValueError, "json"):
            themes.import_file(self.dir / "bozuk.json", dirpath=self.dir)
        with self.assertRaisesRegex(ValueError, "empty"):
            themes.import_file(self.dir / "bos.json", dirpath=self.dir)
        self.assertEqual(themes.load_user_packs(self.dir / "yok")[0], [])

    def test_new_pack_unique_ids(self):
        a = themes.new_pack("Şık Tema", {"background": "#ffffff"}, None, (), self.dir)
        self.assertEqual(a["id"], "u-sik-tema")
        b = themes.new_pack("Şık Tema", None, None, {a["id"]}, self.dir)
        self.assertNotEqual(a["id"], b["id"])
        with self.assertRaises(ValueError):
            themes.save_pack(themes.builtin_packs()[0], self.dir)


class TestPcbMapping(unittest.TestCase):
    LAYERS = [
        {"k": "TOP_OVERLAY", "name": "Top Overlay"}, {"k": "TOP", "name": "Top Layer"},
        {"k": "MID1", "name": "IN1"}, {"k": "MID2", "name": "IN2"},
        {"k": "INTERNAL_PLANE1", "name": "GND"}, {"k": "BOTTOM", "name": "Bottom Layer"},
        {"k": "MULTI_LAYER", "name": "Multi-Layer"}, {"k": "KEEPOUT", "name": "Keep-Out"},
        {"k": "MECHANICAL_15", "name": "Top Courtyard"},
        {"k": "MECHANICAL_16", "name": "Bottom Courtyard"},
        {"k": "MECHANICAL_20", "name": "Bottom Assembly"},
        {"k": "MECHANICAL_50", "name": "Route Tool Path"},
        {"k": "MECHANICAL_29", "name": "Mechanical 29"},
        {"k": "MECHANICAL_30", "name": "Mechanical 30"},
        {"k": "LAYER_99", "name": "?"},
    ]

    def test_layer_keys(self):
        keys = themes.pcb_layer_keys(self.LAYERS)
        self.assertEqual(keys, [
            ("f_silks",), ("copper", "f"), ("copper", "in1"), ("copper", "in2"),
            ("copper", "in3"), ("copper", "b"), ("pad",), ("margin",), ("f_crtyd",),
            ("b_crtyd",), ("b_fab",), ("edge_cuts",), ("user_1",), ("user_2",), None])

    def test_theme_colors(self):
        board = themes.parse_pack(KICAD_THEME, "u")["board"]
        t = themes.pcb_theme_colors(board, self.LAYERS)
        self.assertEqual(len(t["c"]), len(self.LAYERS))
        self.assertEqual(t["c"][1], "#c83434")
        self.assertEqual(t["c"][2], "#010203")
        self.assertIsNone(t["c"][3], "temada in2 yok → özgün renk")
        self.assertIsNone(t["c"][6], "pad rengi yok → özgün renk")
        self.assertEqual(t["bg"], "#001023")
        self.assertEqual(t["hole"], t["bg"])
        self.assertNotEqual(t["fr4"], t["bg"])
        self.assertTrue(themes.norm_color(t["fr4"]))


if __name__ == "__main__":
    unittest.main()
