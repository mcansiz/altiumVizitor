"""
@file gui.py
@brief viewer.py için PyQt5 masaüstü grafik arayüzü.

@details
Altium projesi seçimi, şemaların otomatik listelenmesi ve tüm çıktıların
(HTML görüntüleyiciler, Excel/CSV veri, JSON) tek pencereden üretilmesini sağlar.
Üretim arka plan iş parçacığında (GeneratorThread) yürütülür; ilerleme çubuğu ve
log canlı güncellenir. Arayüz gui.ui (Qt Designer) dosyasından yüklenir ve
APP_STYLE (QSS koyu tema) ile biçimlendirilir.

@author Mikail Cansız
@date 2026
"""
# Schematic Viz Generator — viewer.py için PyQt5 masaüstü grafik arayüzü.
# Copyright (C) 2026  Mikail Cansız <cansizmikail@gmail.com>
#
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
import sys
import platform
import webbrowser
import traceback
from pathlib import Path
from importlib import metadata

from PyQt5 import QtWidgets, QtCore, QtGui, uic
from PyQt5.QtCore import QT_VERSION_STR, PYQT_VERSION_STR

from viewer import (generate_viewer, generate_json,
                    generate_bom_csv, generate_pnp_csv,
                    generate_ic_map_xlsx, generate_mcu_pinout_xlsx,
                    generate_pcb_viewer, generate_combined_viewer,
                    APP_VERSION)


def collect_versions() -> dict:
    """@brief Çalışma ortamının sürüm bilgilerini topla (debug/destek için).
    
    @return Üretilen sonuç.
    """
    info = {
        "Uygulama": APP_VERSION,
        "Python": platform.python_version(),
        "İşletim Sistemi": f"{platform.system()} {platform.release()}",
        "Qt": QT_VERSION_STR,
        "PyQt5": PYQT_VERSION_STR,
    }
    # Pip ile kurulu modüllerin sürümleri (varsa)
    for pkg, label in (
        ("altium-monkey", "altium_monkey"),
        ("openpyxl", "openpyxl"),          # Excel dışa aktarma (BOM/IC/MCU xlsx)
        ("cascadio", "cascadio"),          # 3D STEP tessellation (opsiyonel)
        ("trimesh", "trimesh"),            # 3D STEP mesh ayrıştırma (opsiyonel)
        ("numpy", "numpy"),                # 3D STEP vertex/face işleme
        ("freetype-py", "freetype-py"),    # altium_monkey: yazı tipi render
        ("lxml", "lxml"),                  # altium_monkey: XML parse
        ("lz4", "lz4"),                    # altium_monkey: sıkıştırma
        ("pillow", "pillow"),              # altium_monkey: görüntü
        ("uharfbuzz", "uharfbuzz"),        # altium_monkey: metin şekillendirme
        ("wn-geometer", "wn-geometer"),    # altium_monkey: geometri
    ):
        try:
            info[label] = metadata.version(pkg)
        except Exception:
            info[label] = "—"
    return info


def versions_text() -> str:
    """@brief Sürüm bilgisini tek satırlık özet + çok satırlı tam liste olarak döndür.
    
    @return Üretilen sonuç.
    """
    info = collect_versions()
    lines = [f"{k:18s}: {v}" for k, v in info.items()]
    return "\n".join(lines)


UI_FILE = Path(__file__).parent / "gui.ui"
ICON_FILE = Path(__file__).parent / "icon.ico"
# PyInstaller frozen modda __file__ geçici klasörü gösterir.
# Resource'lar sys._MEIPASS altına extract edilir.
if getattr(sys, "frozen", False):
    UI_FILE = Path(sys._MEIPASS) / "gui.ui"
    ICON_FILE = Path(sys._MEIPASS) / "icon.ico"


class GeneratorThread(QtCore.QThread):
    """@brief Viewer üretimini ayrı thread'de çalıştır → GUI donmasın.
    """
    log_signal = QtCore.pyqtSignal(str)
    progress_signal = QtCore.pyqtSignal(int, str)  # percent (<0 = marquee), label
    done_signal = QtCore.pyqtSignal(bool, str)  # success, output_path

    def __init__(self, mode, project_path, output_path,
                 inter_color="#4ec9b0", intra_color="#ff9800",
                 main_designators=None, min_pins=4, exclude_prefixes=None,
                 parent=None):
        """@brief __init__()

        @param mode Üretim modu (html/json/bom/pnp/icmap/mcupin/pcbview/combined)
        @param project_path Altium proje dosyası (.PrjPcb) yolu
        @param output_path Çıktı dosyası yolu
        @param inter_color Sayfalar arası bağlantı rengi (hex)
        @param intra_color Sayfa içi bağlantı rengi (hex)
        @param main_designators Ana işlemci designator listesi
        @param min_pins Minimum pin sayısı eşiği
        @param exclude_prefixes IC haritasından hariç tutulacak designator önekleri ("J,P,TP")
        @param parent
        """
        super().__init__(parent)
        self.mode = mode  # 'html' | 'json' | 'bom' | 'pnp' | 'icmap'
        self.project_path = project_path
        self.output_path = output_path
        self.inter_color = inter_color
        self.intra_color = intra_color
        self.main_designators = main_designators
        self.min_pins = min_pins
        self.exclude_prefixes = exclude_prefixes

    def run(self):
        # İlerleme callback'i: üretici fonksiyonlara verilir, sinyale çevirir.
        """@brief Arka plan iş parçacığında seçilen üretim modunu çalıştırır.
        """
        def emit_progress(percent, label):
            """@brief İş parçacığından ilerleme sinyali yayar.
            
            @param percent Yüzde değeri (0-100)
            @param label Durum etiketi metni
            """
            self.progress_signal.emit(int(percent), str(label))
        try:
            if self.mode == "json":
                generate_json(
                    project_path=self.project_path,
                    output_path=self.output_path,
                    log=lambda msg: self.log_signal.emit(msg),
                )
            elif self.mode == "bom":
                ok = generate_bom_csv(
                    project_path=self.project_path,
                    output_path=self.output_path,
                    log=lambda msg: self.log_signal.emit(msg),
                )
                if not ok:
                    self.done_signal.emit(False, "BOM verisi yok")
                    return
            elif self.mode == "pnp":
                ok = generate_pnp_csv(
                    project_path=self.project_path,
                    output_path=self.output_path,
                    log=lambda msg: self.log_signal.emit(msg),
                )
                if not ok:
                    self.done_signal.emit(False, "Pick&Place verisi yok (PCB gerekli)")
                    return
            elif self.mode == "icmap":
                ok = generate_ic_map_xlsx(
                    project_path=self.project_path,
                    output_path=self.output_path,
                    min_pins=self.min_pins,
                    main_designators=self.main_designators,
                    exclude_prefixes=self.exclude_prefixes,
                    log=lambda msg: self.log_signal.emit(msg),
                )
                if not ok:
                    self.done_signal.emit(False, "IC haritası üretilemedi (netlist yok)")
                    return
            elif self.mode == "mcupin":
                ok = generate_mcu_pinout_xlsx(
                    project_path=self.project_path,
                    output_path=self.output_path,
                    mcu_designator=self.main_designators,
                    log=lambda msg: self.log_signal.emit(msg),
                )
                if not ok:
                    self.done_signal.emit(
                        False, "MCU pin listesi üretilemedi (MCU designator gir / netlist yok)")
                    return
            elif self.mode == "pcbview":
                ok = generate_pcb_viewer(
                    project_path=self.project_path,
                    output_path=self.output_path,
                    log=lambda msg: self.log_signal.emit(msg),
                    progress=emit_progress,
                )
                if not ok:
                    self.done_signal.emit(
                        False, "PCB görüntüleyici üretilemedi (PCB dosyası yok/okunamadı)")
                    return
            elif self.mode == "combined":
                ok = generate_combined_viewer(
                    project_path=self.project_path,
                    output_path=self.output_path,
                    inter_sheet_color=self.inter_color,
                    intra_sheet_color=self.intra_color,
                    log=lambda msg: self.log_signal.emit(msg),
                    progress=emit_progress,
                )
                if not ok:
                    self.done_signal.emit(
                        False, "Birleşik görünüm üretilemedi")
                    return
            else:
                generate_viewer(
                    project_path=self.project_path,
                    output_path=self.output_path,
                    inter_sheet_color=self.inter_color,
                    intra_sheet_color=self.intra_color,
                    log=lambda msg: self.log_signal.emit(msg),
                    progress=emit_progress,
                )
            # Çıktı yolunu mod'a göre düzelt (CSV/XLSX uzantısı)
            final_out = self.output_path
            if self.mode in ("bom", "pnp"):
                final_out = str(Path(self.output_path).with_suffix(".csv"))
            elif self.mode == "json":
                final_out = str(Path(self.output_path).with_suffix(".json"))
            elif self.mode == "icmap":
                final_out = str(Path(self.output_path).with_suffix(".xlsx"))
            elif self.mode == "mcupin":
                final_out = str(Path(self.output_path).with_suffix(".xlsx"))
            elif self.mode == "pcbview":
                final_out = str(Path(self.output_path).with_suffix(".html"))
            elif self.mode == "combined":
                final_out = str(Path(self.output_path).with_suffix(".html"))
            self.done_signal.emit(True, final_out)
        except Exception as e:
            tb = traceback.format_exc()
            self.log_signal.emit(f"\nHATA: {e}\n{tb}")
            self.done_signal.emit(False, str(e))


APP_STYLE = """
QMainWindow, QWidget { background: #1b1e24; color: #d4d9e0;
  font-family: "Segoe UI", "Segoe UI Variable", system-ui, sans-serif; font-size: 13px; }
QLabel { color: #aab2bd; background: transparent; }
QLabel[cls="h1"] { color: #e9eef4; font-size: 19px; font-weight: 700; padding: 0 2px 2px 2px; }

QGroupBox { border: 1px solid #2f3540; border-radius: 10px; margin-top: 16px;
  padding: 14px; background: #21252e; font-weight: 600; }
QGroupBox::title { subcontrol-origin: margin; subcontrol-position: top left;
  left: 14px; padding: 1px 8px; color: #5fc7ad; }
QGroupBox[cls="sub"] { background: #1b1e25; border: 1px solid #2a2f39; margin-top: 14px; }
QGroupBox[cls="sub"]::title { color: #8893a1; }
QFrame[cls="card"] { background: #1b1e25; border: 1px solid #2a2f39; border-radius: 8px; }

QLineEdit, QPlainTextEdit, QSpinBox, QListWidget { background: #14161c;
  border: 1px solid #2b303b; border-radius: 7px; padding: 7px 9px; color: #e4e8ee;
  selection-background-color: #2c7a62; }
QPlainTextEdit { font-family: Consolas, "Cascadia Mono", monospace; font-size: 12px; color: #cdd3da; }
QLineEdit:focus, QSpinBox:focus { border: 1px solid #4ec9b0; }
QListWidget::item { padding: 5px 8px; border-radius: 5px; }
QListWidget::item:selected { background: #2c7a62; color: #ffffff; }
QListWidget::item:hover { background: #232834; }

QPushButton { background: #2a303b; border: 1px solid #39414e; border-radius: 8px;
  padding: 8px 14px; color: #dde2e8; font-weight: 600; }
QPushButton:hover { background: #323a47; border-color: #4a5365; }
QPushButton:pressed { background: #232831; }
QPushButton:disabled { background: #20242b; color: #5a616c; border-color: #282d36; }

QPushButton[cls="primary"] { background: #1f8a66; border: 1px solid #2bb085;
  color: #f0fff8; font-size: 14px; }
QPushButton[cls="primary"]:hover { background: #25a079; }
QPushButton[cls="primary"]:pressed { background: #1a7355; }
QPushButton[cls="view"] { background: #265a7d; border: 1px solid #34749b; color: #e6f3fb; }
QPushButton[cls="view"]:hover { background: #2d6c95; }
QPushButton[cls="excel"] { background: #2c6f4f; border: 1px solid #3a9069; color: #eafff5; }
QPushButton[cls="excel"]:hover { background: #348361; }
QPushButton[cls="data"] { background: #2a303b; border: 1px solid #3b4150; color: #cfd6df; }
QPushButton[cls="data"]:hover { background: #323a47; border-color: #4ec9b0; color: #d6efe8; }
QPushButton[cls="ghost"] { background: transparent; border: 1px solid #39414e;
  color: #aab2bd; font-weight: 500; }
QPushButton[cls="ghost"]:hover { border-color: #4ec9b0; color: #4ec9b0; }
QPushButton[cls="ghost"]:disabled { color: #565d68; border-color: #2a2f38; }

QProgressBar { border: 1px solid #2b303b; border-radius: 6px; background: #14161c;
  color: #d6dbe2; text-align: center; min-height: 22px; font-size: 11px; }
QProgressBar::chunk { background-color: #2bb085; border-radius: 5px; }

QScrollBar:vertical { background: #1a1d24; width: 12px; margin: 0; border-radius: 6px; }
QScrollBar::handle:vertical { background: #39414e; border-radius: 6px; min-height: 26px; }
QScrollBar::handle:vertical:hover { background: #4a5365; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
QScrollBar::add-page, QScrollBar::sub-page { background: transparent; }

QSpinBox::up-button, QSpinBox::down-button { width: 16px; background: #232834;
  border-left: 1px solid #2b303b; }
QStatusBar { background: #15171c; color: #7e8794; border-top: 1px solid #2a2f38; }
QToolTip { background: #2a303b; color: #e8ecf1; border: 1px solid #4ec9b0;
  border-radius: 4px; padding: 4px 7px; }
"""


class MainWindow(QtWidgets.QMainWindow):
    """@brief Ana uygulama penceresi: proje seçimi → çıktı üretimi → canlı log.
    """
    def __init__(self):
        """@brief __init__()
        """
        super().__init__()
        uic.loadUi(UI_FILE, self)

        # Pencere/taskbar ikonu (varsa) — exe dosya ikonu --icon ile ayrı ayarlanır
        if ICON_FILE.exists():
            self.setWindowIcon(QtGui.QIcon(str(ICON_FILE)))

        # Pencere başlığına versiyon ekle
        self.setWindowTitle(f"Schematic Viz Generator  v{APP_VERSION}")
        #self.setStyleSheet(APP_STYLE)

        # Default renkler
        self.inter_color = "#4ec9b0"
        self.intra_color = "#ff9800"
        self.last_output = None
        self.worker = None
        # Son otomatik önerilen çıktı yolu (proje değişince güncellemeyi yönetir;
        # kullanıcının elle girdiği özel yolu ezmemek için takip edilir).
        self._auto_output = None

        # Sinyal bağlantıları
        self.browseProjectBtn.clicked.connect(self.browse_project)
        self.browseOutputBtn.clicked.connect(self.browse_output)
        self.interColorBtn.clicked.connect(lambda: self.pick_color("inter"))
        self.intraColorBtn.clicked.connect(lambda: self.pick_color("intra"))
        self.generateBtn.clicked.connect(self.generate)
        self.generateJsonBtn.clicked.connect(self.generate_json_action)
        self.openBtn.clicked.connect(self.open_in_browser)

        # BOM ve Pick&Place CSV butonları (varsa bağla)
        bom_btn = getattr(self, "bomBtn", None)
        if bom_btn is not None:
            bom_btn.clicked.connect(self.generate_bom_action)
        pnp_btn = getattr(self, "pnpBtn", None)
        if pnp_btn is not None:
            pnp_btn.clicked.connect(self.generate_pnp_action)
        icmap_btn = getattr(self, "icmapBtn", None)
        if icmap_btn is not None:
            icmap_btn.clicked.connect(self.generate_icmap_action)
        mcupin_btn = getattr(self, "mcuPinBtn", None)
        if mcupin_btn is not None:
            mcupin_btn.clicked.connect(self.generate_mcupin_action)
        pcbview_btn = getattr(self, "pcbViewerBtn", None)
        if pcbview_btn is not None:
            pcbview_btn.clicked.connect(self.generate_pcbview_action)
        combined_btn = getattr(self, "combinedBtn", None)
        if combined_btn is not None:
            combined_btn.clicked.connect(self.generate_combined_action)

        # "Hakkında / Sürümler" butonu (varsa bağla, yoksa sessiz geç)
        about_btn = getattr(self, "aboutBtn", None)
        if about_btn is not None:
            about_btn.clicked.connect(self.show_about)

        # Alt durum çubuğunda kalıcı versiyon özeti
        sb = self.statusBar()
        py = platform.python_version()
        try:
            am = metadata.version("altium-monkey")
        except Exception:
            am = "—"
        sb.showMessage(
            f"v{APP_VERSION}  ·  Python {py}  ·  PyQt5 {PYQT_VERSION_STR}  "
            f"·  altium_monkey {am}"
            f"							coded by Mcansız"
        )

    # === Hakkında diyaloğu ===
    def show_about(self):
        """@brief Hakkında / sürüm bilgisi diyaloğunu açar.
        """
        box = QtWidgets.QMessageBox(self)
        box.setWindowTitle("Hakkında / Sürüm Bilgisi")
        box.setIcon(QtWidgets.QMessageBox.Information)
        box.setText(f"Schematic Viz Generator  v{APP_VERSION}")
        box.setInformativeText(
            "Altium şematik projelerini interaktif HTML viewer'a ve "
            "AI analizine uygun JSON'a dönüştürür.\n\r"
            "Desing by Mikail Cansız"
        )
        # Sürüm listesini monospace detay bölümünde göster
        box.setDetailedText(versions_text())
        # Kopyalama için detayları açıkça öner
        copy_btn = box.addButton("Sürümleri Kopyala", QtWidgets.QMessageBox.ActionRole)
        box.addButton(QtWidgets.QMessageBox.Ok)
        box.exec_()
        if box.clickedButton() == copy_btn:
            QtWidgets.QApplication.clipboard().setText(versions_text())
            self.log("✓ Sürüm bilgisi panoya kopyalandı.")

    # === Proje seçimi ===
    def browse_project(self):
        """@brief Dosya diyaloğuyla Altium projesi seçer ve şemaları listeler.
        """
        path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self,
            "Altium proje dosyası seç",
            str(Path.home()),
            "Altium Project (*.PrjPcb *.PrjPCB);;Tüm Dosyalar (*)",
        )
        if not path:
            return
        self.projectPathEdit.setText(path)
        self.load_schematics(path)

        # Çıktı yolunu yeni projeye göre güncelle. Kullanıcı elle özelleştirmediyse
        # (boş ya da önceki projenin otomatik önerisiyse) yeni öneriyle değiştir;
        # bilerek girilen özel yol korunur.
        suggested = str(Path(path).parent / f"{Path(path).stem}_viz.html")
        current = self.outputPathEdit.text().strip()
        if not current or current == self._auto_output:
            self.outputPathEdit.setText(suggested)
        self._auto_output = suggested

    def load_schematics(self, project_path):
        """@brief Projeyi açıp şemaları listele.
        
        @param project_path Altium proje dosyası (.PrjPcb) yolu
        """
        self.schematicsList.clear()
        self.log("")
        try:
            from altium_monkey.altium_prjpcb import AltiumPrjPcb
            project = AltiumPrjPcb(project_path)
            paths = project.get_reachable_schdoc_paths()
            for p in paths:
                item = QtWidgets.QListWidgetItem(p.stem)
                item.setToolTip(str(p))
                self.schematicsList.addItem(item)
            self.log(f"✓ Proje açıldı, {len(paths)} şema bulundu.")
        except Exception as e:
            self.log(f"✗ Proje açılamadı: {e}")
            QtWidgets.QMessageBox.critical(
                self, "Proje yükleme hatası",
                f"Proje dosyası açılırken hata:\n\n{e}"
            )

    # === Çıktı seçimi ===
    def browse_output(self):
        """@brief Çıktı dosyası yolunu seçtirir.
        """
        suggested = self.outputPathEdit.text() or "schematic_viz.html"
        path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self, "Çıktı yolunu seç", suggested, "HTML (*.html);;Tüm Dosyalar (*)"
        )
        if path:
            self.outputPathEdit.setText(path)

    # === Renk seçici ===
    def pick_color(self, which):
        """@brief Renk seçiciyi açar ve ilgili butonu günceller.
        
        @param which Hedef seçici
        """
        current = self.inter_color if which == "inter" else self.intra_color
        color = QtWidgets.QColorDialog.getColor(
            QtGui.QColor(current), self, f"{which} rengi"
        )
        if not color.isValid():
            return
        hex_str = color.name()
        if which == "inter":
            self.inter_color = hex_str
            btn = self.interColorBtn
        else:
            self.intra_color = hex_str
            btn = self.intraColorBtn
        btn.setText(hex_str)
        # Metnin görünür kalması için kontrast hesabı
        text_color = "white" if color.lightness() < 128 else "black"
        btn.setStyleSheet(
            f"background-color: {hex_str}; color: {text_color}; "
            f"font-family: Consolas; font-weight: bold;"
        )

    # === Log ===
    def _am_version(self):
        """@brief altium_monkey sürüm dizesini döndürür.
        
        @return Üretilen sonuç.
        """
        try:
            return metadata.version("altium-monkey")
        except Exception:
            return "—"

    def log(self, msg):
        """@brief Log paneline satır ekler ve en alta kaydırır.
        
        @param msg Mesaj metni
        """
        self.logEdit.appendPlainText(msg)
        # Otomatik en alta scroll
        sb = self.logEdit.verticalScrollBar()
        sb.setValue(sb.maximum())

    # === Üretim ===
    def generate(self):
        """@brief Şematik HTML görüntüleyici üretimini başlatır.
        """
        self._start_generation(mode="html")

    def generate_json_action(self):
        """@brief AI/LLM için kompakt JSON üretimini başlatır.
        """
        self._start_generation(mode="json")

    def generate_bom_action(self):
        """@brief BOM (CSV) üretimini başlatır.
        """
        self._start_generation(mode="bom")

    def generate_pnp_action(self):
        """@brief Pick&Place (CSV) üretimini başlatır.
        """
        self._start_generation(mode="pnp")

    def generate_icmap_action(self):
        """@brief IC bağlantı haritası (Excel) üretimini başlatır.
        """
        self._start_generation(mode="icmap")

    def generate_pcbview_action(self):
        """@brief PCB görüntüleyici (HTML) üretimini başlatır.
        """
        self._start_generation(mode="pcbview")

    def generate_combined_action(self):
        """@brief Şematik + PCB + 3B birleşik görüntüleyici üretimini başlatır.
        """
        self._start_generation(mode="combined")

    def generate_mcupin_action(self):
        # MCU designator zorunlu
        """@brief MCU pin listesi (Excel) üretimini başlatır (MCU zorunlu).
        """
        main_edit = getattr(self, "mainIcEdit", None)
        mcu = main_edit.text().strip() if main_edit else ""
        if not mcu:
            QtWidgets.QMessageBox.warning(
                self, "MCU gerekli",
                "MCU pin listesi için 'Ana İşlemci(ler)' kutusuna MCU "
                "designator'ını yaz (örn. U2).")
            return
        # Tek MCU bekleniyor — virgüllüyse ilkini al
        if "," in mcu:
            QtWidgets.QMessageBox.information(
                self, "Tek MCU",
                "MCU pin listesi tek entegre içindir. İlk designator kullanılacak: "
                + mcu.split(",")[0].strip())
        self._start_generation(mode="mcupin")

    def _all_action_buttons(self):
        """@brief Üretim sırasında devre dışı bırakılacak butonlar.
        
        @return Üretilen sonuç.
        """
        names = ["generateBtn", "generateJsonBtn", "bomBtn", "pnpBtn",
                 "icmapBtn", "mcuPinBtn", "pcbViewerBtn", "combinedBtn"]
        return [getattr(self, n) for n in names if getattr(self, n, None)]

    _BTN_LABELS = {
        "generateBtn": "Şematik Viewer",
        "generateJsonBtn": "JSON (AI / LLM için)",
        "bomBtn": "BOM (CSV)",
        "pnpBtn": "Pick && Place (CSV)",
        "icmapBtn": "IC Bağlantı Haritası (Excel)",
        "mcuPinBtn": "MCU Pin Listesi (Excel)",
        "pcbViewerBtn": "PCB Görüntüleyici",
        "combinedBtn": "Şematik + PCB + 3D  ★",
    }
    _MODE_BTN = {
        "html": "generateBtn",
        "json": "generateJsonBtn",
        "bom": "bomBtn",
        "pnp": "pnpBtn",
        "icmap": "icmapBtn",
        "mcupin": "mcuPinBtn",
        "pcbview": "pcbViewerBtn",
        "combined": "combinedBtn",
    }

    def _start_generation(self, mode):
        """@brief Seçilen modda arka plan üretimini başlatır; arayüzü kilitler.
        
        @param mode Üretim modu (html/json/bom/pnp/icmap/mcupin/pcbview/combined)
        """
        project_path = self.projectPathEdit.text().strip()
        output_path = self.outputPathEdit.text().strip()
        if not project_path or not Path(project_path).exists():
            QtWidgets.QMessageBox.warning(
                self, "Eksik", "Önce geçerli bir proje dosyası seç."
            )
            return
        if not output_path:
            QtWidgets.QMessageBox.warning(
                self, "Eksik", "Çıktı yolunu belirt."
            )
            return

        # IC/MCU ayarlarını oku (uzantı ve dosya adı için gerekli)
        main_edit = getattr(self, "mainIcEdit", None)
        main_desigs = main_edit.text().strip() if main_edit else ""
        # MCU pin listesi tek entegre içindir — virgüllüyse ilkini al
        if mode == "mcupin" and "," in main_desigs:
            main_desigs = main_desigs.split(",")[0].strip()
        min_spin = getattr(self, "minPinSpin", None)
        min_pins = min_spin.value() if min_spin else 4
        excl_edit = getattr(self, "excludePrefixEdit", None)
        exclude_prefixes = excl_edit.text().strip() if excl_edit else ""

        # Çıktı uzantısını mod'a göre otomatik ayarla
        if mode == "json":
            output_path = str(Path(output_path).with_suffix(".json"))
        elif mode == "bom":
            base = Path(output_path)
            output_path = str(base.with_name(base.stem + "_BOM").with_suffix(".csv"))
        elif mode == "pnp":
            base = Path(output_path)
            output_path = str(base.with_name(base.stem + "_PnP").with_suffix(".csv"))
        elif mode == "icmap":
            base = Path(output_path)
            output_path = str(base.with_name(base.stem + "_IC_Harita").with_suffix(".xlsx"))
        elif mode == "mcupin":
            base = Path(output_path)
            tag = main_desigs if main_desigs else "MCU"
            output_path = str(base.with_name(base.stem + f"_{tag}_PinListesi").with_suffix(".xlsx"))
        elif mode == "pcbview":
            base = Path(output_path)
            output_path = str(base.with_name(base.stem + "_PCB").with_suffix(".html"))
        elif mode == "combined":
            base = Path(output_path)
            output_path = str(base.with_name(base.stem + "_Birlesik").with_suffix(".html"))

        self.logEdit.clear()
        self.log(f"Schematic Viz v{APP_VERSION}  ·  Python {platform.python_version()}"
                 f"  ·  altium_monkey {self._am_version()}")
        self.log("-" * 60)

        # Tüm butonları devre dışı bırak, aktif mod butonuna "Üretiliyor..." yaz
        for btn in self._all_action_buttons():
            btn.setEnabled(False)
        active_btn = getattr(self, self._MODE_BTN.get(mode, "generateBtn"), None)
        if active_btn:
            active_btn.setText("Üretiliyor...")
        self.openBtn.setEnabled(False)
        self._current_mode = mode

        # İlerleme çubuğunu sıfırla ve göster
        pbar = getattr(self, "progressBar", None)
        if pbar is not None:
            pbar.setRange(0, 100)
            pbar.setValue(0)
            pbar.setFormat("Başlatılıyor… %p%")
            pbar.setVisible(True)

        self.worker = GeneratorThread(
            mode, project_path, output_path,
            inter_color=self.inter_color, intra_color=self.intra_color,
            main_designators=main_desigs or None, min_pins=min_pins,
            exclude_prefixes=exclude_prefixes or None,
        )
        self.worker.log_signal.connect(self.log)
        self.worker.progress_signal.connect(self.on_progress)
        self.worker.done_signal.connect(self.on_generation_done)
        self.worker.start()

    def on_progress(self, percent, label):
        """@brief Üretim ilerlemesini çubuğa yansıt. percent<0 → belirsiz (marquee).
        
        @param percent Yüzde değeri (0-100)
        @param label Durum etiketi metni
        """
        pbar = getattr(self, "progressBar", None)
        if pbar is None:
            return
        if percent < 0:
            # Süresi kestirilemeyen adım (örn. PCB katman render) → marquee
            pbar.setRange(0, 0)
            pbar.setFormat(label)
        else:
            pbar.setRange(0, 100)
            pbar.setValue(percent)
            pbar.setFormat(f"{label}  %p%")

    def on_generation_done(self, success, message):
        # İlerleme çubuğunu tamamla/sıfırla (marquee'den determinate'e dön)
        """@brief Üretim bitince sonucu loglar ve arayüzü tekrar açar.
        
        @param success İşlem başarılı mı (bool)
        @param message Mesaj metni
        """
        pbar = getattr(self, "progressBar", None)
        if pbar is not None:
            pbar.setRange(0, 100)
            if success:
                pbar.setValue(100)
                pbar.setFormat("Tamamlandı  %p%")
            else:
                pbar.setValue(0)
                pbar.setFormat("Başarısız")
        # Tüm butonları geri etkinleştir ve etiketleri sıfırla
        for name, label in self._BTN_LABELS.items():
            btn = getattr(self, name, None)
            if btn:
                btn.setEnabled(True)
                btn.setText(label)
        if success:
            self.last_output = message
            # HTML üretildiyse tarayıcıda aç butonunu etkinleştir
            if message.lower().endswith(".html"):
                self.openBtn.setEnabled(True)
            self.log(f"\n✓ TAMAMLANDI: {message}")
        else:
            self.log(f"\n✗ {message}")

    def open_in_browser(self):
        """@brief Son üretilen çıktıyı varsayılan tarayıcıda açar.
        """
        if self.last_output and Path(self.last_output).exists():
            webbrowser.open(Path(self.last_output).as_uri())


def main():
    """@brief Uygulama giriş noktası (QApplication + MainWindow).
    """
    app = QtWidgets.QApplication(sys.argv)
    app.setStyle("Fusion")
    if ICON_FILE.exists():
        app.setWindowIcon(QtGui.QIcon(str(ICON_FILE)))
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
