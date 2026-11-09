"""
@file themes.py
@brief Renk teması paketleri: KiCad tema JSON'u ile uyumlu yükleme, doğrulama,
       kullanıcı tema klasörü ve PCB katman eşlemesi.

@details
**Paket biçimi = KiCad'in renk teması dosyası** (KiCad'de `colors/*.json`):

    {"meta": {"name": "Nord", "filename": "nord", "version": 3},
     "schematic": {"background": "rgb(46, 52, 64)", "wire": "...", ...},
     "board": {"background": "...", "f_silks": "...",
               "copper": {"f": "...", "b": "...", "in1": "..."}}}

Bir KiCad teması dönüştürülmeden içe aktarılır; buradan dışa aktarılan dosya da
KiCad'e konabilir (renkler KiCad'in `rgb(...)` / `rgba(...)` yazımıyla yazılır,
dosyadaki tanımadığımız bölüm ve anahtarlar — `3d_viewer`, `gerbview`,
`erc_error`… — olduğu gibi korunur). Bölümler isteğe bağlıdır: `board`
bölümü olmayan tema yalnız şematik listesinde görünür (pointhi deposundaki
11 temanın 7'si böyle).

Hazır temalar (salt okunur) bu modülde Python verisi olarak durur: PyInstaller'a
ek veri dosyası girmesin (`i18n`'deki kararın aynısı). Kullanıcı temaları
`user_theme_dir()` altında birer JSON dosyasıdır.

**GÜVENLİK**: tema renkleri üretilen HTML'deki JS dizgelerine ve canvas
`fillStyle`'ına gömülür → her değer `norm_color()`'dan geçer; tanınmayan biçim
atılır (yerine yedek renk gelir). Tema ADI HTML'e `html.escape` ile, JS'e
`_js_json` ile girer (viewer.py).

Bu modül üçüncü parti kütüphane KULLANMAZ (gui.py ve viewer.py'den önce de
güvenle import edilebilir).
"""
import colorsys
import copy
import json
import os
import re
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Renk biçimleri
# ---------------------------------------------------------------------------
_HEX_RE = re.compile(r"^#([0-9a-fA-F]{3}|[0-9a-fA-F]{6}|[0-9a-fA-F]{8})$")
_RGB_RE = re.compile(r"^rgba?\(\s*(\d{1,3})\s*,\s*(\d{1,3})\s*,\s*(\d{1,3})\s*"
                     r"(?:,\s*([0-9]*\.?[0-9]+)\s*)?\)$", re.I)


def parse_color(value):
    """@brief Renk dizgesini `(r, g, b, a)` demetine çevirir (0-255, alfa 0-1).

    @details Kabul edilenler: `#rgb`, `#rrggbb`, `#rrggbbaa`, `rgb(r, g, b)`,
    `rgba(r, g, b, a)`, `transparent`. Başka her şey (ad, `hsl()`, betik
    parçası…) None döner.
    @param value Renk dizgesi
    @return (r, g, b, a) veya None
    """
    if not isinstance(value, str):
        return None
    v = value.strip()
    if v.lower() == "transparent":
        return (0, 0, 0, 0.0)
    m = _HEX_RE.match(v)
    if m:
        h = m.group(1)
        if len(h) == 3:
            h = "".join(c * 2 for c in h)
        r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
        a = int(h[6:8], 16) / 255 if len(h) == 8 else 1.0
        return (r, g, b, a)
    m = _RGB_RE.match(v)
    if m:
        r, g, b = (int(m.group(i)) for i in (1, 2, 3))
        if max(r, g, b) > 255:
            return None
        a = float(m.group(4)) if m.group(4) is not None else 1.0
        return (r, g, b, max(0.0, min(1.0, a)))
    return None


def _fmt_alpha(a):
    return ("%.3f" % a).rstrip("0").rstrip(".") or "0"


def format_color(rgba):
    """@brief `(r, g, b, a)` → `#rrggbb` (opak) ya da `rgba(r,g,b,a)`.

    @param rgba parse_color() çıktısı
    @return CSS renk dizgesi
    """
    r, g, b, a = rgba
    if a >= 0.999:
        return "#%02x%02x%02x" % (r, g, b)
    return "rgba(%d,%d,%d,%s)" % (r, g, b, _fmt_alpha(a))


def norm_color(value):
    """@brief Rengi doğrulayıp tek biçime getirir; geçersizse None.

    @param value Renk dizgesi (KiCad `rgb(...)`, CSS hex …)
    @return `#rrggbb` / `rgba(r,g,b,a)` veya None
    """
    p = parse_color(value)
    return format_color(p) if p else None


def kicad_color(value):
    """@brief Rengi KiCad'in tema dosyasındaki yazıma çevirir.

    @param value Normalize renk
    @return `rgb(r, g, b)` / `rgba(r, g, b, a)` (geçersizse None)
    """
    p = parse_color(value)
    if not p:
        return None
    r, g, b, a = p
    if a >= 0.999:
        return "rgb(%d, %d, %d)" % (r, g, b)
    return "rgba(%d, %d, %d, %.3f)" % (r, g, b, a)


# ---------------------------------------------------------------------------
# Yazı tipleri (v2.40.0)
# ---------------------------------------------------------------------------
# Yazı tipi DOSYASI gömülmez — sistem fontlarının çoğunun lisansı dağıtıma
# izin vermez. Seçilen ad CSS yazı tipi listesinin BAŞINA konur, ardından
# özgün yazı tipi gelir: HTML'i açan bilgisayarda yoksa özgün font kullanılır.
GENERIC_FONTS = ("sans-serif", "serif", "monospace", "system-ui", "cursive", "fantasy")
# Görüntüleyicinin araç çubuğundaki şematik yazı tipi seçicisinde hazır liste
# (Windows / macOS / Linux'ta yaygın olanlar + genel aileler)
HTML_FONT_CHOICES = (
    "Arial", "Segoe UI", "Calibri", "Verdana", "Tahoma", "Trebuchet MS",
    "Helvetica", "DejaVu Sans", "Liberation Sans",
    "Times New Roman", "Georgia", "Consolas", "Courier New", "DejaVu Sans Mono",
    "sans-serif", "serif", "monospace",
)
_FONT_OK = re.compile(r"^[\w .\-]{1,60}$")


def clean_font(name) -> str:
    """@brief Yazı tipi adını doğrular: harf/rakam/boşluk/.-_ dışında karakter
    (tırnak, virgül, noktalı virgül, <>…) varsa '' döner — ad CSS'e ve JS
    dizgelerine gömülür.

    @param name Aile adı ("" / None = özgün yazı tipi)
    @return Temiz ad ya da ''
    """
    s = str(name or "").strip()
    return s if _FONT_OK.match(s) and not s.startswith("@") else ""


def css_font_stack(name, fallback) -> str:
    """@brief Seçilen yazı tipini özgün listenin önüne koyar.

    @param name Seçilen aile (clean_font'tan geçmiş; '' = yalnız fallback)
    @param fallback Özgün CSS listesi (ör. "Consolas,monospace")
    @return CSS font-family listesi
    """
    if not name:
        return fallback
    q = name if name in GENERIC_FONTS else '"%s"' % name
    return q + ", " + fallback


# ---------------------------------------------------------------------------
# Kontrast / okunurluk (v2.36.1'de viewer.py'deydi; GUI önizlemesi de
# kullansın diye buraya taşındı — viewer.py aynı adlarla yeniden dışa verir)
# ---------------------------------------------------------------------------
# Okunurluk uyarlaması (v2.36.1, kullanıcı bildirimi: "blok tasarımların kutu
# içi zemin ile aynı renkte kalmış … wdark'ta mor ve siyah göz yoruyor").
# Tema tablosu kaynakla BİREBİR kalır; uyarlama üretimde uygulanır:
#  1. Sheet symbol (blok) dolgusu: KiCad temalarının `sheet_background`'ı 9
#     temada saydam (blok zeminle aynı görünüyordu). v2.36.1'de gövde rengine
#     eşitlendi; v2.40.0'dan beri AYRI ve düzenlenebilir bir renktir ve hazır
#     temalarda / saydam blokta `derive_sheet_fill()` ile zeminden ve gövdeden
#     ayırt edilen bir ton üretilir (kullanıcı istekleri: "sembol ile blok
#     sembolün iç rengi değiştirilebilir olmalı", "blok yapı olduğu anlaşılsın").
#  2. Çizgi/yazı rolleri zemine (ve gövde / blok içindekiler o dolguya) karşı
#     WCAG kontrastı en az _TH_MIN_CONTRAST olacak şekilde, TON (hue) ve
#     doygunluk korunarak yalnız açıklığı kaydırılır. Ölçülen en kötüler:
#     Nord tel 1.8 / hiyerarşik etiket 1.4, Eagle fields/sheet 1.9, koyu
#     temalarda komponent çizgisi gövdeye karşı 2.2–2.5.
_TH_MIN_CONTRAST = 3.0
_TH_ON_BG = ("wire", "bus", "junction", "component_outline", "pin", "pin_number",
             "pin_name", "reference", "value", "fields", "label_local",
             "label_global", "label_hier", "sheet", "sheet_name",
             "sheet_filename", "sheet_label", "no_connect", "note", "worksheet")
_TH_ON_BODY = ("component_outline", "pin_name")        # gövde dolgusu üstünde
_TH_ON_SHEET = ("sheet", "sheet_label")                 # blok dolgusu üstünde


def _th_rgb(c):
    """@brief Opak renk → (r, g, b) 0..1; saydam ya da geçersizse None."""
    p = parse_color(c)
    if not p or p[3] < 0.999:
        return None
    return tuple(v / 255 for v in p[:3])


def _th_over(c, bg):
    """@brief Rengi (alfa varsa) `bg` zemininin üstüne karıştırıp (r, g, b) 0..1 verir."""
    p = parse_color(c)
    if not p:
        return None
    a = p[3]
    return tuple(a * (v / 255) + (1 - a) * b for v, b in zip(p[:3], bg))


def _th_lum(rgb):
    """@brief WCAG bağıl parlaklık."""
    f = lambda v: v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4
    r, g, b = (f(v) for v in rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def _th_contrast(a, b):
    """@brief İki rengin WCAG kontrast oranı (1..21)."""
    la, lb = _th_lum(a), _th_lum(b)
    return (max(la, lb) + 0.05) / (min(la, lb) + 0.05)


def sch_theme_readable(colors: dict) -> dict:
    """@brief Tema renklerini okunurluk kuralına göre uyarlanmış KOPYA döndürür.

    @details Bkz. yukarıdaki açıklama. Eşiği zaten geçen renge DOKUNULMAZ;
    geçmeyen rengin HLS açıklığı zemin açıksa koyulaştırılarak, koyuysa
    açılarak 0.01 adımlarla kaydırılır (ilk yeten değer — en küçük değişiklik).
    Zemin ile gövde dolgusu aynı tarafta (ikisi de açık / ikisi de koyu)
    olduğundan tek yön ikisini birden sağlar.

    @param colors {KiCad anahtarı: renk}
    @return uyarlanmış yeni sözlük
    """
    c = dict(colors)
    sb = parse_color(c.get("sheet_background"))
    if not sb or sb[3] < 0.05:                 # saydam blok → ayırt edilen dolgu
        c["sheet_background"] = derive_sheet_fill(c)
    bg = _th_rgb(c["background"])
    if not bg:
        return c
    # Yarı saydam renk (KiCad temalarında gövde dolgusu / not rengi `rgba`
    # olabiliyor — shirokuma): kontrast, zemine karıştırılmış ETKİN renkle
    # ölçülür. Eskiden `_th_rgb` saydamda None verdiğinden tüm uyarlama
    # sessizce atlanıyordu. Düzeltilen renk opak yazılır.
    body = _th_over(c["component_body"], bg)
    sheet = _th_over(c["sheet_background"], bg)
    if not body or not sheet:
        return c
    darken = _th_lum(bg) > 0.18
    for k in _TH_ON_BG:
        rgb = _th_over(c.get(k), bg)
        if not rgb:
            continue
        refs = ([bg] + ([body] if k in _TH_ON_BODY else [])
                + ([sheet] if k in _TH_ON_SHEET else []))
        worst = lambda x: min(_th_contrast(x, r) for r in refs)
        if worst(rgb) >= _TH_MIN_CONTRAST:
            continue
        h, l, s = colorsys.rgb_to_hls(*rgb)
        # Önce zeminin tersine (açık zeminde koyulaştır); yetmezse — kullanıcı
        # blok/gövde dolgusunu zeminin öbür tarafına çektiyse — öbür yön; o da
        # yetmezse en iyi sonuç. İlk yön yettiğinde sonuç eskisiyle aynıdır.
        best = None
        for dark in (darken, not darken):
            for i in range(1, 101):
                nl = max(0.0, l - i * 0.01) if dark else min(1.0, l + i * 0.01)
                # Denetim YUVARLANMIŞ renkle yapılır: #rrggbb'ye yuvarlama kontrastı
                # eşiğin hemen altına düşürebiliyordu (sol-dark fields 2.998).
                q = tuple(round(v * 255) for v in colorsys.hls_to_rgb(h, nl, s))
                w = worst(tuple(v / 255 for v in q))
                if best is None or w > best[0]:
                    best = (w, q)
                if w >= _TH_MIN_CONTRAST:
                    best = (w, q)
                    break
                if nl in (0.0, 1.0):
                    break
            if best[0] >= _TH_MIN_CONTRAST:
                break
        c[k] = "#%02x%02x%02x" % best[1]
    return c


def is_dark(color) -> bool:
    """@brief Zemin rengi koyu mu (WCAG parlaklığı < 0.18)."""
    rgb = _th_rgb(color)
    return bool(rgb) and _th_lum(rgb) < 0.18


def _oklab(rgb):
    """@brief sRGB (0..1) → Oklab (algısal renk uzayı; ΔE ≈ göze görünen fark)."""
    f = lambda v: v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4
    r, g, b = (f(v) for v in rgb)
    l = (0.4122214708 * r + 0.5363325363 * g + 0.0514459929 * b) ** (1 / 3)
    m = (0.2119034982 * r + 0.6806995451 * g + 0.1073969566 * b) ** (1 / 3)
    s_ = (0.0883024619 * r + 0.2817188376 * g + 0.6299787005 * b) ** (1 / 3)
    return (0.2104542553 * l + 0.7936177850 * m - 0.0040720468 * s_,
            1.9779984951 * l - 2.4285922050 * m + 0.4505937099 * s_,
            0.0259040371 * l + 0.7827717662 * m - 0.8086757660 * s_)


def _de(a, b):
    """@brief İki rengin Oklab farkı (0.02 ≈ zor seçilir, 0.05 ≈ açıkça farklı)."""
    pa, pb = _oklab(a), _oklab(b)
    return sum((x - y) ** 2 for x, y in zip(pa, pb)) ** 0.5


# Blok (sayfa sembolü) dolgusu zeminden ve sembol gövdesinden en az bu kadar
# farklı olmalı — "blok yapı olduğu anlaşılsın" (kullanıcı isteği, v2.40.0)
_SHEET_FILL_MIN_DE = 0.05
# Tonun alınacağı tema renkleri (sırayla): önce blok sınırının kendisi
_SHEET_FILL_SOURCES = ("sheet", "sheet_label", "sheet_name", "label_hier", "bus",
                       "note", "label_global", "wire")


def derive_sheet_fill(sch) -> str:
    """@brief Temanın paletinden, zeminden ve gövdeden ayırt edilen blok dolgusu.

    @details Blok sınır renginin zemine karıştırılmış açık tonu (açık temada
    ~%16, koyu temada ~%30). Ton zeminden VE sembol gövdesinden en az
    `_SHEET_FILL_MIN_DE` (Oklab) farklı olmalı; tutmazsa oran ve sonra
    `_SHEET_FILL_SOURCES`'taki diğer renkler denenir (Black/White'ta sınır
    siyah → açık gri). Hiçbiri tutmazsa gövdenin açıklığı zeminden uzaklaştırılır.

    @param sch Şematik renkleri (background, component_body … dolu)
    @return '#rrggbb'
    """
    bg = _th_rgb(sch.get("background")) or (1.0, 1.0, 1.0)
    body = _th_over(sch.get("component_body"), bg) or bg
    dark = _th_lum(bg) < 0.18
    base = 0.30 if dark else 0.16
    q8 = lambda c: tuple(round(max(0.0, min(1.0, v)) * 255) / 255 for v in c)
    hx = lambda c: "#%02x%02x%02x" % tuple(round(v * 255) for v in c)
    for key in _SHEET_FILL_SOURCES:
        src = _th_over(sch.get(key), bg)
        if not src:
            continue
        for a in (base, base * 1.5, base * 0.6, base * 2.2):
            q = q8(tuple(a * x + (1 - a) * y for x, y in zip(src, bg)))
            if _de(q, bg) >= _SHEET_FILL_MIN_DE and _de(q, body) >= _SHEET_FILL_MIN_DE:
                return hx(q)
    return _shift_lightness(hx(q8(body)), 0.12 if dark else -0.12)


def _shift_lightness(color, amount):
    """@brief Rengin HLS açıklığını `amount` kadar kaydırır (#rrggbb)."""
    rgb = _th_rgb(color)
    if not rgb:
        return color
    h, l, s = colorsys.rgb_to_hls(*rgb)
    l = max(0.0, min(1.0, l + amount))
    return "#%02x%02x%02x" % tuple(round(v * 255) for v in colorsys.hls_to_rgb(h, l, s))


# ---------------------------------------------------------------------------
# Anahtarlar
# ---------------------------------------------------------------------------
# Şematik: draw-list rolleri (viewer._dl_role) bu KiCad anahtarlarını kullanır.
SCH_KEYS = (
    "background", "wire", "bus", "junction", "component_outline", "component_body",
    "pin", "pin_name", "pin_number", "reference", "value", "fields",
    "label_local", "label_global", "label_hier", "sheet", "sheet_background",
    "sheet_name", "sheet_filename", "sheet_label", "no_connect", "note", "worksheet",
)
# Eksik anahtarın yedek zinciri (eski sürüm KiCad temalarında `worksheet` /
# `sheet_background` yok; elle yazılmış dosyalarda daha fazlası eksik olabilir).
_SCH_FALLBACK = {
    "wire": ("component_outline",), "bus": ("wire",), "junction": ("wire",),
    "component_outline": ("note",), "component_body": ("background",),
    "pin": ("component_outline",), "pin_name": ("pin", "reference"),
    "pin_number": ("pin",), "reference": ("component_outline",),
    "value": ("reference",), "fields": ("value",), "label_local": ("wire",),
    "label_global": ("label_local",), "label_hier": ("label_global",),
    "sheet": ("component_outline",), "sheet_name": ("sheet",),
    "sheet_filename": ("sheet_name",), "sheet_label": ("sheet",),
    "no_connect": ("bus", "wire"), "note": ("component_outline",),
    "worksheet": ("note",),
}

# PCB: kullandığımız düz anahtarlar + `copper` alt sözlüğü (f, b, in1..in30).
BOARD_KEYS = (
    "background", "edge_cuts", "f_silks", "b_silks", "f_mask", "b_mask",
    "f_paste", "b_paste", "f_crtyd", "b_crtyd", "f_fab", "b_fab",
    "pad_through_hole", "via_through", "margin", "dwgs_user", "cmts_user",
    "eco1_user", "eco2_user",
) + tuple(f"user_{i}" for i in range(1, 10))
COPPER_KEYS = ("f", "b") + tuple(f"in{i}" for i in range(1, 31))

# "Altium (orijinal)" PCB renkleri — viewer._GEO_LAYER_STYLE ile AYNI olmalı
# (test denetler). Kopyalanarak yeni PCB teması kurulabilsin diye paket
# biçiminde de tutulur; listedeki olmayan katmanlar viewer'da üretilen renkle
# çizilir.
ALTIUM_BOARD = {
    "background": "#0a0a0a", "edge_cuts": "#c8b400",
    "f_silks": "#e8e8e8", "b_silks": "#9a9a9a",
    "f_mask": "#1a6b3a", "b_mask": "#0d4d28",
    "f_paste": "#b0b0b0", "b_paste": "#808080",
    "pad_through_hole": "#d4a020", "margin": "#7a5cff",
    "copper": {"f": "#e04040", "b": "#4060e0"},
}
ALTIUM_ID = "altium"


# ---------------------------------------------------------------------------
# Hazır temalar
# ---------------------------------------------------------------------------
# Şematik: KiCad 10 "KiCad Default" + github.com/pointhi/kicad-color-schemes
# (CC0) şematik bölümleri; eksik `worksheet` ← `note`, `sheet_background` ←
# saydam. PCB (board): aynı deponun `kicad_2020`, `nord`, `eagle-dark`,
# `behave-dark` dosyalarının board bölümleri (CC0), yalnız kullandığımız
# anahtarlar.
_SCH_KICAD = {
    'background': '#f5f4ef', 'wire': '#009600', 'bus': '#000084',
    'junction': '#009600', 'component_outline': '#840000', 'component_body': '#ffffc2',
    'pin': '#840000', 'pin_name': '#006464', 'pin_number': '#a90000',
    'reference': '#006464', 'value': '#006464', 'fields': '#840084',
    'label_local': '#0f0f0f', 'label_global': '#840000', 'label_hier': '#725600',
    'sheet': '#840000', 'sheet_background': 'rgba(255,255,255,0)',
    'sheet_name': '#006464', 'sheet_filename': '#725600', 'sheet_label': '#006464',
    'no_connect': '#000084', 'note': '#0000c2', 'worksheet': '#840000',
}
_SCH_WLIGHT = {
    'background': '#fffcf8', 'wire': '#000080', 'bus': '#0000ff',
    'junction': '#000080', 'component_outline': '#000000', 'component_body': '#fffed0',
    'pin': '#000000', 'pin_name': '#000000', 'pin_number': '#808080',
    'reference': '#000080', 'value': '#000084', 'fields': '#840084',
    'label_local': '#000080', 'label_global': '#800000', 'label_hier': '#800000',
    'sheet': '#000000', 'sheet_background': '#c0ffb8', 'sheet_name': '#000080',
    'sheet_filename': '#000080', 'sheet_label': '#800000', 'no_connect': '#000084',
    'note': '#008000', 'worksheet': '#000000',
}
_SCH_SOL_LIGHT = {
    'background': '#fdf6e3', 'wire': '#859900', 'bus': '#268bd2',
    'junction': '#859900', 'component_outline': '#586e75', 'component_body': '#eee8d5',
    'pin': '#586e75', 'pin_name': '#cb4b16', 'pin_number': '#b58900',
    'reference': '#268bd2', 'value': '#6c71c4', 'fields': '#93a1a1',
    'label_local': '#2aa198', 'label_global': '#2aa198', 'label_hier': '#2aa198',
    'sheet': '#586e75', 'sheet_background': 'rgba(255,255,255,0)',
    'sheet_name': '#268bd2', 'sheet_filename': '#6c71c4', 'sheet_label': '#cb4b16',
    'no_connect': '#6c71c4', 'note': '#586e75', 'worksheet': '#dc322f',
}
_SCH_NORD = {
    'background': '#eceff4', 'wire': '#a3be8c', 'bus': '#81a1c1',
    'junction': '#a3be8c', 'component_outline': '#4c566a', 'component_body': '#e5e9f0',
    'pin': '#4c566a', 'pin_name': '#434c5e', 'pin_number': '#434c5e',
    'reference': '#5e81ac', 'value': '#5e81ac', 'fields': '#5e81ac',
    'label_local': '#434c5e', 'label_global': '#bf616a', 'label_hier': '#ebcb8b',
    'sheet': '#b48ead', 'sheet_background': 'rgba(255,255,255,0)',
    'sheet_name': '#b48ead', 'sheet_filename': '#b48ead', 'sheet_label': '#ebcb8b',
    'no_connect': '#81a1c1', 'note': '#5e81ac', 'worksheet': '#3b4252',
}
_SCH_BLUE_TONE = {
    'background': '#ffffff', 'wire': '#428437', 'bus': '#6e3ba0',
    'junction': '#428437', 'component_outline': '#313184', 'component_body': '#d2d4ff',
    'pin': '#3d3384', 'pin_name': '#411d64', 'pin_number': '#5a4eca',
    'reference': '#3a7384', 'value': '#3a7484', 'fields': '#006784',
    'label_local': '#000000', 'label_global': '#842784', 'label_hier': '#542682',
    'sheet': '#523d65', 'sheet_background': 'rgba(0,0,0,0)', 'sheet_name': '#008484',
    'sheet_filename': '#008484', 'sheet_label': '#552784', 'no_connect': '#5d0084',
    'note': '#0000c2', 'worksheet': '#00001b',
}
_SCH_BW = {
    'background': '#ffffff', 'wire': '#000000', 'bus': '#000000',
    'junction': '#000000', 'component_outline': '#000000', 'component_body': '#c0c0c0',
    'pin': '#000000', 'pin_name': '#000000', 'pin_number': '#000000',
    'reference': '#000000', 'value': '#000000', 'fields': '#000000',
    'label_local': '#000000', 'label_global': '#000000', 'label_hier': '#000000',
    'sheet': '#000000', 'sheet_background': 'rgba(255,255,255,0)',
    'sheet_name': '#000000', 'sheet_filename': '#000000', 'sheet_label': '#000000',
    'no_connect': '#000000', 'note': '#000000', 'worksheet': '#000000',
}
_SCH_SOL_DARK = {
    'background': '#002b36', 'wire': '#859900', 'bus': '#268bd2',
    'junction': '#859900', 'component_outline': '#93a1a1', 'component_body': '#073642',
    'pin': '#93a1a1', 'pin_name': '#cb4b16', 'pin_number': '#b58900',
    'reference': '#268bd2', 'value': '#6c71c4', 'fields': '#586e75',
    'label_local': '#2aa198', 'label_global': '#2aa198', 'label_hier': '#2aa198',
    'sheet': '#93a1a1', 'sheet_background': 'rgba(255,255,255,0)',
    'sheet_name': '#268bd2', 'sheet_filename': '#6c71c4', 'sheet_label': '#cb4b16',
    'no_connect': '#6c71c4', 'note': '#93a1a1', 'worksheet': '#dc322f',
}
_SCH_WDARK = {
    'background': '#282c34', 'wire': '#98c379', 'bus': '#61afef',
    'junction': '#98c379', 'component_outline': '#e06c75', 'component_body': '#545862',
    'pin': '#e06c75', 'pin_name': '#98c379', 'pin_number': '#e06c75',
    'reference': '#56b6c2', 'value': '#56b6c2', 'fields': '#56b6c2',
    'label_local': '#e5c07b', 'label_global': '#e06c75', 'label_hier': '#c678dd',
    'sheet': '#c678dd', 'sheet_background': '#000000', 'sheet_name': '#c678dd',
    'sheet_filename': '#c678dd', 'sheet_label': '#c678dd', 'no_connect': '#61afef',
    'note': '#61afef', 'worksheet': '#7f848e',
}
_SCH_BEHAVE = {
    'background': '#232932', 'wire': '#8dd272', 'bus': '#4487aa',
    'junction': '#8dd272', 'component_outline': '#c4626b', 'component_body': '#513c56',
    'pin': '#c4626b', 'pin_name': '#669696', 'pin_number': '#c4626b',
    'reference': '#a683e1', 'value': '#669696', 'fields': '#786596',
    'label_local': '#4487aa', 'label_global': '#c46c2d', 'label_hier': '#c3ae72',
    'sheet': '#856fa5', 'sheet_background': 'rgba(0,0,0,0)', 'sheet_name': '#669696',
    'sheet_filename': '#856fa5', 'sheet_label': '#c47a4f', 'no_connect': '#95dbdf',
    'note': '#4487aa', 'worksheet': '#4487aa',
}
_SCH_MONOKAI = {
    'background': '#3b3a32', 'wire': '#a6e22e', 'bus': '#66d9ef',
    'junction': '#a6e22e', 'component_outline': '#f92672', 'component_body': '#49483e',
    'pin': '#f92672', 'pin_name': '#66d9ef', 'pin_number': '#f92672',
    'reference': '#66d9ef', 'value': '#66d9ef', 'fields': '#ae81ff',
    'label_local': '#f8f8f2', 'label_global': '#f92672', 'label_hier': '#ffe792',
    'sheet': '#ae81ff', 'sheet_background': 'rgba(0,0,0,0)', 'sheet_name': '#66d9ef',
    'sheet_filename': '#ffe792', 'sheet_label': '#ffe792', 'no_connect': '#66d9ef',
    'note': '#fd971f', 'worksheet': '#635778',
}
_SCH_EAGLE = {
    'background': '#212121', 'wire': '#00a000', 'bus': '#0060c0',
    'junction': '#00a000', 'component_outline': '#c00000', 'component_body': '#2c2c2c',
    'pin': '#c00000', 'pin_name': '#c0c0c0', 'pin_number': '#c00000',
    'reference': '#c0c0c0', 'value': '#c0c0c0', 'fields': '#8000a0',
    'label_local': '#c0c0c0', 'label_global': '#00a0e0', 'label_hier': '#a0a000',
    'sheet': '#8000a0', 'sheet_background': 'rgba(255,255,255,0)',
    'sheet_name': '#00a0cc', 'sheet_filename': '#a0a000', 'sheet_label': '#a0a000',
    'no_connect': '#612be0', 'note': '#c0c000', 'worksheet': '#c00000',
}

_BOARD_KICAD = {'background': '#001023', 'edge_cuts': '#d0d2cd', 'f_silks': '#f2eda1', 'b_silks': '#e8b2a7', 'f_mask': 'rgba(216,100,255,0.4)', 'b_mask': 'rgba(2,255,238,0.4)', 'f_paste': 'rgba(180,160,154,0.902)', 'b_paste': '#00c2c2', 'f_crtyd': '#ff00f5', 'b_crtyd': '#ff26e2', 'f_fab': '#afafaf', 'b_fab': '#585d84', 'pad_through_hole': '#e3b72e', 'via_through': '#ececec', 'margin': '#ff26e2', 'dwgs_user': '#c2c2c2', 'cmts_user': '#5994dc', 'eco1_user': '#b4dbd2', 'eco2_user': '#d8c852', 'user_1': '#c2c2c2', 'user_2': '#5994dc', 'user_3': '#b4dbd2', 'user_4': '#d8c852', 'user_5': '#c2c2c2', 'user_6': '#5994dc', 'user_7': '#b4dbd2', 'user_8': '#d8c852', 'user_9': '#e8b2a7', 'copper': {'f': '#c83434', 'b': '#4d7fc4', 'in1': '#7fc87f', 'in2': '#ce7d2c', 'in3': '#4fcbcb', 'in4': '#db628b', 'in5': '#a7a5c6', 'in6': '#28ccd9', 'in7': '#e8b2a7', 'in8': '#f2eda1', 'in9': '#8dcb81', 'in10': '#ed7c33', 'in11': '#5bc3eb', 'in12': '#f76f8e', 'in13': '#a7a5c6', 'in14': '#28ccd9', 'in15': '#e8b2a7', 'in16': '#f2eda1', 'in17': '#ed7c33', 'in18': '#5bc3eb', 'in19': '#f76f8e', 'in20': '#a7a5c6', 'in21': '#28ccd9', 'in22': '#e8b2a7', 'in23': '#f2eda1', 'in24': '#ed7c33', 'in25': '#5bc3eb', 'in26': '#f76f8e', 'in27': '#a7a5c6', 'in28': '#28ccd9', 'in29': '#e8b2a7', 'in30': '#f2eda1'}}
_BOARD_NORD = {'background': '#2e3440', 'edge_cuts': '#9450a0', 'f_silks': '#c47b99', 'b_silks': '#918ac3', 'f_mask': '#bf616a', 'b_mask': '#81a1c1', 'f_paste': '#e0aca5', 'b_paste': '#88c0d0', 'f_crtyd': '#c2c2c2', 'b_crtyd': '#848484', 'f_fab': '#798596', 'b_fab': '#987d7e', 'pad_through_hole': '#d8dee9', 'via_through': '#d8dee9', 'margin': '#ff26e2', 'dwgs_user': '#d8dee9', 'cmts_user': '#726775', 'eco1_user': '#008400', 'eco2_user': '#c2c200', 'user_1': '#c2c2c2', 'user_2': '#5994dc', 'user_3': '#b4dbd2', 'user_4': '#d8c852', 'user_5': '#c2c2c2', 'user_6': '#5994dc', 'user_7': '#b4dbd2', 'user_8': '#d8c852', 'user_9': '#e8b2a7', 'copper': {'f': '#b3474d', 'b': '#5e81ac', 'in1': '#ebcb8b', 'in2': '#a3be8c', 'in3': '#c20000', 'in4': '#008484', 'in5': '#008400', 'in6': '#000084', 'in7': '#848484', 'in8': '#840084', 'in9': '#c2c2c2', 'in10': '#840084', 'in11': '#840000', 'in12': '#848400', 'in13': '#c2c2c2', 'in14': '#000084', 'in15': '#008400', 'in16': '#840000', 'in17': '#c2c200', 'in18': '#c200c2', 'in19': '#c20000', 'in20': '#008484', 'in21': '#008400', 'in22': '#000084', 'in23': '#848484', 'in24': '#840084', 'in25': '#c2c2c2', 'in26': '#840084', 'in27': '#840000', 'in28': '#848400', 'in29': '#c2c2c2', 'in30': '#000084'}}
_BOARD_EAGLE = {'background': '#212121', 'edge_cuts': 'rgba(160,160,160,0.8)', 'f_silks': 'rgba(224,170,170,0.8)', 'b_silks': 'rgba(170,170,224,0.8)', 'f_mask': 'rgba(224,170,170,0.7)', 'b_mask': 'rgba(170,170,224,0.7)', 'f_paste': 'rgba(192,128,128,0.75)', 'b_paste': 'rgba(128,128,192,0.75)', 'f_crtyd': '#f8f8f2', 'b_crtyd': '#f8f8f2', 'f_fab': '#e0aaaa', 'b_fab': '#aaaac0', 'pad_through_hole': 'rgba(50,200,50,0.7)', 'via_through': '#c2c2c2', 'margin': '#ff26e2', 'dwgs_user': '#c0c0c0', 'cmts_user': '#a0a000', 'eco1_user': '#008400', 'eco2_user': '#c2c200', 'user_1': '#c2c2c2', 'user_2': '#5994dc', 'user_3': '#b4dbd2', 'user_4': '#d8c852', 'user_5': '#c2c2c2', 'user_6': '#5994dc', 'user_7': '#b4dbd2', 'user_8': '#d8c852', 'user_9': '#e8b2a7', 'copper': {'f': 'rgba(192,0,0,0.7)', 'b': 'rgba(50,50,200,0.7)', 'in1': 'rgba(255,255,0,0.7)', 'in2': 'rgba(200,200,50,0.7)', 'in3': 'rgba(50,200,200,0.7)', 'in4': 'rgba(0,255,255,0.7)', 'in5': 'rgba(255,50,255,0.7)', 'in6': 'rgba(200,50,200,0.7)', 'in7': '#848484', 'in8': '#840084', 'in9': '#c2c2c2', 'in10': '#840084', 'in11': '#840000', 'in12': '#848400', 'in13': '#c2c2c2', 'in14': '#000084', 'in15': '#008400', 'in16': '#840000', 'in17': '#c2c200', 'in18': '#c200c2', 'in19': '#c20000', 'in20': '#008484', 'in21': '#008400', 'in22': '#000084', 'in23': '#848484', 'in24': '#840084', 'in25': '#c2c2c2', 'in26': '#840084', 'in27': '#840000', 'in28': '#848400', 'in29': '#c2c2c2', 'in30': '#000084'}}
_BOARD_BEHAVE = {'background': '#232932', 'edge_cuts': '#c8a339', 'f_silks': '#81bebe', 'b_silks': '#796596', 'f_mask': 'rgba(180,74,76,0.698)', 'b_mask': 'rgba(54,132,109,0.698)', 'f_paste': '#ff00ff', 'b_paste': '#00c2c2', 'f_crtyd': '#c9a9f9', 'b_crtyd': '#95dbdf', 'f_fab': '#f0d879', 'b_fab': '#8dd272', 'via_through': '#c2c2c2', 'dwgs_user': '#a5a5a5', 'cmts_user': '#41a042', 'eco1_user': '#008400', 'eco2_user': '#ff5762', 'copper': {'f': 'rgba(194,96,101,0.8)', 'b': 'rgba(101,162,229,0.8)', 'in1': 'rgba(194,107,170,0.6)', 'in2': 'rgba(127,194,161,0.6)', 'in3': '#c20000', 'in4': '#008484', 'in5': '#008400', 'in6': '#000084', 'in7': '#848484', 'in8': '#840084', 'in9': '#c2c2c2', 'in10': '#840084', 'in11': '#840000', 'in12': '#848400', 'in13': '#c2c2c2', 'in14': '#000084', 'in15': '#008400', 'in16': '#840000', 'in17': '#c2c200', 'in18': '#c200c2', 'in19': '#c20000', 'in20': '#008484', 'in21': '#008400', 'in22': '#000084', 'in23': '#848484', 'in24': '#840084', 'in25': '#c2c2c2', 'in26': '#840084', 'in27': '#840000', 'in28': '#848400', 'in29': '#c2c2c2', 'in30': '#000084'}}

_SRC = "github.com/pointhi/kicad-color-schemes"
# (id, ad, koyu mu, şematik, board, kaynak) — sıra = seçim listesindeki sıra
_BUILTIN_TABLE = [
    ("kicad", "KiCad", False, _SCH_KICAD, _BOARD_KICAD, "KiCad 10 / " + _SRC),
    ("wlight", "wLight", False, _SCH_WLIGHT, None, _SRC),
    ("sol-light", "Solarized Light", False, _SCH_SOL_LIGHT, None, _SRC),
    ("nord", "Nord", False, _SCH_NORD, _BOARD_NORD, _SRC),
    ("blue-tone", "Blue Tone", False, _SCH_BLUE_TONE, None, _SRC),
    ("bw", "Black/White", False, _SCH_BW, None, _SRC),
    ("sol-dark", "Solarized Dark", True, _SCH_SOL_DARK, None, _SRC),
    ("wdark", "wDark", True, _SCH_WDARK, None, _SRC),
    ("behave", "Behave Dark", True, _SCH_BEHAVE, _BOARD_BEHAVE, _SRC),
    ("monokai", "Monokai", True, _SCH_MONOKAI, None, _SRC),
    ("eagle", "Eagle Dark", True, _SCH_EAGLE, _BOARD_EAGLE, _SRC),
]


def builtin_packs():
    """@brief Hazır (salt okunur) temaların derin kopyası.

    @details Önce v2.36.0'daki 11 tema (sıra değişmedi), sonra
    `theme_library.LIBRARY`'deki üçüncü parti temalar. Bir tema yalnız şematik
    ya da yalnız board içerebilir (`None`).
    @return paket listesi (bkz. parse_pack çıktısı)
    """
    from theme_library import LIBRARY
    out = []
    for tid, name, dark, sch, board, src in _BUILTIN_TABLE:
        sch = dict(sch)
        # Blok dolgusu: temanın kendi blok sınır renginin tonu, zeminden ve
        # gövdeden ayırt edilir (v2.40.0, "blok yapı olduğu anlaşılsın").
        sch["sheet_background"] = derive_sheet_fill(sch)
        out.append({
            "id": tid, "name": name, "dark": dark, "builtin": True, "path": None,
            "schematic": sch,
            "board": copy.deepcopy(board) if board else None,
            "source": src, "license": "CC0-1.0",
            "copyright": "pointhi/kicad-color-schemes", "raw": None,
        })
    for t in LIBRARY:
        sch, board = t["schematic"], t["board"]
        if sch:
            sch = dict(sch)
            sch["sheet_background"] = derive_sheet_fill(sch)    # hepsinde aynı kural
        out.append({
            "id": t["id"], "name": t["name"],
            "dark": is_dark((sch or board)["background"]), "builtin": True, "path": None,
            "schematic": sch or None,
            "board": copy.deepcopy(board) if board else None,
            "source": t["source"], "license": t["license"],
            "copyright": t["copyright"], "raw": None,
        })
    return out


_MIT_TEXT = """Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE."""


def notices_text() -> str:
    """@brief Hazır temaların kaynak / telif / lisans bildirimi (İngilizce, lisans dili).

    @details MIT ve Apache-2.0 lisansları, dağıtılan kopyada telif satırının
    ve lisans bildiriminin bulunmasını ister — renk değerleri uygulamanın
    içinde dağıtıldığı için bildirim de içeride durur (Renk Temaları →
    Lisanslar…). CC0 temalar bildirim gerektirmez, yine de kaynakları listelenir.
    """
    packs = builtin_packs()
    out = ["Built-in color themes — sources and licenses", "=" * 46, ""]
    groups = {}
    for p in packs:
        groups.setdefault(p["license"], []).append(p)
    for lic in ("MIT", "Apache-2.0", "CC0-1.0"):
        items = groups.get(lic) or []
        if not items:
            continue
        out.append(f"[{lic}]")
        for p in items:
            out.append(f"  {p['name']} — {p['copyright']} — {p['source']}")
        out.append("")
        if lic == "MIT":
            out += ["MIT License (applies to each MIT theme above, with its copyright line):",
                    "", _MIT_TEXT, ""]
        elif lic == "Apache-2.0":
            out += ["Licensed under the Apache License, Version 2.0 (the \"License\"); you may",
                    "not use these files except in compliance with the License. You may obtain",
                    "a copy of the License at http://www.apache.org/licenses/LICENSE-2.0",
                    "Distributed on an \"AS IS\" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY",
                    "KIND. Colors were converted from KiCad theme JSON (only the keys this",
                    "application uses were kept).", ""]
        elif lic == "CC0-1.0":
            out += ["Public domain dedication: https://creativecommons.org/publicdomain/zero/1.0/", ""]
    return "\n".join(out)


def legacy_sch_table():
    """@brief Eski `_SCH_THEMES` biçimi: [(id, ad, koyu, renkler)] (hazır temalar)."""
    return [(p["id"], p["name"], p["dark"], p["schematic"])
            for p in builtin_packs() if p["schematic"]]


# ---------------------------------------------------------------------------
# Paket ayrıştırma
# ---------------------------------------------------------------------------
_NAME_BAD = re.compile(r"[\x00-\x1f\x7f⟪⟫]")


def clean_name(name) -> str:
    """@brief Tema adını güvenli kısa metne indirger (kontrol karakteri / çeviri işareti atılır)."""
    s = _NAME_BAD.sub("", str(name or "")).strip()
    # "__X__" şablon yer tutucularına benzemesin (HTML şablonları .replace ile doldurulur)
    s = re.sub(r"_{2,}", "_", s)
    return s[:60] or "?"


def _norm_sch(sec):
    """@brief Şematik bölümünü normalize eder; eksik anahtarları yedek zincirle doldurur."""
    if not isinstance(sec, dict):
        return None
    c = {k: norm_color(sec.get(k)) for k in SCH_KEYS}
    if not c["background"] or not _th_rgb(c["background"]):
        return None
    sb = parse_color(c["sheet_background"])
    if not sb or sb[3] < 0.05:
        c["sheet_background"] = None        # saydam blok → aşağıda türetilir
    last = "#000000" if not is_dark(c["background"]) else "#ffffff"
    for _ in range(4):                       # zincir derinliği en çok 3
        for k in SCH_KEYS:
            if c[k]:
                continue
            for alt in _SCH_FALLBACK.get(k, ()):
                if c.get(alt):
                    c[k] = c[alt]
                    break
    for k in SCH_KEYS:
        if not c[k] and k != "sheet_background":
            c[k] = last
    if not c["sheet_background"]:
        c["sheet_background"] = derive_sheet_fill(c)   # saydam blok → ayırt edilen dolgu
    return c


def _norm_board(sec):
    """@brief Board bölümünü normalize eder (eksik anahtarlar boş kalır)."""
    if not isinstance(sec, dict):
        return None
    bg = norm_color(sec.get("background"))
    if not bg or not _th_rgb(bg):
        return None
    out = {"background": bg}
    for k in BOARD_KEYS[1:]:
        v = norm_color(sec.get(k))
        if v:
            out[k] = v
    cu = sec.get("copper") if isinstance(sec.get("copper"), dict) else {}
    out["copper"] = {k: norm_color(cu[k]) for k in COPPER_KEYS if norm_color(cu.get(k))}
    return out


def parse_pack(data, pid, builtin=False, path=None):
    """@brief KiCad biçimli tema sözlüğünü doğrulanmış pakete çevirir.

    @param data json.load çıktısı
    @param pid Paket kimliği
    @param builtin Hazır tema mı
    @param path Kaynak dosya (kullanıcı teması)
    @return {"id","name","dark","builtin","path","schematic","board","raw",…}
            ya da (tema hiç kullanılabilir bölüm içermiyorsa) None
    """
    if not isinstance(data, dict):
        return None
    meta = data.get("meta") if isinstance(data.get("meta"), dict) else {}
    sch = _norm_sch(data.get("schematic"))
    brd = _norm_board(data.get("board"))
    if not sch and not brd:
        return None
    name = clean_name(meta.get("name") or (Path(path).stem if path else pid))
    bg = (sch or brd)["background"]
    return {"id": pid, "name": name, "dark": is_dark(bg), "builtin": builtin,
            "path": Path(path) if path else None, "schematic": sch, "board": brd,
            "source": str(meta.get("source") or ""), "license": str(meta.get("license") or ""),
            "raw": data}


# ---------------------------------------------------------------------------
# Kullanıcı klasörü
# ---------------------------------------------------------------------------
def user_theme_dir() -> Path:
    """@brief Kullanıcı temalarının klasörü (oluşturulmaz).

    @details `SCHVIZ_THEME_DIR` ortam değişkeni önceliklidir (testler bunu
    kullanır). Windows: `%APPDATA%/SchematicViz/themes` · macOS:
    `~/Library/Application Support/SchematicViz/themes` · Linux:
    `$XDG_CONFIG_HOME/SchematicViz/themes` (yoksa `~/.config`).
    """
    env = os.environ.get("SCHVIZ_THEME_DIR")
    if env:
        return Path(env)
    if sys.platform.startswith("win"):
        base = Path(os.environ.get("APPDATA") or (Path.home() / "AppData" / "Roaming"))
    elif sys.platform == "darwin":
        base = Path.home() / "Library" / "Application Support"
    else:
        base = Path(os.environ.get("XDG_CONFIG_HOME") or (Path.home() / ".config"))
    return base / "SchematicViz" / "themes"


_TR_ASCII = str.maketrans("çğıöşüÇĞİÖŞÜâîû", "cgiosuCGIOSUaiu")


def slugify(name) -> str:
    """@brief Tema adından dosya adı (ASCII, küçük harf, tire)."""
    s = str(name or "").translate(_TR_ASCII).lower()
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return s[:40] or "tema"


def user_id(stem) -> str:
    """@brief Kullanıcı temasının kimliği (hazır kimliklerle çakışmasın diye önekli)."""
    return "u-" + slugify(stem)


def load_user_packs(dirpath=None):
    """@brief Kullanıcı klasöründeki `*.json` temaları okur.

    @param dirpath Klasör (None = user_theme_dir())
    @return (paketler, hatalar) — hatalar [(dosya adı, neden)]; neden 'json' |
            'empty' (kullanılabilir bölüm yok)
    """
    d = Path(dirpath) if dirpath else user_theme_dir()
    packs, errors, seen = [], [], set()
    if not d.is_dir():
        return packs, errors
    for f in sorted(d.glob("*.json"), key=lambda p: p.name.lower()):
        try:
            data = json.loads(f.read_text(encoding="utf-8-sig"))
        except Exception:
            errors.append((f.name, "json"))
            continue
        pid = user_id(f.stem)
        while pid in seen:
            pid += "-2"
        p = parse_pack(data, pid, path=f)
        if p is None:
            errors.append((f.name, "empty"))
            continue
        seen.add(pid)
        packs.append(p)
    return packs, errors


def load_all(dirpath=None):
    """@brief Hazır + kullanıcı temaları (bozuk kullanıcı dosyaları atlanır)."""
    return builtin_packs() + load_user_packs(dirpath)[0]


def find(packs, pid):
    """@brief Kimliğe göre paket (yoksa None)."""
    return next((p for p in packs if p["id"] == pid), None)


def pack_to_kicad(pack) -> dict:
    """@brief Paketi KiCad tema dosyası sözlüğüne çevirir.

    @details Kaynak dosyada olup bizim kullanmadığımız bölüm/anahtarlar
    (`3d_viewer`, `erc_error`, `copper.in31`…) korunur; yalnız bildiğimiz
    anahtarlar güncellenir.
    """
    raw = copy.deepcopy(pack.get("raw")) if isinstance(pack.get("raw"), dict) else {}
    meta = raw.get("meta") if isinstance(raw.get("meta"), dict) else {}
    stem = Path(pack["path"]).stem if pack.get("path") else slugify(pack["name"])
    meta.update({"name": pack["name"], "filename": stem})
    meta.setdefault("version", 3)
    raw["meta"] = meta
    if pack.get("schematic"):
        sec = raw.get("schematic") if isinstance(raw.get("schematic"), dict) else {}
        sec.update({k: kicad_color(v) for k, v in pack["schematic"].items() if kicad_color(v)})
        raw["schematic"] = sec
    if pack.get("board"):
        sec = raw.get("board") if isinstance(raw.get("board"), dict) else {}
        for k, v in pack["board"].items():
            if k == "copper":
                cu = sec.get("copper") if isinstance(sec.get("copper"), dict) else {}
                cu.update({ck: kicad_color(cv) for ck, cv in v.items() if kicad_color(cv)})
                sec["copper"] = cu
            elif kicad_color(v):
                sec[k] = kicad_color(v)
        raw["board"] = sec
    return raw


def unique_stem(base, dirpath=None, taken=()) -> str:
    """@brief Klasörde ve `taken` içinde olmayan dosya adı kökü."""
    d = Path(dirpath) if dirpath else user_theme_dir()
    stem, n = slugify(base), 2
    s = stem
    while s in taken or (d / (s + ".json")).exists():
        s = f"{stem}-{n}"
        n += 1
    return s


def save_pack(pack, dirpath=None) -> Path:
    """@brief Kullanıcı temasını dosyasına yazar (yoksa klasörde yeni ad alır).

    @return yazılan dosya
    """
    if pack.get("builtin"):
        raise ValueError("builtin")
    d = Path(dirpath) if dirpath else user_theme_dir()
    d.mkdir(parents=True, exist_ok=True)
    if not pack.get("path"):
        pack["path"] = d / (unique_stem(pack.get("_stem") or pack["name"], d) + ".json")
    data = pack_to_kicad(pack)
    Path(pack["path"]).write_text(json.dumps(data, indent=2, ensure_ascii=False),
                                  encoding="utf-8")
    pack["raw"] = data
    return Path(pack["path"])


def new_pack(name, schematic=None, board=None, taken_ids=(), dirpath=None):
    """@brief Bellekte yeni kullanıcı teması (dosyası save_pack ile yazılır).

    @param name Görünen ad
    @param schematic Şematik renkleri (kopyalanır) ya da None
    @param board Board renkleri (kopyalanır) ya da None
    @param taken_ids Kullanılmış kimlikler
    @param dirpath Kullanıcı tema klasörü (None = user_theme_dir())
    """
    name = clean_name(name)
    stem = unique_stem(name, dirpath, taken={i[2:] for i in taken_ids if i.startswith("u-")})
    pid = user_id(stem)
    bg = (schematic or board or {}).get("background", "#ffffff")
    return {"id": pid, "name": name, "dark": is_dark(bg), "builtin": False,
            "path": None, "schematic": copy.deepcopy(schematic),
            "board": copy.deepcopy(board), "source": "", "license": "",
            "raw": None, "_stem": stem}


def import_file(path, taken_ids=(), dirpath=None):
    """@brief Bir KiCad tema dosyasını yeni kullanıcı paketi olarak okur (yazmaz).

    @raise ValueError('json') okunamadı · ValueError('empty') kullanılabilir
           şematik/board bölümü yok
    """
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    except Exception:
        raise ValueError("json")
    p = parse_pack(data, "tmp")
    if p is None:
        raise ValueError("empty")
    fresh = new_pack(p["name"], p["schematic"], p["board"], taken_ids, dirpath)
    fresh["raw"] = data
    return fresh


# ---------------------------------------------------------------------------
# PCB katman eşlemesi (Altium iç anahtarı → KiCad tema anahtarı)
# ---------------------------------------------------------------------------
_FLAT_BY_K = {
    "TOP_OVERLAY": "f_silks", "BOTTOM_OVERLAY": "b_silks",
    "TOP_SOLDER": "f_mask", "BOTTOM_SOLDER": "b_mask",
    "TOP_PASTE": "f_paste", "BOTTOM_PASTE": "b_paste",
    "KEEPOUT": "margin", "DRILL_GUIDE": "dwgs_user", "DRILL_DRAWING": "dwgs_user",
}
_MECH_SPARE = ("eco1_user", "eco2_user", "cmts_user", "dwgs_user")


def pcb_layer_keys(layers):
    """@brief Görüntüleyici katmanlarını KiCad tema anahtarlarına eşler.

    @details Katmanın değişmeyen iç anahtarı `k` kullanılır (TOP, MID3,
    INTERNAL_PLANE1, MECHANICAL_29…). Altium'un mekanik katmanları KiCad'de
    ayrı rollerdir; görünen AD üzerinden tanınır ("Top Courtyard" → f_crtyd,
    "Bottom Assembly" → b_fab, "Route Tool Path" → edge_cuts). Tanınmayan
    mekanikler sırayla user_1…user_9, sonra eco1/eco2/cmts/dwgs alır.
    İç katman numarası: MIDn → in{n}, düzlem n → in{MID sayısı + n}.

    @param layers geo["layers"] (sırası korunur)
    @return her katman için ("copper", "in3") / ("f_silks",) / ("pad",) ya da None
    """
    mids = sum(1 for l in layers if str(l.get("k", "")).startswith("MID"))
    user_n, out = 0, []
    for l in layers:
        k = str(l.get("k") or "")
        nm = str(l.get("name") or "").lower()
        num = re.search(r"(\d+)$", k)
        if k == "TOP":
            out.append(("copper", "f"))
        elif k == "BOTTOM":
            out.append(("copper", "b"))
        elif k.startswith("MID") and num:
            out.append(("copper", "in" + num.group(1)))
        elif k.startswith("INTERNAL_PLANE") and num:
            out.append(("copper", "in%d" % min(30, mids + int(num.group(1)))))
        elif k == "MULTI_LAYER":
            out.append(("pad",))
        elif k in _FLAT_BY_K:
            out.append((_FLAT_BY_K[k],))
        elif k.startswith("MECHANICAL"):
            side = "b_" if nm.startswith("bottom") else "f_"
            if "courtyard" in nm:
                out.append((side + "crtyd",))
            elif any(w in nm for w in ("assembly", "fab", "3d body", "component outline",
                                         "designator")):
                out.append((side + "fab",))
            elif "dimension" in nm:
                out.append(("dwgs_user",))
            elif any(w in nm for w in ("route tool", "board shape", "outline", "v-cut",
                                         "v cut", "edge")):
                out.append(("edge_cuts",))
            elif "comment" in nm:
                out.append(("cmts_user",))
            else:
                user_n += 1
                out.append((f"user_{user_n}",) if user_n <= 9
                           else (_MECH_SPARE[(user_n - 10) % len(_MECH_SPARE)],))
        else:
            out.append(None)
    return out


def pcb_theme_colors(board, layers):
    """@brief Bir board temasının bu board'un katmanlarına göre renk tablosu.

    @param board Normalize board bölümü
    @param layers geo["layers"]
    @return {"bg","fr4","edge","hole","c":[renk|None …]} — None = katman özgün
            renginde kalır (temada karşılığı yok)
    """
    bg = board["background"]
    cu = board.get("copper") or {}
    cols = []
    for key in pcb_layer_keys(layers):
        if key is None:
            cols.append(None)
        elif key[0] == "copper":
            cols.append(cu.get(key[1]))
        elif key[0] == "pad":
            cols.append(board.get("pad_through_hole") or board.get("via_through"))
        else:
            cols.append(board.get(key[0]))
    # Levha (FR4) dolgusu KiCad'in 2B görünümünde yok → zeminden türetilir:
    # biraz açık (koyu zeminde) / biraz koyu (açık zeminde) ki board ayırt edilsin.
    fr4 = _shift_lightness(bg, 0.07 if is_dark(bg) else -0.07)
    return {"bg": bg, "fr4": fr4, "edge": board.get("edge_cuts"), "hole": bg, "c": cols}
