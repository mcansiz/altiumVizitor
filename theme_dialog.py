"""
@file theme_dialog.py
@brief "Renk Temaları" diyaloğu: şematik ve PCB temalarını seç, kopyala,
       düzenle, KiCad JSON'u olarak içe / dışa aktar.

@details KiCad'in Tercihler → Renkler sayfasının karşılığı. Her sekmede
(Şematik / PCB) tema seçilir; seçilen tema üretilen HTML'in AÇILIŞ temasıdır
(tüm temalar HTML'e gömülür, tarayıcıda araç çubuğundan değiştirilebilir).

- Hazır temalar salt okunurdur; renge tıklanınca kopyası önerilir.
- Değişiklikler bellekte tutulur; dosyalar yalnız **Tamam**'da yazılır /
  silinir (İptal hiçbir şeyi değiştirmez).
- Önizleme, HTML'in kullandığı renklerle çizilir: şematikte okunurluk
  uyarlaması (`themes.sch_theme_readable`) uygulanmış haliyle.
"""
import json
from pathlib import Path

from PyQt5 import QtCore, QtGui, QtWidgets

import themes
from i18n import tr

ALTIUM = themes.ALTIUM_ID

# (anahtar yolu, Türkçe etiket) — sıra = listedeki sıra.
SCH_ROWS = [
    (("background",), "Arka plan"),
    (("wire",), "Teller"),
    (("bus",), "Veri yolları"),
    (("junction",), "Bağlantı noktaları"),
    (("component_outline",), "Sembol gövdesi dış hatları"),
    (("component_body",), "Sembol gövdesi dolguları"),
    (("pin",), "Pinler"),
    (("pin_name",), "Pin adları"),
    (("pin_number",), "Pin numaraları"),
    (("reference",), "Sembol referansları (designator)"),
    (("value",), "Sembol değerleri"),
    (("fields",), "Sembol alanları"),
    (("label_local",), "Etiketler"),
    (("label_global",), "Genel etiketler"),
    (("label_hier",), "Hiyerarşik etiketler"),
    (("sheet",), "Sayfa sembolü (blok) sınırları"),
    (("sheet_background",), "Sayfa sembolü (blok) dolgusu"),
    (("sheet_name",), "Sayfa sembolü adları"),
    (("sheet_filename",), "Sayfa sembolü dosya adları"),
    (("sheet_label",), "Sayfa pinleri"),
    (("no_connect",), "Bağlantısız işaretleri"),
    (("note",), "Notlar ve grafikler"),
    (("worksheet",), "Çizim sayfası (çerçeve)"),
]
BOARD_ROWS = [
    (("background",), "Arka plan"),
    (("edge_cuts",), "Board kenarı"),
    (("copper", "f"), "Üst bakır"),
    (("copper", "b"), "Alt bakır"),
] + [(("copper", f"in{i}"), "İç bakır {n}") for i in range(1, 15)] + [
    (("pad_through_hole",), "Delikli pad'ler (Multi-Layer)"),
    (("f_silks",), "Üst silkscreen"),
    (("b_silks",), "Alt silkscreen"),
    (("f_mask",), "Üst lehim maskesi"),
    (("b_mask",), "Alt lehim maskesi"),
    (("f_paste",), "Üst pasta"),
    (("b_paste",), "Alt pasta"),
    (("f_crtyd",), "Üst courtyard"),
    (("b_crtyd",), "Alt courtyard"),
    (("f_fab",), "Üst montaj (assembly)"),
    (("b_fab",), "Alt montaj (assembly)"),
    (("margin",), "Keepout"),
    (("dwgs_user",), "Ölçüler / çizimler"),
    (("cmts_user",), "Yorumlar"),
] + [((f"user_{i}",), "Mekanik {n}") for i in range(1, 10)]

# Yazı Tipleri sekmesi: (anahtar, başlık, açıklama)
FONT_ROWS = [
    ("sch", "Şematik yazıları",
     "Şema üzerindeki tüm yazılar: designator, değer, pin adı / numarası, net etiketi, notlar."),
    ("pcb", "PCB etiketleri",
     "Görüntüleyicinin çizdiği etiketler: pad numarası / net adı, ölçü, seçim etiketi. "
     "Silkscreen yazıları Altium'un çizdiği şekillerdir, değişmez."),
    ("ui", "Arayüz",
     "Paneller, araç çubukları, listeler ve açılır pencereler (şematik, PCB, 3D, birleşik görünüm)."),
]


def _row_label(text, keypath):
    """@brief Satır etiketini çevirir (numaralı satırlarda numarayı yerleştirir)."""
    num = "".join(ch for ch in keypath[-1] if ch.isdigit())
    return tr(text).format(n=num) if "{n}" in text else tr(text)


def qcolor(value, fallback="#808080"):
    """@brief Tema rengini QColor'a çevirir (alfa dahil)."""
    p = themes.parse_color(value) or themes.parse_color(fallback)
    c = QtGui.QColor(p[0], p[1], p[2])
    c.setAlphaF(p[3])
    return c


def _get(section_colors, keypath):
    """@brief Anahtar yoluyla renk okur (yoksa None)."""
    cur = section_colors or {}
    for k in keypath:
        if not isinstance(cur, dict):
            return None
        cur = cur.get(k)
    return cur if isinstance(cur, str) else None


def _set(section_colors, keypath, value):
    """@brief Anahtar yoluyla renk yazar (ara sözlükleri kurar)."""
    cur = section_colors
    for k in keypath[:-1]:
        cur = cur.setdefault(k, {})
    cur[keypath[-1]] = value


def swatch_icon(value, size=18):
    """@brief Renk kutucuğu ikonu (saydam renkte dama zemin üstünde)."""
    pm = QtGui.QPixmap(size * 2, size)
    pm.fill(QtCore.Qt.transparent)
    p = QtGui.QPainter(pm)
    if value:
        c = qcolor(value)
        if c.alphaF() < 0.999:
            s = 6
            for y in range(0, size, s):
                for x in range(0, size * 2, s):
                    p.fillRect(x, y, s, s, QtGui.QColor(
                        "#bbbbbb" if (x // s + y // s) % 2 else "#ffffff"))
        p.fillRect(0, 0, size * 2, size, c)
        p.setPen(QtGui.QColor("#555555"))
        p.drawRect(0, 0, size * 2 - 1, size - 1)
    else:
        p.setPen(QtGui.QPen(QtGui.QColor("#888888"), 1, QtCore.Qt.DashLine))
        p.drawRect(0, 0, size * 2 - 1, size - 1)
    p.end()
    return QtGui.QIcon(pm)


# ---------------------------------------------------------------------------
# Önizlemeler
# ---------------------------------------------------------------------------
class SchPreview(QtWidgets.QWidget):
    """@brief Şematik teması önizlemesi: küçük bir devre (op-amp, etiketler, blok)."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.colors = None
        self.setMinimumSize(360, 260)

    def set_colors(self, colors):
        """@param colors Okunurluk uyarlaması UYGULANMIŞ renkler ya da None (Altium)"""
        self.colors = colors
        self.update()

    def paintEvent(self, _ev):
        p = QtGui.QPainter(self)
        p.setRenderHint(QtGui.QPainter.Antialiasing)
        if not self.colors:
            p.fillRect(self.rect(), QtGui.QColor("#f0f0f0"))
            p.setPen(QtGui.QColor("#555555"))
            p.drawText(self.rect().adjusted(20, 0, -20, 0),
                       QtCore.Qt.AlignCenter | QtCore.Qt.TextWordWrap,
                       tr("Altium'daki özgün renkler kullanılır — renk teması uygulanmaz."))
            p.end()
            return
        C = lambda k: qcolor(self.colors.get(k))
        # 400 x 280 mantıksal alan → widget'a sığdır
        sx, sy = self.width() / 400, self.height() / 280
        sc = min(sx, sy)
        p.fillRect(self.rect(), C("background"))
        p.translate((self.width() - 400 * sc) / 2, (self.height() - 280 * sc) / 2)
        p.scale(sc, sc)
        f = QtGui.QFont("Arial", 7)
        p.setFont(f)

        def pen(k, w=1.2, style=QtCore.Qt.SolidLine):
            p.setPen(QtGui.QPen(C(k), w, style))

        def text(k, x, y, s, bold=False):
            ff = QtGui.QFont(f)
            ff.setBold(bold)
            p.setFont(ff)
            p.setPen(C(k))
            p.drawText(QtCore.QPointF(x, y), s)

        # çizim sayfası çerçevesi
        pen("worksheet", 1)
        p.setBrush(QtCore.Qt.NoBrush)
        p.drawRect(QtCore.QRectF(6, 6, 388, 268))
        p.drawLine(QtCore.QPointF(240, 274), QtCore.QPointF(240, 240))
        p.drawLine(QtCore.QPointF(240, 240), QtCore.QPointF(394, 240))
        text("worksheet", 246, 254, "Title: " + tr("Renk önizleme"))
        text("worksheet", 246, 267, "Rev: A   Sheet 1/1")
        # op-amp sembolü
        p.setBrush(C("component_body"))
        pen("component_outline", 1.4)
        tri = QtGui.QPolygonF([QtCore.QPointF(150, 70), QtCore.QPointF(150, 140),
                               QtCore.QPointF(210, 105)])
        p.drawPolygon(tri)
        p.setBrush(QtCore.Qt.NoBrush)
        pen("pin", 1.4)
        for y in (85, 125):
            p.drawLine(QtCore.QPointF(130, y), QtCore.QPointF(150, y))
        p.drawLine(QtCore.QPointF(210, 105), QtCore.QPointF(230, 105))
        text("pin_number", 134, 82, "3")
        text("pin_number", 134, 122, "2")
        text("pin_number", 216, 102, "6")
        text("pin_name", 153, 88, "+")
        text("pin_name", 153, 128, "−")
        text("reference", 172, 66, "U1", bold=True)
        text("value", 172, 152, "OPA604")
        text("fields", 172, 162, "SOIC-8")
        # teller + bağlantı noktası
        pen("wire", 1.6)
        p.drawLine(QtCore.QPointF(60, 85), QtCore.QPointF(130, 85))
        p.drawLine(QtCore.QPointF(100, 125), QtCore.QPointF(130, 125))
        p.drawLine(QtCore.QPointF(100, 125), QtCore.QPointF(100, 175))
        p.drawLine(QtCore.QPointF(100, 175), QtCore.QPointF(250, 175))
        p.drawLine(QtCore.QPointF(250, 175), QtCore.QPointF(250, 105))
        p.drawLine(QtCore.QPointF(230, 105), QtCore.QPointF(290, 105))
        p.setPen(QtCore.Qt.NoPen)
        p.setBrush(C("junction"))
        p.drawEllipse(QtCore.QPointF(250, 105), 3, 3)
        p.setBrush(QtCore.Qt.NoBrush)
        # veri yolu
        pen("bus", 3.5)
        p.drawLine(QtCore.QPointF(30, 205), QtCore.QPointF(200, 205))
        text("label_local", 40, 200, "DATA[0..7]")
        # etiketler
        text("label_local", 64, 81, "IN_P")
        pen("label_global", 1)
        gl = QtGui.QPolygonF([QtCore.QPointF(290, 105), QtCore.QPointF(298, 98),
                              QtCore.QPointF(350, 98), QtCore.QPointF(350, 112),
                              QtCore.QPointF(298, 112)])
        p.drawPolygon(gl)
        text("label_global", 302, 109, "VOUT")
        pen("label_hier", 1)
        p.drawRect(QtCore.QRectF(14, 79, 40, 12))
        text("label_hier", 17, 89, "SENSE")
        # bağlantısız işareti
        pen("no_connect", 1.4)
        p.drawLine(QtCore.QPointF(204, 199), QtCore.QPointF(216, 211))
        p.drawLine(QtCore.QPointF(216, 199), QtCore.QPointF(204, 211))
        pen("wire", 1.6)
        p.drawLine(QtCore.QPointF(200, 205), QtCore.QPointF(210, 205))
        # sayfa sembolü (blok)
        p.setBrush(qcolor(self.colors.get("sheet_background")))
        pen("sheet", 1.4)
        p.drawRect(QtCore.QRectF(300, 135, 80, 70))
        p.setBrush(QtCore.Qt.NoBrush)
        text("sheet_name", 300, 131, "U_Power")
        text("sheet_filename", 300, 216, "Power.SchDoc")
        text("sheet_label", 305, 160, "VIN")
        text("sheet_label", 305, 180, "GND")
        # not
        text("note", 20, 40, tr("Not: önizleme"))
        p.end()


class PcbPreview(QtWidgets.QWidget):
    """@brief PCB teması önizlemesi: bakır izler, pad'ler, via, silkscreen."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.board = None
        self.setMinimumSize(360, 260)

    def set_board(self, board):
        """@param board Normalize board renkleri"""
        self.board = board
        self.update()

    def paintEvent(self, _ev):
        p = QtGui.QPainter(self)
        p.setRenderHint(QtGui.QPainter.Antialiasing)
        b = self.board or themes.ALTIUM_BOARD
        cu = b.get("copper") or {}
        bg = b["background"]
        col = lambda v, fb: qcolor(v or fb)
        sc = min(self.width() / 400, self.height() / 280)
        p.fillRect(self.rect(), qcolor(bg))
        p.translate((self.width() - 400 * sc) / 2, (self.height() - 280 * sc) / 2)
        p.scale(sc, sc)
        fr4 = themes._shift_lightness(bg, 0.07 if themes.is_dark(bg) else -0.07)
        if self.board is None:
            fr4 = "#0e3b21"
        p.setBrush(qcolor(fr4))
        p.setPen(QtGui.QPen(col(b.get("edge_cuts"), "#c8b400"), 1.5))
        p.drawRoundedRect(QtCore.QRectF(20, 20, 360, 240), 8, 8)
        rnd = QtCore.Qt.RoundCap

        def track(c, pts, w=4):
            p.setPen(QtGui.QPen(c, w, QtCore.Qt.SolidLine, rnd, QtCore.Qt.RoundJoin))
            p.setBrush(QtCore.Qt.NoBrush)
            p.drawPolyline(QtGui.QPolygonF([QtCore.QPointF(x, y) for x, y in pts]))

        bot = col(cu.get("b"), "#4060e0")
        inn = col(cu.get("in1"), "#888888")
        top = col(cu.get("f"), "#e04040")
        track(bot, [(70, 230), (250, 230), (300, 180)], 5)
        track(inn, [(60, 60), (60, 200), (120, 200)], 3)
        track(top, [(110, 110), (200, 110), (240, 70), (330, 70)], 4)
        track(top, [(110, 150), (210, 150)], 4)
        # SMD pad'ler (üst bakır)
        p.setPen(QtCore.Qt.NoPen)
        p.setBrush(top)
        for y in (100, 140):
            p.drawRect(QtCore.QRectF(95, y, 16, 20))
            p.drawRect(QtCore.QRectF(205, y, 16, 20))
        # delikli pad'ler + via
        pad = col(b.get("pad_through_hole") or b.get("via_through"), "#d4a020")
        hole = qcolor(bg) if self.board else qcolor("#0b0b0b")
        for x in (300, 330, 360):
            p.setBrush(pad)
            p.drawEllipse(QtCore.QPointF(x, 180), 9, 9)
            p.setBrush(hole)
            p.drawEllipse(QtCore.QPointF(x, 180), 4, 4)
        p.setBrush(pad)
        p.drawEllipse(QtCore.QPointF(330, 70), 6, 6)
        p.setBrush(hole)
        p.drawEllipse(QtCore.QPointF(330, 70), 2.5, 2.5)
        # silkscreen + courtyard + montaj
        silk = col(b.get("f_silks"), "#e8e8e8")
        p.setBrush(QtCore.Qt.NoBrush)
        p.setPen(QtGui.QPen(silk, 1.2))
        p.drawRect(QtCore.QRectF(88, 92, 140, 76))
        f = QtGui.QFont("Arial", 9)
        f.setBold(True)
        p.setFont(f)
        p.drawText(QtCore.QPointF(90, 88), "U1")
        p.drawText(QtCore.QPointF(292, 205), "J1")
        p.setPen(QtGui.QPen(col(b.get("f_crtyd"), "#666666"), 0.8, QtCore.Qt.DashLine))
        p.drawRect(QtCore.QRectF(82, 86, 152, 88))
        bsilk = col(b.get("b_silks"), "#9a9a9a")
        p.setPen(QtGui.QPen(bsilk, 1))
        f.setBold(False)
        p.setFont(f)
        p.drawText(QtCore.QPointF(40, 250), "C7 (" + tr("alt") + ")")
        p.end()


# ---------------------------------------------------------------------------
# Diyalog
# ---------------------------------------------------------------------------
class ThemeDialog(QtWidgets.QDialog):
    """@brief Renk Temaları diyaloğu (bkz. dosya başı)."""

    SECTIONS = (("schematic", "Şematik"), ("board", "PCB"))

    def __init__(self, parent=None, sch_id=ALTIUM, pcb_id=ALTIUM, theme_dir=None, fonts=None):
        """@param sch_id / pcb_id Başlangıçta seçili (açılış) temaları
        @param theme_dir Kullanıcı tema klasörü (None = themes.user_theme_dir())
        @param fonts {"sch", "pcb", "ui"} başlangıç yazı tipleri ('' = özgün)"""
        super().__init__(parent)
        self.setWindowTitle(tr("Renk Temaları ve Yazı Tipleri"))
        self.resize(940, 680)
        self.theme_dir = Path(theme_dir) if theme_dir else themes.user_theme_dir()
        user, self.load_errors = themes.load_user_packs(self.theme_dir)
        self.packs = themes.builtin_packs() + user
        self.dirty = set()        # kaydedilecek kullanıcı temalarının id'leri
        self.deleted = []         # Tamam'da silinecek dosyalar
        self.ui = {}

        root = QtWidgets.QVBoxLayout(self)
        self.tabs = QtWidgets.QTabWidget()
        root.addWidget(self.tabs, 1)
        for sec, title in self.SECTIONS:
            self.tabs.addTab(self._build_page(sec), tr(title))
        self.tabs.addTab(self._build_font_page(fonts or {}), tr("Yazı Tipleri"))

        bar = QtWidgets.QHBoxLayout()
        self.copyBtn = QtWidgets.QPushButton(tr("Kopyala…"))
        self.copyBtn.setToolTip(tr("Seçili temanın düzenlenebilir bir kopyasını oluştur"))
        self.renameBtn = QtWidgets.QPushButton(tr("Yeniden Adlandır…"))
        self.deleteBtn = QtWidgets.QPushButton(tr("Sil"))
        self.importBtn = QtWidgets.QPushButton(tr("İçe Aktar…"))
        self.importBtn.setToolTip(tr("KiCad renk teması dosyası (.json) yükle"))
        self.exportBtn = QtWidgets.QPushButton(tr("Dışa Aktar…"))
        self.exportBtn.setToolTip(tr("Seçili temayı KiCad renk teması dosyası olarak kaydet (KiCad de açar)"))
        self.folderBtn = QtWidgets.QPushButton(tr("Tema Klasörünü Aç"))
        self.folderBtn.setToolTip(str(self.theme_dir))
        self.licenseBtn = QtWidgets.QPushButton(tr("Lisanslar…"))
        self.licenseBtn.setToolTip(tr("Hazır temaların kaynakları ve lisans bildirimleri"))
        for b in (self.copyBtn, self.renameBtn, self.deleteBtn, self.importBtn, self.exportBtn):
            bar.addWidget(b)
        bar.addStretch(1)
        bar.addWidget(self.licenseBtn)
        bar.addWidget(self.folderBtn)
        root.addLayout(bar)

        note = QtWidgets.QLabel(tr(
            "Seçili temalar üretilen HTML'lerin açılış temasıdır. Tüm temalar HTML'e "
            "gömülür; tarayıcıda araç çubuğundaki seçiciden değiştirilebilir."))
        note.setWordWrap(True)
        note.setStyleSheet("color:#777;")
        root.addWidget(note)
        if self.load_errors:
            warn = QtWidgets.QLabel(tr("Okunamayan tema dosyaları (atlandı): {a0}").format(
                a0=", ".join(n for n, _why in self.load_errors)))
            warn.setWordWrap(True)
            warn.setStyleSheet("color:#c62828;")
            root.addWidget(warn)
        box = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
        box.button(QtWidgets.QDialogButtonBox.Ok).setText(tr("Tamam"))
        box.button(QtWidgets.QDialogButtonBox.Cancel).setText(tr("İptal"))
        box.accepted.connect(self.accept)
        box.rejected.connect(self.reject)
        root.addWidget(box)

        self.copyBtn.clicked.connect(lambda: self.copy_current())
        self.renameBtn.clicked.connect(self.rename_current)
        self.deleteBtn.clicked.connect(self.delete_current)
        self.importBtn.clicked.connect(self.import_theme)
        self.exportBtn.clicked.connect(self.export_current)
        self.folderBtn.clicked.connect(self.open_folder)
        self.licenseBtn.clicked.connect(self.show_licenses)
        self.tabs.currentChanged.connect(lambda _i: self._update_buttons())

        self._fill_combo("schematic", sch_id)
        self._fill_combo("board", pcb_id)

    # --- kurulum ---------------------------------------------------------
    def _build_page(self, sec):
        page = QtWidgets.QWidget()
        lay = QtWidgets.QVBoxLayout(page)
        top = QtWidgets.QHBoxLayout()
        top.addWidget(QtWidgets.QLabel(tr("Tema:")))
        combo = QtWidgets.QComboBox()
        combo.setMinimumWidth(260)
        top.addWidget(combo, 1)
        lay.addLayout(top)
        info = QtWidgets.QLabel()
        info.setWordWrap(True)
        info.setStyleSheet("color:#777;")
        lay.addWidget(info)

        split = QtWidgets.QSplitter(QtCore.Qt.Horizontal)
        scroll = QtWidgets.QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        scroll.setMinimumWidth(300)
        holder = QtWidgets.QWidget()
        grid = QtWidgets.QGridLayout(holder)
        grid.setVerticalSpacing(2)
        rows = {}
        for r, (keypath, label) in enumerate(SCH_ROWS if sec == "schematic" else BOARD_ROWS):
            btn = QtWidgets.QToolButton()
            btn.setIconSize(QtCore.QSize(36, 18))
            btn.setAutoRaise(True)
            btn.clicked.connect(lambda _c=False, s=sec, k=keypath: self.edit_color(s, k))
            lab = QtWidgets.QLabel(_row_label(label, keypath))
            grid.addWidget(btn, r, 0)
            grid.addWidget(lab, r, 1)
            rows[keypath] = (btn, lab)
        grid.setColumnStretch(1, 1)
        grid.setRowStretch(len(rows), 1)
        scroll.setWidget(holder)
        split.addWidget(scroll)
        preview = SchPreview() if sec == "schematic" else PcbPreview()
        split.addWidget(preview)
        split.setStretchFactor(0, 0)
        split.setStretchFactor(1, 1)
        split.setSizes([330, 560])
        lay.addWidget(split, 1)
        combo.currentIndexChanged.connect(lambda _i, s=sec: self._show(s))
        self.ui[sec] = {"combo": combo, "rows": rows, "preview": preview, "info": info,
                        "scroll": scroll}
        return page

    def _fill_combo(self, sec, select_id):
        combo = self.ui[sec]["combo"]
        combo.blockSignals(True)
        combo.clear()
        combo.addItem(tr("Altium (orijinal)"), ALTIUM)
        for p in self.packs:
            if p.get(sec):
                label = p["name"] + ("  " + tr("(salt okunur)") if p["builtin"] else "")
                combo.addItem(label, p["id"])
        idx = combo.findData(select_id)
        combo.setCurrentIndex(idx if idx >= 0 else 0)
        combo.blockSignals(False)
        self._show(sec)

    # --- durum -----------------------------------------------------------
    def current_section(self):
        """@return "schematic" | "board" | None (Yazı Tipleri sekmesi)"""
        i = self.tabs.currentIndex()
        return self.SECTIONS[i][0] if 0 <= i < len(self.SECTIONS) else None

    def current_pack(self, sec=None):
        """@return seçili paket (Altium ya da Yazı Tipleri sekmesi = None)"""
        sec = sec or self.current_section()
        if sec is None:
            return None
        return themes.find(self.packs, self.ui[sec]["combo"].currentData())

    def selected_fonts(self):
        """@return {"sch", "pcb", "ui"} — seçilen aileler ('' = özgün)"""
        return {k: themes.clean_font(c.currentData()) for k, (c, _p) in self.font_ui.items()}

    def _build_font_page(self, fonts):
        """@brief Yazı Tipleri sekmesi: şematik / PCB etiketleri / arayüz."""
        page = QtWidgets.QWidget()
        lay = QtWidgets.QVBoxLayout(page)
        # Bu bilgisayardaki aileler + başka sistemlerde yaygın olanlar (HTML başka
        # bilgisayarda açılacaksa onlar da seçilebilsin)
        fams = sorted({f for f in QtGui.QFontDatabase().families() if themes.clean_font(f)}
                      | set(themes.HTML_FONT_CHOICES), key=str.lower)
        grid = QtWidgets.QGridLayout()
        grid.setColumnStretch(1, 1)
        self.font_ui = {}
        sample = "U1  OPA604  ·  NET_SDA  ·  R12 4k7  ·  0123456789"
        for r, (key, title, hint) in enumerate(FONT_ROWS):
            lab = QtWidgets.QLabel("<b>" + tr(title) + "</b>")
            combo = QtWidgets.QComboBox()
            combo.addItem(tr("Özgün yazı tipi"), "")
            cur = themes.clean_font(fonts.get(key))
            names = fams + ([cur] if cur and cur not in fams else [])
            for f in names:
                combo.addItem(f, f)
            idx = combo.findData(cur)
            combo.setCurrentIndex(idx if idx >= 0 else 0)
            prev = QtWidgets.QLabel(sample)
            prev.setMinimumHeight(28)
            h = QtWidgets.QLabel(tr(hint))
            h.setWordWrap(True)
            h.setStyleSheet("color:#777;")
            grid.addWidget(lab, r * 3, 0)
            grid.addWidget(combo, r * 3, 1)
            grid.addWidget(prev, r * 3 + 1, 1)
            grid.addWidget(h, r * 3 + 2, 1)
            grid.setRowMinimumHeight(r * 3 + 2, 30)

            def upd(_i=0, c=combo, pv=prev):
                f = QtGui.QFont(c.currentData() or self.font().family())
                f.setPointSize(12)
                pv.setFont(f)
            combo.currentIndexChanged.connect(upd)
            upd()
            self.font_ui[key] = (combo, prev)
        lay.addLayout(grid)
        note = QtWidgets.QLabel(tr(
            "Yazı tipi dosyası HTML'e gömülmez: HTML'i açan bilgisayarda o yazı tipi yoksa "
            "özgün yazı tipi kullanılır. Paylaşacağın HTML için Arial, Segoe UI, Consolas gibi "
            "yaygın yazı tiplerini seç. Şematik yazı tipi tarayıcıda araç çubuğundan da "
            "değiştirilebilir."))
        note.setWordWrap(True)
        note.setStyleSheet("color:#777;")
        lay.addWidget(note)
        lay.addStretch(1)
        return page

    def selected_ids(self):
        """@return (şematik açılış teması id, PCB açılış teması id)"""
        return (self.ui["schematic"]["combo"].currentData() or ALTIUM,
                self.ui["board"]["combo"].currentData() or ALTIUM)

    def _section_colors(self, sec, pack):
        if pack is None:
            return themes.ALTIUM_BOARD if sec == "board" else None
        return pack.get(sec)

    def _show(self, sec):
        ui = self.ui[sec]
        pack = self.current_pack(sec)
        colors = self._section_colors(sec, pack)
        ui["scroll"].setVisible(colors is not None)
        for keypath, (btn, lab) in ui["rows"].items():
            v = _get(colors, keypath)
            btn.setIcon(swatch_icon(v))
            btn.setToolTip(v or tr("Tanımsız — özgün renk kullanılır"))
            lab.setEnabled(bool(v))
        if pack is None:
            ui["info"].setText(
                tr("Altium'daki özgün renkler kullanılır — renk teması uygulanmaz.")
                if sec == "schematic" else
                tr("Görüntüleyicinin varsayılan renkleri (salt okunur). Listede olmayan katmanlar otomatik renk alır."))
        elif pack["builtin"]:
            ui["info"].setText(tr("Hazır tema (salt okunur). Düzenlemek için bir renge tıkla ya da Kopyala.")
                               + "  ·  " + " · ".join(x for x in (
                                   pack.get("license"), pack.get("copyright"),
                                   pack.get("source")) if x))
        else:
            where = str(pack["path"]) if pack.get("path") else tr("(henüz kaydedilmedi)")
            ui["info"].setText(tr("Kullanıcı teması · {a0}").format(a0=where))
        if sec == "schematic":
            ui["preview"].set_colors(themes.sch_theme_readable(colors) if colors else None)
        else:
            ui["preview"].set_board(pack["board"] if pack else None)
        self._update_buttons()

    def _update_buttons(self):
        sec = self.current_section()
        pack = self.current_pack(sec)
        user = bool(pack) and not pack["builtin"]
        self.copyBtn.setEnabled(sec is not None)
        self.renameBtn.setEnabled(user)
        self.deleteBtn.setEnabled(user)
        self.exportBtn.setEnabled(pack is not None)

    def _taken_ids(self):
        return {p["id"] for p in self.packs}

    def _refresh_combos(self, select=None):
        """@param select {bölüm: id} — verilmeyen bölümde mevcut seçim korunur"""
        select = select or {}
        for sec, _t in self.SECTIONS:
            cur = select.get(sec, self.ui[sec]["combo"].currentData())
            self._fill_combo(sec, cur)

    # --- eylemler --------------------------------------------------------
    def copy_current(self, ask_name=True):
        """@brief Seçili temanın düzenlenebilir kopyasını oluşturur.

        @param ask_name Ad sorulsun mu (renge tıklayınca önerilen kopyada sorulmaz)
        @return yeni paket ya da None (vazgeçildi)
        """
        sec = self.current_section()
        if sec is None:
            return None
        base = self.current_pack(sec)
        if base is None:
            base_name = tr("Altium (orijinal)")
            if sec == "board":
                sch, board = None, themes.ALTIUM_BOARD
            else:   # özgün renkler tema olarak ifade edilemez → KiCad'den başla
                sch, board = themes.find(self.packs, "kicad")["schematic"], None
        else:
            base_name, sch, board = base["name"], base.get("schematic"), base.get("board")
        name = tr("{a0} (kopya)").format(a0=base_name)
        if ask_name:
            name, ok = QtWidgets.QInputDialog.getText(
                self, tr("Temayı Kopyala"), tr("Yeni temanın adı:"), text=name)
            if not ok or not name.strip():
                return None
        new = themes.new_pack(name, sch, board, self._taken_ids(), self.theme_dir)
        self.packs.append(new)
        self.dirty.add(new["id"])
        self._refresh_combos({sec: new["id"]})
        return new

    def rename_current(self):
        pack = self.current_pack()
        if not pack or pack["builtin"]:
            return
        name, ok = QtWidgets.QInputDialog.getText(
            self, tr("Yeniden Adlandır"), tr("Temanın adı:"), text=pack["name"])
        if ok and name.strip():
            pack["name"] = themes.clean_name(name)
            self.dirty.add(pack["id"])
            self._refresh_combos()

    def delete_current(self):
        pack = self.current_pack()
        if not pack or pack["builtin"]:
            return
        ans = QtWidgets.QMessageBox.question(
            self, tr("Temayı Sil"),
            tr("“{a0}” teması silinsin mi? (Dosya Tamam'a basınca silinir.)").format(a0=pack["name"]))
        if ans != QtWidgets.QMessageBox.Yes:
            return
        self.packs.remove(pack)
        self.dirty.discard(pack["id"])
        if pack.get("path"):
            self.deleted.append(Path(pack["path"]))
        self._refresh_combos({sec: ALTIUM for sec, _t in self.SECTIONS
                              if self.ui[sec]["combo"].currentData() == pack["id"]})

    def import_theme(self):
        path, _f = QtWidgets.QFileDialog.getOpenFileName(
            self, tr("KiCad Renk Teması Yükle"), "",
            tr("KiCad renk teması (*.json);;Tüm dosyalar (*)"))
        if not path:
            return
        try:
            pack = themes.import_file(path, self._taken_ids(), self.theme_dir)
        except ValueError as e:
            msg = (tr("Dosya okunamadı (geçerli bir JSON değil).") if str(e) == "json" else
                   tr("Dosyada kullanılabilir şematik ya da PCB renk bölümü yok."))
            QtWidgets.QMessageBox.warning(self, tr("İçe Aktar"), msg)
            return
        self.packs.append(pack)
        self.dirty.add(pack["id"])
        sec = self.current_section() or "schematic"
        if not pack.get(sec):                       # yalnız diğer bölümü var
            sec = "board" if sec == "schematic" else "schematic"
            self.tabs.setCurrentIndex(0 if sec == "schematic" else 1)
        self._refresh_combos({sec: pack["id"]})

    def export_current(self):
        pack = self.current_pack()
        if pack is None:
            return
        stem = Path(pack["path"]).stem if pack.get("path") else themes.slugify(pack["name"])
        path, _f = QtWidgets.QFileDialog.getSaveFileName(
            self, tr("Temayı Dışa Aktar"), stem + ".json", tr("KiCad renk teması (*.json)"))
        if not path:
            return
        try:
            Path(path).write_text(json.dumps(themes.pack_to_kicad(pack), indent=2,
                                             ensure_ascii=False), encoding="utf-8")
        except OSError as e:
            QtWidgets.QMessageBox.warning(self, tr("Dışa Aktar"), str(e))

    def open_folder(self):
        try:
            self.theme_dir.mkdir(parents=True, exist_ok=True)
        except OSError:
            pass
        QtGui.QDesktopServices.openUrl(QtCore.QUrl.fromLocalFile(str(self.theme_dir)))

    def show_licenses(self):
        """@brief Hazır temaların kaynak / telif / lisans bildirimini gösterir."""
        dlg = QtWidgets.QDialog(self)
        dlg.setWindowTitle(tr("Tema Lisansları"))
        dlg.resize(760, 560)
        lay = QtWidgets.QVBoxLayout(dlg)
        txt = QtWidgets.QPlainTextEdit(themes.notices_text())
        txt.setReadOnly(True)
        txt.setFont(QtGui.QFontDatabase.systemFont(QtGui.QFontDatabase.FixedFont))
        lay.addWidget(txt)
        box = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Close)
        box.button(QtWidgets.QDialogButtonBox.Close).setText(tr("Kapat"))
        box.rejected.connect(dlg.reject)
        lay.addWidget(box)
        dlg.exec_()

    def edit_color(self, sec, keypath):
        """@brief Bir rengi QColorDialog ile değiştirir (hazır temada önce kopya önerir)."""
        if self.current_section() != sec:
            return
        pack = self.current_pack(sec)
        if pack is None or pack["builtin"]:
            name = pack["name"] if pack else tr("Altium (orijinal)")
            ans = QtWidgets.QMessageBox.question(
                self, tr("Salt Okunur Tema"),
                tr("“{a0}” hazır bir tema ve salt okunur.\nDüzenlemek için kopyası oluşturulsun mu?")
                .format(a0=name))
            if ans != QtWidgets.QMessageBox.Yes:
                return
            pack = self.copy_current(ask_name=False)
            if pack is None:
                return
        colors = pack[sec]
        cur = _get(colors, keypath) or "#808080"
        opts = QtWidgets.QColorDialog.ShowAlphaChannel
        label = _row_label(dict(SCH_ROWS + BOARD_ROWS).get(keypath, ""), keypath)
        c = QtWidgets.QColorDialog.getColor(qcolor(cur), self, label, opts)
        if not c.isValid():
            return
        val = themes.format_color((c.red(), c.green(), c.blue(), round(c.alphaF(), 3)))
        if keypath == ("background",) and not themes._th_rgb(val):
            val = themes.format_color((c.red(), c.green(), c.blue(), 1.0))  # zemin opak olmalı
        _set(colors, keypath, val)
        if keypath == ("background",):
            pack["dark"] = themes.is_dark(val)
        self.dirty.add(pack["id"])
        self._show(sec)

    def accept(self):
        """@brief Değişiklikleri diske yazar; hata olursa diyalog açık kalır."""
        try:
            for f in self.deleted:
                if f.exists():
                    f.unlink()
            self.deleted = []
            remap = {}
            for p in self.packs:
                if p["id"] in self.dirty and not p["builtin"]:
                    old = p["id"]
                    path = themes.save_pack(p, self.theme_dir)
                    p["id"] = themes.user_id(path.stem)
                    remap[old] = p["id"]
            self.dirty.clear()
        except OSError as e:
            QtWidgets.QMessageBox.warning(self, tr("Renk Temaları"),
                                          tr("Tema kaydedilemedi: {a0}").format(a0=e))
            return
        if remap:
            sel = {sec: remap.get(self.ui[sec]["combo"].currentData(),
                                  self.ui[sec]["combo"].currentData())
                   for sec, _t in self.SECTIONS}
            self._refresh_combos(sel)
        super().accept()
