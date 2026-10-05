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
