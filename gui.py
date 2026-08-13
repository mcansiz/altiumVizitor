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

# --- Bağımlılık kapısı ----------------------------------------------------
# HİÇBİR üçüncü-parti import'tan ÖNCE çalışmalı (PyQt5 dahil): eksik paket
# durumunda kullanıcı, anlaşılmaz bir ImportError traceback'i yerine hangi
# kütüphanenin eksik olduğunu ve kurulum komutunu gören açık bir mesaj alsın.
# Eksik/uyumsuz paket varsa uygulama BAŞLAMAZ (mesaj + diyalog + çıkış kodu 1).
import deps
deps.enforce(gui=True)

from PyQt5 import QtWidgets, QtCore, QtGui, uic
from PyQt5.QtCore import QT_VERSION_STR, PYQT_VERSION_STR

import i18n
from i18n import tr
from viewer import (generate_viewer, generate_json,
                    generate_bom_csv, generate_pnp_csv,
                    generate_ic_map_xlsx, generate_mcu_pinout_xlsx,
                    generate_pcb_viewer,
    generate_pcb_canvas_viewer, generate_combined_viewer,
                    APP_VERSION)


def collect_versions() -> dict:
    """@brief Çalışma ortamının sürüm bilgilerini topla (debug/destek için).
    
    @return Üretilen sonuç.
    """
    info = {
        tr("Uygulama"): APP_VERSION,
        "Python": platform.python_version(),
        tr("İşletim Sistemi"): f"{platform.system()} {platform.release()}",
        "Qt": QT_VERSION_STR,
        "PyQt5": PYQT_VERSION_STR,
    }
    # Bağımlılıkların sürümleri — TEK KAYNAK deps.DEPENDENCIES (bkz. deps.py).
    # Sorunlu paketlerde sürümün yanına durumu da yazılır; normalde eksik paketle
    # uygulama hiç açılmaz, ama SCHVIZ_SKIP_DEP_CHECK ile atlanmışsa burada görünür.
    for dist, ver, durum, _purpose, _direct in deps.status_table():
        if dist == "PyQt5":
            continue  # yukarıda PYQT_VERSION_STR ile zaten listelendi
        info[dist] = ver if durum == "tamam" else f"{ver}  ({tr(durum)})"
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
                 fast_pcb=False, parent=None):
        """@brief __init__()

        @param mode Üretim modu (html/json/bom/pnp/icmap/mcupin/pcbview/combined)
        @param project_path Altium proje dosyası (.PrjPcb) yolu
        @param output_path Çıktı dosyası yolu
        @param inter_color Sayfalar arası bağlantı rengi (hex)
        @param intra_color Sayfa içi bağlantı rengi (hex)
        @param main_designators Ana işlemci designator listesi
        @param min_pins Minimum pin sayısı eşiği
        @param exclude_prefixes IC haritasından hariç tutulacak designator önekleri ("J,P,TP")
        @param fast_pcb Birleşik görünümde PCB paneli geometri (canvas) olsun mu
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
        self.fast_pcb = fast_pcb

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
                    self.done_signal.emit(False, tr("BOM verisi yok"))
                    return
            elif self.mode == "pnp":
                ok = generate_pnp_csv(
                    project_path=self.project_path,
                    output_path=self.output_path,
                    log=lambda msg: self.log_signal.emit(msg),
                )
                if not ok:
                    self.done_signal.emit(
                        False, tr("Pick&Place verisi yok (PCB gerekli)"))
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
                    self.done_signal.emit(
                        False, tr("IC haritası üretilemedi (netlist yok)"))
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
                        False,
                        tr("MCU pin listesi üretilemedi "
                           "(MCU designator gir / netlist yok)"))
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
                        False,
                        tr("PCB görüntüleyici üretilemedi "
                           "(PCB dosyası yok/okunamadı)"))
                    return
            elif self.mode == "pcbgeo":
                ok = generate_pcb_canvas_viewer(
                    project_path=self.project_path,
                    output_path=self.output_path,
                    log=lambda msg: self.log_signal.emit(msg),
                    progress=emit_progress,
                )
                if not ok:
                    self.done_signal.emit(
                        False,
                        tr("PCB (geometri) görüntüleyici üretilemedi "
                           "(PCB dosyası yok/okunamadı)"))
                    return
            elif self.mode == "combined":
                ok = generate_combined_viewer(
                    project_path=self.project_path,
                    output_path=self.output_path,
                    inter_sheet_color=self.inter_color,
                    intra_sheet_color=self.intra_color,
                    log=lambda msg: self.log_signal.emit(msg),
                    progress=emit_progress,
                    fast_pcb=self.fast_pcb,
                )
                if not ok:
                    self.done_signal.emit(
                        False, tr("Birleşik görünüm üretilemedi"))
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
            elif self.mode in ("pcbview", "pcbgeo"):
                final_out = str(Path(self.output_path).with_suffix(".html"))
            elif self.mode == "combined":
                final_out = str(Path(self.output_path).with_suffix(".html"))
            self.done_signal.emit(True, final_out)
        except Exception as e:
            tb = traceback.format_exc()
            self.log_signal.emit(tr("\nHATA: {hata}\n{iz}").format(hata=e, iz=tb))
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
QMenuBar { background: #15171c; color: #d4d9e0; border-bottom: 1px solid #2a2f38; }
QMenuBar::item { background: transparent; padding: 6px 11px; border-radius: 6px; }
QMenuBar::item:selected { background: #2a303b; color: #e9eef4; }
QMenuBar::item:pressed { background: #1f8a66; color: #f0fff8; }
QMenu { background: #21252e; color: #d4d9e0; border: 1px solid #2f3540;
  border-radius: 8px; padding: 5px; }
QMenu::item { padding: 6px 26px 6px 22px; border-radius: 5px; }
QMenu::item:selected { background: #2c7a62; color: #ffffff; }
QMenu::item:disabled { color: #5a616c; }
QMenu::separator { height: 1px; background: #2f3540; margin: 5px 8px; }
QMenu::indicator { width: 13px; height: 13px; left: 6px; }
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

        # Kalıcı ayarlar (son açılan proje klasörü vb.) — Windows'ta registry,
        # Linux/macOS'ta ini dosyası; yol ayracı OS'a göre çözülür.
        self.settings = QtCore.QSettings("SchematicViz", "SchematicViz")

        # --- Dil altyapısı ------------------------------------------------
        # gui.ui'den gelen metinler HENÜZ TÜRKÇEYKEN yedeklenir; dil her
        # değiştiğinde çeviri bu kaynak yedekten yeniden uygulanır (İngilizceye
        # çevrilmiş metin bir sonraki geçişte katalog anahtarı olarak
        # bulunamayacağı için doğrudan yerinde çeviri geri dönüşü engellerdi).
        # Renk butonlarının metni bir ETİKET değil VERİDİR (seçili hex kodu) —
        # yedeğe alınırsa dil değişiminde kullanıcının seçtiği rengi ezerdi.
        self._ui_snapshot = i18n.snapshot_widgets(
            self, exclude=("interColorBtn", "intraColorBtn"))
        self._menu_texts = []   # [(QAction|QMenu, kaynak_metin), ...]
        self._menu_tips = []    # [(QAction, kaynak_ipucu), ...]

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
        pcbgeo_btn = getattr(self, "pcbGeoBtn", None)
        if pcbgeo_btn is not None:
            pcbgeo_btn.clicked.connect(self.generate_pcbgeo_action)
        combined_btn = getattr(self, "combinedBtn", None)
        if combined_btn is not None:
            combined_btn.clicked.connect(self.generate_combined_action)

        # "Hakkında / Sürümler" butonu (varsa bağla, yoksa sessiz geç)
        about_btn = getattr(self, "aboutBtn", None)
        if about_btn is not None:
            about_btn.clicked.connect(self.show_about)

        # Üst menü çubuğu (butonlarla aynı eylemler + klavye kısayolları + dil)
        self._build_menu()

        # Kayıtlı dili uygula (yoksa kaynak dil: Türkçe → mevcut davranış)
        saved_lang = self.settings.value("language", i18n.SOURCE_LANGUAGE, type=str)
        self.set_language(saved_lang, persist=False)

    # === Menü çubuğu ===
    def _add_action(self, menu, text, slot, shortcut=None, tip=None,
                    checkable=False, checked=False):
        """@brief Menüye eylem ekler ve metnini dil yedeğine kaydeder.

        @param menu Hedef QMenu
        @param text Türkçe kaynak metin (çeviri anahtarı)
        @param slot Tetiklendiğinde çağrılacak fonksiyon (None = bağlama yok)
        @param shortcut Klavye kısayolu (ör. "Ctrl+O")
        @param tip Durum çubuğu ipucu (Türkçe kaynak metin)
        @param checkable Eylem işaretlenebilir mi
        @param checked İlk işaret durumu
        @return Oluşturulan QAction.
        """
        act = QtWidgets.QAction(tr(text), self)
        if shortcut:
            act.setShortcut(QtGui.QKeySequence(shortcut))
        if checkable:
            act.setCheckable(True)
            act.setChecked(checked)
        if tip:
            act.setStatusTip(tr(tip))
            self._menu_tips.append((act, tip))
        if slot is not None:
            act.triggered.connect(slot)
        menu.addAction(act)
        self._menu_texts.append((act, text))
        return act

    def _add_menu(self, parent, text):
        """@brief Menü (veya alt menü) ekler ve başlığını dil yedeğine kaydeder.

        @param parent Üst QMenuBar / QMenu
        @param text Türkçe kaynak başlık
        @return Oluşturulan QMenu.
        """
        menu = parent.addMenu(tr(text))
        self._menu_texts.append((menu, text))
        return menu

    def _build_menu(self):
        """@brief Üst menü çubuğunu kurar (Dosya / Üret / Ayarlar / Yardım).

        @details Menü eylemleri mevcut buton slotlarını yeniden kullanır; üretim
        eylemleri `self._menu_action_items` listesinde tutulur ve üretim sırasında
        butonlarla birlikte devre dışı bırakılır.
        """
        bar = self.menuBar()

        # --- Dosya ---
        file_menu = self._add_menu(bar, "&Dosya")
        self._add_action(file_menu, "Proje &Aç…", self.browse_project, "Ctrl+O",
                         tip="Proje dosyası seç (Ctrl+O)")
        self._add_action(file_menu, "Çı&ktı Yolu Seç…", self.browse_output, "Ctrl+S")
        file_menu.addSeparator()
        self.openOutputAct = self._add_action(
            file_menu, "Son Çıktıyı Tarayıcıda Aç", self.open_in_browser, "Ctrl+B")
        self.openOutputAct.setEnabled(False)
        self._add_action(file_menu, "Çıktı Klasörünü Aç", self.open_output_folder)
        file_menu.addSeparator()
        self._add_action(file_menu, "Log'u Temizle", self.clear_log)
        file_menu.addSeparator()
        self._add_action(file_menu, "Çıkış", self.close, "Ctrl+Q",
                         tip="Uygulamadan çık")

        # --- Üret --- (butonlarla aynı eylemler, kısayollu)
        gen_menu = self._add_menu(bar, "&Üret")
        self._menu_action_items = [
            self._add_action(gen_menu, "Şematik Viewer", self.generate, "Ctrl+1"),
            self._add_action(gen_menu, "PCB Görüntüleyici",
                             self.generate_pcbview_action, "Ctrl+2"),
            self._add_action(gen_menu, "PCB Hızlı (geometri)",
                             self.generate_pcbgeo_action, "Ctrl+3"),
            self._add_action(gen_menu, "Şematik + PCB + 3D  ★",
                             self.generate_combined_action, "Ctrl+4"),
        ]
        gen_menu.addSeparator()
        self._menu_action_items += [
            self._add_action(gen_menu, "MCU Pin Listesi (Excel)",
                             self.generate_mcupin_action),
            self._add_action(gen_menu, "IC Bağlantı Haritası (Excel)",
                             self.generate_icmap_action),
            self._add_action(gen_menu, "BOM (CSV)", self.generate_bom_action),
            self._add_action(gen_menu, "Pick && Place (CSV)", self.generate_pnp_action),
            self._add_action(gen_menu, "JSON (AI / LLM için)",
                             self.generate_json_action),
        ]

        # --- Ayarlar ---
        set_menu = self._add_menu(bar, "&Ayarlar")
        lang_menu = self._add_menu(set_menu, "Dil / Language")
        self._lang_group = QtWidgets.QActionGroup(self)
        self._lang_group.setExclusive(True)
        self._lang_actions = {}
        for code, name in i18n.LANGUAGES.items():
            # Dil adları çevrilmez: her dil kendi adıyla yazılır (Türkçe/English)
            act = QtWidgets.QAction(name, self)
            act.setCheckable(True)
            act.setData(code)
            act.triggered.connect(lambda _checked, c=code: self.set_language(c))
            self._lang_group.addAction(act)
            lang_menu.addAction(act)
            self._lang_actions[code] = act

        set_menu.addSeparator()
        self._add_action(set_menu, "Sayfalar Arası Renk…",
                         lambda: self.pick_color("inter"))
        self._add_action(set_menu, "Sayfa İçi Renk…",
                         lambda: self.pick_color("intra"))
        set_menu.addSeparator()
        fast_chk = getattr(self, "fastPcbCheck", None)
        self.fastPcbAct = self._add_action(
            set_menu, "Birleşikte Hızlı PCB Kullan (geometri)", None,
            checkable=True,
            checked=bool(fast_chk is not None and fast_chk.isChecked()))
        # Menü ↔ kutucuk çift yönlü senkron (tek durum, iki giriş noktası)
        if fast_chk is not None:
            self.fastPcbAct.toggled.connect(fast_chk.setChecked)
            fast_chk.toggled.connect(self.fastPcbAct.setChecked)
        else:
            self.fastPcbAct.setEnabled(False)

        # --- Yardım ---
        help_menu = self._add_menu(bar, "&Yardım")
        self._add_action(help_menu, "Hakkında / Sürümler", self.show_about, "F1")
        self._add_action(help_menu, "Sürümleri Panoya Kopyala", self.copy_versions)
        self._add_action(help_menu, "Bağımlılık Durumu", self.show_dependencies)

    # === Dil ===
    def set_language(self, code, persist=True):
        """@brief Arayüz dilini değiştirir ve tüm metinleri yeniden çevirir.

        @param code Dil kodu ("tr" | "en")
        @param persist Seçim QSettings'e kaydedilsin mi (açılışta kaydı uygularken False)
        """
        code = i18n.set_language(code)
        if persist:
            self.settings.setValue("language", code)
        # Dil menüsündeki işareti seçime eşitle (menüden gelmeyen çağrılar için)
        act = getattr(self, "_lang_actions", {}).get(code)
        if act is not None and not act.isChecked():
            act.setChecked(True)
        self.retranslate_ui()

    def retranslate_ui(self):
        """@brief Tüm arayüz metinlerini etkin dile göre yeniden yazar.

        @details gui.ui widget'ları kaynak yedekten (`_ui_snapshot`), menü
        öğeleri `_menu_texts`/`_menu_tips` listelerinden çevrilir. Üretim
        sırasında "Üretiliyor..." yazan buton bozulmasın diye aktif buton
        etiketleri yalnız üretim yokken sıfırlanır.
        """
        i18n.apply_snapshot(self._ui_snapshot)
        for obj, source in self._menu_texts:
            if isinstance(obj, QtWidgets.QMenu):
                obj.setTitle(tr(source))
            else:
                obj.setText(tr(source))
        for act, source in self._menu_tips:
            act.setStatusTip(tr(source))
        # Üretim sürüyorsa aktif butonun "Üretiliyor..." etiketini koru
        if self.worker is not None and self.worker.isRunning():
            active = getattr(self, self._MODE_BTN.get(
                getattr(self, "_current_mode", ""), ""), None)
            if active is not None:
                active.setText(tr("Üretiliyor..."))
        self._update_status_bar()

    def _update_status_bar(self):
        """@brief Alt durum çubuğundaki kalıcı sürüm/dil özetini yazar.
        """
        sb = self.statusBar()
        py = platform.python_version()
        sb.showMessage(
            f"v{APP_VERSION}  ·  Python {py}  ·  PyQt5 {PYQT_VERSION_STR}  "
            f"·  altium_monkey {self._am_version()}"
            f"  ·  {tr('Dil: {ad}').format(ad=i18n.LANGUAGES[i18n.language()])}"
            f"							coded by Mcansız"
        )

    # === Hakkında diyaloğu ===
    def show_about(self):
        """@brief Hakkında / sürüm bilgisi diyaloğunu açar.
        """
        box = QtWidgets.QMessageBox(self)
        box.setWindowTitle(tr("Hakkında / Sürüm Bilgisi"))
        box.setIcon(QtWidgets.QMessageBox.Information)
        box.setText(f"Schematic Viz Generator  v{APP_VERSION}")
        box.setInformativeText(
            tr("Altium şematik projelerini interaktif HTML viewer'a ve "
               "AI analizine uygun JSON'a dönüştürür.")
            + "\n\rDesign by Mikail Cansız"
        )
        # Sürüm listesini monospace detay bölümünde göster
        box.setDetailedText(versions_text())
        # Kopyalama için detayları açıkça öner
        copy_btn = box.addButton(tr("Sürümleri Kopyala"),
                                 QtWidgets.QMessageBox.ActionRole)
        box.addButton(QtWidgets.QMessageBox.Ok)
        box.exec_()
        if box.clickedButton() == copy_btn:
            self.copy_versions()

    def copy_versions(self):
        """@brief Sürüm listesini panoya kopyalar (Yardım menüsü + Hakkında diyaloğu).
        """
        QtWidgets.QApplication.clipboard().setText(versions_text())
        self.log(tr("✓ Sürüm bilgisi panoya kopyalandı."))

    def show_dependencies(self):
        """@brief Kurulu bağımlılıkları durumlarıyla birlikte log paneline yazar.
        """
        rows = deps.status_table()
        self.log("")
        self.log(tr("Bağımlılıklar ({sayi} paket):").format(sayi=len(rows)))
        for dist, ver, durum, purpose, direct in rows:
            mark = "✓" if durum == "tamam" else "✗"
            kind = tr("doğrudan") if direct else tr("alt bağımlılık")
            self.log(f"  {mark} {dist:<16s} {ver:<14s} {tr(durum):<22s} "
                     f"[{kind}]  {purpose}")

    def clear_log(self):
        """@brief Log panelini temizler.
        """
        self.logEdit.clear()

    def open_output_folder(self):
        """@brief Son üretilen çıktının bulunduğu klasörü dosya yöneticisinde açar.
        """
        target = self.last_output or self.outputPathEdit.text().strip()
        folder = Path(target).parent if target else None
        if not folder or not folder.is_dir():
            QtWidgets.QMessageBox.information(
                self, tr("Çıktı klasörü yok"),
                tr("Henüz üretilmiş bir çıktı yok (veya dosya taşınmış)."))
            return
        QtGui.QDesktopServices.openUrl(
            QtCore.QUrl.fromLocalFile(str(folder)))

    # === Proje seçimi ===
    def _last_project_dir(self) -> str:
        """@brief Proje "Gözat" diyaloğunun açılacağı klasörü belirler.

        @details Önce alandaki mevcut proje yolunun klasörü, sonra en son
        seçilen klasör (QSettings), o da yoksa kullanıcının ev dizini kullanılır.
        Var olmayan (ör. silinmiş/taşınmış) klasörler atlanır.

        @return Diyaloğun başlangıç klasörü.
        """
        current = self.projectPathEdit.text().strip()
        if current:
            parent = Path(current).parent
            if parent.is_dir():
                return str(parent)
        saved = self.settings.value("lastProjectDir", "", type=str)
        if saved and Path(saved).is_dir():
            return saved
        return str(Path.home())

    def browse_project(self):
        """@brief Dosya diyaloğuyla Altium projesi seçer ve şemaları listeler.
        """
        path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self,
            tr("Altium proje dosyası seç"),
            self._last_project_dir(),
            tr("Altium Project (*.PrjPcb *.PrjPCB);;Tüm Dosyalar (*)"),
        )
        if not path:
            return
        # Bir sonraki "Gözat"ta aynı klasörden başla
        self.settings.setValue("lastProjectDir", str(Path(path).parent))
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
            self.log(tr("✓ Proje açıldı, {sayi} şema bulundu.").format(sayi=len(paths)))
        except Exception as e:
            self.log(tr("✗ Proje açılamadı: {hata}").format(hata=e))
            QtWidgets.QMessageBox.critical(
                self, tr("Proje yükleme hatası"),
                tr("Proje dosyası açılırken hata:\n\n{hata}").format(hata=e)
            )

    # === Çıktı seçimi ===
    def browse_output(self):
        """@brief Çıktı dosyası yolunu seçtirir.
        """
        suggested = self.outputPathEdit.text() or "schematic_viz.html"
        path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self, tr("Çıktı yolunu seç"), suggested,
            tr("HTML (*.html);;Tüm Dosyalar (*)")
        )
        if path:
            self.outputPathEdit.setText(path)

    # === Renk seçici ===
    def pick_color(self, which):
        """@brief Renk seçiciyi açar ve ilgili butonu günceller.
        
        @param which Hedef seçici
        """
        current = self.inter_color if which == "inter" else self.intra_color
        title = tr("Sayfalar arası bağlantı rengi") if which == "inter" \
            else tr("Sayfa içi bağlantı rengi")
        color = QtWidgets.QColorDialog.getColor(
            QtGui.QColor(current), self, title
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

    def generate_pcbgeo_action(self):
        """@brief Geometri tabanlı (canvas) PCB görüntüleyici üretimini başlatır.

        SVG katmanları yerine ham geometri gömülür: dosya ~3-15x küçük,
        her zoom seviyesinde akıcı.
        """
        self._start_generation(mode="pcbgeo")

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
                self, tr("MCU gerekli"),
                tr("MCU pin listesi için 'MCU / Ana İşlemci' kutusuna MCU "
                   "designator'ını yaz (örn. U2)."))
            return
        # Tek MCU bekleniyor — virgüllüyse ilkini al
        if "," in mcu:
            QtWidgets.QMessageBox.information(
                self, tr("Tek MCU"),
                tr("MCU pin listesi tek entegre içindir. İlk designator "
                   "kullanılacak: {desig}").format(desig=mcu.split(",")[0].strip()))
        self._start_generation(mode="mcupin")

    def _all_action_buttons(self):
        """@brief Üretim sırasında devre dışı bırakılacak butonlar.
        
        @return Üretilen sonuç.
        """
        names = ["generateBtn", "generateJsonBtn", "bomBtn", "pnpBtn",
                 "icmapBtn", "mcuPinBtn", "pcbViewerBtn", "pcbGeoBtn",
                 "combinedBtn"]
        return [getattr(self, n) for n in names if getattr(self, n, None)]

    ## @brief Buton adı → gui.ui'deki KAYNAK (Türkçe) etiket.
    #  Üretim bitince etiketler buradan `tr()` ile geri yazılır; değerler
    #  gui.ui ile BİREBİR aynı olmalı (aksi halde etiket üretimden sonra değişir).
    _BTN_LABELS = {
        "generateBtn": "Şematik Viewer üret",
        "generateJsonBtn": "JSON (AI / LLM için)",
        "bomBtn": "BOM (CSV)",
        "pnpBtn": "Pick && Place (CSV)",
        "icmapBtn": "IC Bağlantı Haritası (Excel)",
        "mcuPinBtn": "MCU Pin Listesi (Excel)",
        "pcbViewerBtn": "PCB Görüntüleyici üret",
        "pcbGeoBtn": "PCB Hızlı (geometri) üret",
        "combinedBtn": "Şematik + PCB + 3D hepsini üret",
    }
    _MODE_BTN = {
        "html": "generateBtn",
        "json": "generateJsonBtn",
        "bom": "bomBtn",
        "pnp": "pnpBtn",
        "icmap": "icmapBtn",
        "mcupin": "mcuPinBtn",
        "pcbview": "pcbViewerBtn",
        "pcbgeo": "pcbGeoBtn",
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
                self, tr("Eksik"), tr("Önce geçerli bir proje dosyası seç.")
            )
            return
        if not output_path:
            QtWidgets.QMessageBox.warning(
                self, tr("Eksik"), tr("Çıktı yolunu belirt.")
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
        elif mode == "pcbgeo":
            base = Path(output_path)
            output_path = str(base.with_name(base.stem + "_PCB_hizli").with_suffix(".html"))
        elif mode == "combined":
            base = Path(output_path)
            output_path = str(base.with_name(base.stem + "_Birlesik").with_suffix(".html"))

        self.logEdit.clear()
        self.log(f"Schematic Viz v{APP_VERSION}  ·  Python {platform.python_version()}"
                 f"  ·  altium_monkey {self._am_version()}")
        self.log("-" * 60)

        # Tüm butonları (ve aynı işi yapan menü eylemlerini) devre dışı bırak,
        # aktif mod butonuna "Üretiliyor..." yaz
        for btn in self._all_action_buttons():
            btn.setEnabled(False)
        for act in getattr(self, "_menu_action_items", []):
            act.setEnabled(False)
        active_btn = getattr(self, self._MODE_BTN.get(mode, "generateBtn"), None)
        if active_btn:
            active_btn.setText(tr("Üretiliyor..."))
        self._set_open_enabled(False)
        self._current_mode = mode

        # İlerleme çubuğunu sıfırla ve göster
        pbar = getattr(self, "progressBar", None)
        if pbar is not None:
            pbar.setRange(0, 100)
            pbar.setValue(0)
            pbar.setFormat(tr("Başlatılıyor… %p%"))
            pbar.setVisible(True)

        fast_chk = getattr(self, "fastPcbCheck", None)
        self.worker = GeneratorThread(
            mode, project_path, output_path,
            inter_color=self.inter_color, intra_color=self.intra_color,
            main_designators=main_desigs or None, min_pins=min_pins,
            exclude_prefixes=exclude_prefixes or None,
            fast_pcb=bool(fast_chk is not None and fast_chk.isChecked()),
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
                pbar.setFormat(tr("Tamamlandı  %p%"))
            else:
                pbar.setValue(0)
                pbar.setFormat(tr("Başarısız"))
        # Tüm butonları geri etkinleştir ve etiketleri (etkin dilde) sıfırla
        for name, label in self._BTN_LABELS.items():
            btn = getattr(self, name, None)
            if btn:
                btn.setEnabled(True)
                btn.setText(tr(label))
        for act in getattr(self, "_menu_action_items", []):
            act.setEnabled(True)
        if success:
            self.last_output = message
            # HTML üretildiyse tarayıcıda aç butonunu etkinleştir
            if message.lower().endswith(".html"):
                self._set_open_enabled(True)
            self.log(tr("\n✓ TAMAMLANDI: {yol}").format(yol=message))
        else:
            self.log(f"\n✗ {message}")

    def _set_open_enabled(self, enabled):
        """@brief "Son çıktıyı tarayıcıda aç" buton ve menü eylemini birlikte ayarlar.

        @param enabled Etkin mi (bool)
        """
        self.openBtn.setEnabled(enabled)
        act = getattr(self, "openOutputAct", None)
        if act is not None:
            act.setEnabled(enabled)

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
