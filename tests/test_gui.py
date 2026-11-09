"""
@file tests/test_gui.py
@brief Arayüz duman testi (ekransız Qt): pencere, menüler, dil gidiş-dönüşü.

@details `gui.run_selftest` paketlenmiş uygulamanın da kullandığı denetimdir
(tools/smoke_launch.py); burada kaynaktan çalıştırılır. Ekran gerekmesin diye
QT_QPA_PLATFORM yoksa `offscreen` atanır.
"""
import json
import os
import unittest

from tests._support import OUT

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


class TestGui(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import gui
        from PyQt5 import QtWidgets
        cls.gui = gui
        cls.app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])

    def test_selftest_ui_only(self):
        """--selftest (projesiz): gui.ui yükleniyor, menü kuruluyor, dil dönüyor."""
        OUT.mkdir(parents=True, exist_ok=True)
        report = OUT / "gui_selftest.json"
        code = self.gui.run_selftest(str(report))
        data = json.loads(report.read_text(encoding="utf-8"))
        self.assertEqual(code, 0, data.get("error"))
        self.assertEqual([s["step"] for s in data["steps"]], ["arayuz", "dil", "importlar"])

    def test_button_labels_match_ui(self):
        """_BTN_LABELS gui.ui'deki kaynak etiketlerle birebir (üretimden sonra geri yazılır)."""
        import i18n
        i18n.set_language("tr")
        win = self.gui.MainWindow()
        try:
            win.set_language("tr", persist=False)
            for name, label in win._BTN_LABELS.items():
                btn = getattr(win, name, None)
                with self.subTest(button=name):
                    self.assertIsNotNone(btn)
                    self.assertEqual(btn.text(), label)
        finally:
            win.close()

    def test_theme_dialog(self):
        """Renk Temaları: kopyala → renk değiştir → Tamam dosyaya yazar; ana pencere bağlı."""
        import re
        import tempfile
        from unittest import mock
        from PyQt5 import QtGui, QtWidgets
        import i18n
        import themes
        import theme_dialog
        with tempfile.TemporaryDirectory() as tmp:
            dlg = theme_dialog.ThemeDialog(None, "nord", "eagle", theme_dir=tmp)
            self.assertEqual(dlg.selected_ids(), ("nord", "eagle"))
            dlg.tabs.setCurrentIndex(1)
            with mock.patch.object(QtWidgets.QMessageBox, "question",
                                   return_value=QtWidgets.QMessageBox.Yes), \
                 mock.patch.object(QtWidgets.QColorDialog, "getColor",
                                   return_value=QtGui.QColor(10, 200, 30)):
                dlg.edit_color("board", ("copper", "f"))    # hazır tema → kopya
            sch, pcb = dlg.selected_ids()
            self.assertTrue(pcb.startswith("u-"), pcb)
            dlg.accept()
            packs, errors = themes.load_user_packs(tmp)
            self.assertEqual(errors, [])
            self.assertEqual([p["id"] for p in packs], [pcb])
            self.assertEqual(packs[0]["board"]["copper"]["f"], "#0ac81e")
            self.assertEqual(sch, "nord")
            dlg.close()
            # İngilizce: diyalogda Türkçe metin kalmamalı
            i18n.set_language("en")
            try:
                d2 = theme_dialog.ThemeDialog(None, theme_dir=tmp)
                texts = [d2.tabs.tabText(i) for i in range(d2.tabs.count())]
                for w in d2.findChildren(QtWidgets.QWidget):
                    for prop in ("text", "toolTip"):
                        v = w.property(prop)
                        if isinstance(v, str):
                            texts.append(v)
                for sec in ("schematic", "board"):
                    c = d2.ui[sec]["combo"]
                    texts += [c.itemText(i) for i in range(c.count())]
                bad = [t for t in texts if re.search("[çğıöşüÇĞİÖŞÜ]", t)]
                self.assertEqual(bad, [])
                d2.close()
            finally:
                i18n.set_language("tr")
        win = self.gui.MainWindow()
        try:
            self.assertIsNotNone(getattr(win, "themesBtn", None))
            self.assertIn("Renk Temaları ve Yazı Tipleri…", [src for _o, src in win._menu_texts])
            ts = win.theme_set()
            self.assertIn(ts["sch"], {p["id"] for p in ts["packs"]} | {"altium"})
            self.assertEqual(set(ts["fonts"]), {"sch", "pcb", "ui"})
            # kayıt yoksa üç yazı tipi de Segoe UI; "özgün" kaydı ('') korunur
            from PyQt5 import QtCore
            with tempfile.TemporaryDirectory() as tmp:
                win.settings = QtCore.QSettings(os.path.join(tmp, "s.ini"),
                                                QtCore.QSettings.IniFormat)
                self.assertEqual(win._fonts(), {"sch": "Segoe UI", "pcb": "Segoe UI",
                                                "ui": "Segoe UI"})
                win.settings.setValue("fontPcb", "")
                self.assertEqual(win._fonts()["pcb"], "")
                win.settings.sync()
                del win.settings
        finally:
            win.close()
        # Yazı Tipleri sekmesi: başlangıç değeri, seçim, özgün = ''
        with tempfile.TemporaryDirectory() as tmp:
            d3 = theme_dialog.ThemeDialog(None, theme_dir=tmp,
                                          fonts={"sch": "Courier New", "pcb": "", "ui": "X;bad"})
            self.assertEqual(d3.tabs.count(), 3)
            got = d3.selected_fonts()
            self.assertEqual(got["sch"], "Courier New")
            self.assertEqual(got["pcb"], "")
            self.assertEqual(got["ui"], "", "geçersiz ad atılmalı")
            d3.tabs.setCurrentIndex(2)
            self.assertFalse(d3.copyBtn.isEnabled())
            self.assertIsNone(d3.copy_current(ask_name=False))
            c = d3.font_ui["pcb"][0]
            c.setCurrentIndex(1)
            self.assertEqual(d3.selected_fonts()["pcb"], c.itemData(1))
            d3.close()
        win = self.gui.MainWindow()
        try:
            pass
        finally:
            win.close()

    def test_no_missing_translations(self):
        """Arayüzdeki her Türkçe etiketin İngilizce karşılığı var."""
        import i18n
        win = self.gui.MainWindow()
        try:
            texts = [src for _w, _prop, src in win._ui_snapshot] \
                + [src for _obj, src in win._menu_texts]
            self.assertEqual(i18n.missing_keys(texts), [])
        finally:
            win.close()


if __name__ == "__main__":
    unittest.main()
