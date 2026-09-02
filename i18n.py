"""
@file i18n.py
@brief Arayüz dil desteği (Türkçe kaynak → İngilizce çeviri).

@details
Kaynak dil TÜRKÇE'dir: kodda ve gui.ui'de metinler Türkçe yazılır, çeviri
katalogu bu Türkçe dizgeyi anahtar olarak kullanır (Qt Linguist'in `tr()`
yaklaşımının sözlük tabanlı, derleme adımı gerektirmeyen karşılığı).

Kullanım:
    import i18n
    from i18n import tr
    i18n.set_language("en")
    tr("Altium Projesi")   # -> "Altium Project"

Karşılığı olmayan metin AYNEN döner (çeviri eksikse arayüz bozulmaz, yalnızca
o satır Türkçe kalır). Bu yüzden yeni metin eklerken katalogu güncellemek
zorunlu değildir — ama unutulan çeviriler `missing_keys()` ile listelenebilir.

Widget metinleri `snapshot_widgets()` ile bir kez (henüz Türkçeyken)
yedeklenir; dil değişince `apply_snapshot()` her metni KAYNAK Türkçesinden
yeniden çevirir. Aksi halde İngilizceden Türkçeye dönüş mümkün olmazdı.

@author Mikail Cansız
@date 2026
"""
# Schematic Viz Generator — arayüz dil desteği.
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

## @brief Kaynak dil (kataloğun anahtarlarının dili) — çeviri gerektirmez.
SOURCE_LANGUAGE = "tr"

## @brief Desteklenen diller ve menüde görünen adları.
LANGUAGES = {
    "tr": "Türkçe",
    "en": "English",
}


# ---------------------------------------------------------------------------
# İngilizce katalog — anahtar = gui.ui / gui.py içindeki TÜRKÇE metnin AYNISI.
# (Boşluklar, üç nokta "…", emoji ve "&&" kaçışları birebir eşleşmelidir.)
# ---------------------------------------------------------------------------
_EN = {
    # --- gui.ui: proje / çıktı -------------------------------------------
    "Altium Projesi": "Altium Project",
    ".PrjPcb proje dosyasını seç…": "Select the .PrjPcb project file…",
    "Gözat…": "Browse…",
    "Çıktı dosyası": "Output File",
    "Çıktı yolu (.html / .xlsx / .csv otomatik)…":
        "Output path (.html / .xlsx / .csv automatic)…",
    "Bulunan Şematikler": "Schematics Found",
    "Log": "Log",
    "Hazır": "Ready",
    "Python, PyQt5 ve modül sürümlerini göster":
        "Show Python, PyQt5 and module versions",
    "ℹ  Hakkında / Sürümler": "ℹ  About / Versions",

    # --- gui.ui: Excel / veri --------------------------------------------
    "📊  Excel / Veri Dışa Aktarma": "📊  Excel / Data Export",
    "MCU / Ana İşlemci:": "MCU / Main Processor:",
    "Ana işlemci designator'ı. Boş = en çok pinli IC otomatik. Çoklu: U2,U7":
        "Main processor designator. Empty = the IC with the most pins is "
        "detected automatically. Multiple: U2,U7",
    "örn. U2  (boş = otomatik, çoklu: U2,U7)":
        "e.g. U2  (empty = automatic, multiple: U2,U7)",
    "Min pin (IC haritası):": "Min pins (IC map):",
    "Bu sayıdan az pinli komponentler IC haritasına dahil edilmez":
        "Components with fewer pins than this are excluded from the IC map",
    "Hariç tut (IC haritası):": "Exclude (IC map):",
    "Designator HARF önekleri: bu öneklerle başlayan komponentler IC haritasına "
    "dahil edilmez (örn. J,P,TP → konnektör/header/testpoint). Ana işlemci asla "
    "hariç tutulmaz.":
        "Designator LETTER prefixes: components starting with these prefixes are "
        "excluded from the IC map (e.g. J,P,TP → connector/header/testpoint). "
        "The main processor is never excluded.",
    "örn. J,P,TP  (boş = hepsi dahil)": "e.g. J,P,TP  (empty = include all)",
    "MCU'nun her pini → hangi entegre/pin'e gidiyor (tek entegre)":
        "Every MCU pin → which IC/pin it goes to (single IC)",
    "MCU Pin Listesi (Excel)": "MCU Pin List (Excel)",
    "Her IC için pin→net→ana işlemci portu tablosu (≥ min pin)":
        "pin→net→main processor port table for every IC (≥ min pins)",
    "IC Bağlantı Haritası (Excel)": "IC Connection Map (Excel)",
    "Malzeme listesini CSV olarak dışa aktar (tüm parametreler)":
        "Export the bill of materials as CSV (all parameters)",
    "BOM (CSV)": "BOM (CSV)",
    "PCB yerleşim koordinatlarını CSV olarak dışa aktar (PCB gerekir)":
        "Export PCB placement coordinates as CSV (PCB required)",
    "Pick && Place (CSV)": "Pick && Place (CSV)",
    "SVG'siz kompakt JSON - AI/LLM analizi için (pin→net, BOM, varyant)":
        "Compact JSON without SVG - for AI/LLM analysis (pin→net, BOM, variants)",
    "JSON (AI / LLM için)": "JSON (for AI / LLM)",

    # --- gui.ui: görüntüleyiciler ----------------------------------------
    "🖥  Görüntüleyiciler (HTML)": "🖥  Viewers (HTML)",
    "İnteraktif şematik HTML görüntüleyici üret":
        "Generate an interactive schematic HTML viewer",
    "Şematik Viewer üret": "Generate Schematic Viewer",
    "Tam ekran PCB görüntüleyici (geometri/canvas): katman aç-kapa, tıklanabilir "
    "komponentler, ölçüm, net seçimi, BOM · Montaj paneli, döndür/çevir.":
        "Full-screen PCB viewer (geometry/canvas): layer toggling, clickable "
        "components, measurement, net selection, BOM · Assembly panel, "
        "rotate/flip.",
    "PCB Görüntüleyici üret": "Generate PCB Viewer",
    "Şematik + PCB + 3D tek dosyada. Üç yönlü cross-probe: birinde komponente "
    "tıkla → diğerlerinde gösterilir":
        "Schematic + PCB + 3D in a single file. Three-way cross-probe: click a "
        "component in one → it is shown in the others",
    "Şematik + PCB + 3D hepsini üret": "Generate Schematic + PCB + 3D (all)",
    "↗  Son çıktıyı tarayıcıda aç": "↗  Open last output in browser",
    "Şematik bağlantı renkleri": "Schematic connection colors",
    "Sayfalar arası:": "Between sheets:",
    "Sayfa içi:": "Within sheet:",
    "Antet / firma logosunu gizle": "Hide title block / company logo",
    "Sayfa antetini (firma logosu, gizlilik metni, DWN/CHK/REV/SHEET tablosu) "
    "üretilen HTML'e koyma. Altium'un Show Template Graphics / Title Block "
    "seçeneğini kapatmakla aynı şey: sayfa boyutu ve şema içeriği "
    "değişmez, sayfaya elle konmuş görseller (datasheet fotoğrafı vb.) "
    "korunur.":
        "Keep the sheet title block (company logo, confidentiality note, "
        "DWN/CHK/REV/SHEET table) out of the generated HTML. Same as turning off "
        "Show Template Graphics / Title Block in Altium: sheet size and schematic "
        "content are unchanged, and images placed by hand on the sheet "
        "(datasheet photos etc.) are kept.",

    # --- Menü çubuğu ------------------------------------------------------
    "&Dosya": "&File",
    "Proje &Aç…": "&Open Project…",
    "Çı&ktı Yolu Seç…": "Select Ou&tput Path…",
    "Son Çıktıyı Tarayıcıda Aç": "Open Last Output in Browser",
    "Çıktı Klasörünü Aç": "Open Output Folder",
    "Log'u Temizle": "Clear Log",
    "Çıkış": "Quit",
    "&Üret": "&Generate",
    "Şematik Viewer": "Schematic Viewer",
    "PCB Görüntüleyici": "PCB Viewer",
    "Şematik + PCB + 3D  ★": "Schematic + PCB + 3D  ★",
    "&Görünüm": "&View",
    "Tam Ekran": "Full Screen",
    "Pencereyi tam ekran yap / geri al (F11)":
        "Make the window full screen / restore it (F11)",
    "&Ayarlar": "&Settings",
    "Dil / Language": "Language / Dil",
    "Sayfalar Arası Renk…": "Between-sheets Color…",
    "Sayfa İçi Renk…": "Within-sheet Color…",
    "&Yardım": "&Help",
    "Hakkında / Sürümler": "About / Versions",
    "Sürümleri Panoya Kopyala": "Copy Versions to Clipboard",
    "Bağımlılık Durumu": "Dependency Status",
    "Proje dosyası seç (Ctrl+O)": "Select project file (Ctrl+O)",
    "Uygulamadan çık": "Quit the application",

    # --- gui.py: sürüm / hakkında ----------------------------------------
    "Uygulama": "Application",
    "İşletim Sistemi": "Operating System",
    "Hakkında / Sürüm Bilgisi": "About / Version Information",
    "Altium şematik projelerini interaktif HTML viewer'a ve AI analizine uygun "
    "JSON'a dönüştürür.":
        "Converts Altium schematic projects into an interactive HTML viewer and "
        "into JSON suitable for AI analysis.",
    "Sürümleri Kopyala": "Copy Versions",
    "✓ Sürüm bilgisi panoya kopyalandı.": "✓ Version information copied to clipboard.",
    "Dil: {ad}": "Language: {ad}",

    # deps.status_table() durum sözcükleri (Hakkında listesinde görünür)
    "tamam": "ok",
    "kurulu değil": "not installed",
    "kurulum bozuk": "broken installation",
    "eski sürüm": "outdated",

    # --- gui.py: diyaloglar / loglar -------------------------------------
    "Altium proje dosyası seç": "Select Altium project file",
    "Altium Project (*.PrjPcb *.PrjPCB);;Tüm Dosyalar (*)":
        "Altium Project (*.PrjPcb *.PrjPCB);;All Files (*)",
    "Çıktı yolunu seç": "Select output path",
    "HTML (*.html);;Tüm Dosyalar (*)": "HTML (*.html);;All Files (*)",
    "✓ Proje açıldı, {sayi} şema bulundu.":
        "✓ Project opened, {sayi} schematic(s) found.",
    "✗ Proje açılamadı: {hata}": "✗ Project could not be opened: {hata}",
    "Proje yükleme hatası": "Project load error",
    "Proje dosyası açılırken hata:\n\n{hata}":
        "Error while opening the project file:\n\n{hata}",
    "Sayfalar arası bağlantı rengi": "Between-sheets connection color",
    "Sayfa içi bağlantı rengi": "Within-sheet connection color",
    "MCU gerekli": "MCU required",
    "MCU pin listesi için 'MCU / Ana İşlemci' kutusuna MCU designator'ını yaz "
    "(örn. U2).":
        "For the MCU pin list, type the MCU designator into the 'MCU / Main "
        "Processor' box (e.g. U2).",
    "Tek MCU": "Single MCU",
    "MCU pin listesi tek entegre içindir. İlk designator kullanılacak: {desig}":
        "The MCU pin list is for a single IC. The first designator will be used: "
        "{desig}",
    "Eksik": "Missing",
    "Önce geçerli bir proje dosyası seç.": "Select a valid project file first.",
    "Çıktı yolunu belirt.": "Specify the output path.",
    "Üretiliyor...": "Generating...",
    "Başlatılıyor… %p%": "Starting… %p%",
    "Tamamlandı  %p%": "Completed  %p%",
    "Başarısız": "Failed",
    "\n✓ TAMAMLANDI: {yol}": "\n✓ COMPLETED: {yol}",
    "Çıktı klasörü yok": "No output folder",
    "Henüz üretilmiş bir çıktı yok (veya dosya taşınmış).":
        "There is no generated output yet (or the file has been moved).",

    # --- gui.py: üretim hata mesajları (GeneratorThread) ------------------
    "BOM verisi yok": "No BOM data",
    "Pick&Place verisi yok (PCB gerekli)": "No Pick&Place data (PCB required)",
    "IC haritası üretilemedi (netlist yok)":
        "IC map could not be generated (no netlist)",
    "MCU pin listesi üretilemedi (MCU designator gir / netlist yok)":
        "MCU pin list could not be generated (enter an MCU designator / no netlist)",
    "PCB görüntüleyici üretilemedi (PCB dosyası yok/okunamadı)":
        "PCB viewer could not be generated (PCB file missing/unreadable)",
    "Birleşik görünüm üretilemedi": "Combined view could not be generated",
    "\nHATA: {hata}\n{iz}": "\nERROR: {hata}\n{iz}",

    # --- gui.py: bağımlılık listesi --------------------------------------
    "Bağımlılıklar ({sayi} paket):": "Dependencies ({sayi} packages):",
    "doğrudan": "direct",
    "alt bağımlılık": "sub-dependency",

    # --- gui.py: not taşıma (Dosya menüsü) ------------------------------
    "Notları Eski Çıktıdan Taşı…": "Transfer Notes From an Older Output…",
    "Eski HTML deki (veya _notlar.json daki) şematik notlarını yeni üretilen HTML e taşı":
        "Move schematic notes from an older HTML (or _notlar.json) into the newly generated HTML",
    "Not taşıma": "Note transfer",
    "Notların OKUNACAĞI dosya (eski HTML veya _notlar.json)":
        "File to READ notes FROM (older HTML or _notlar.json)",
    "Not kaynağı (*.html *.htm *.json)":
        "Note source (*.html *.htm *.json)",
    "Kaynak okunamadı: {hata}": "Could not read source: {hata}",
    "Bu dosyada not bulunamadı. Notların taşınabilmesi için görüntüleyicide önce Kaydet (HTML e göm) ya da Dışa (_notlar.json) kullanılmış olmalı.":
        "No notes found in this file. To transfer notes, first use Save (embed into the HTML) or Export (_notlar.json) in the viewer.",
    "Notların YAZILACAĞI HTML (yeni üretilen)":
        "HTML to WRITE notes INTO (the newly generated one)",
    "Görüntüleyici HTML (*.html *.htm)": "Viewer HTML (*.html *.htm)",
    "Kaynak ve hedef aynı dosya.": "Source and target are the same file.",
    "Hedefte zaten {sayi} not gömülü. Üzerine yazılsın mı?":
        "The target already has {sayi} embedded notes. Overwrite them?",
    "Notlar yazılamadı: {hata}": "Could not write notes: {hata}",
    " (birleşik görünümün şematik paneline)":
        " (into the schematic pane of the combined view)",
    "✓ {sayi} not taşındı: {kaynak} → {hedef}{ek}":
        "✓ {sayi} notes transferred: {kaynak} → {hedef}{ek}",
    "{sayi} not/kutu {hedef} dosyasına gömüldü. Dosyayı tarayıcıda Ctrl+F5 ile açınca notlar görünür.":
        "{sayi} notes/boxes embedded into {hedef}. Open the file with Ctrl+F5 in the browser to see them.",
}


# ---------------------------------------------------------------------------
# viewer.py üretim log'u ve ilerleme etiketleri.
# Anahtarlar `log()` / `prog()` çağrılarındaki şablonlarla BİREBİR aynıdır;
# "{a0}", "{a1:.1f}" gibi yer tutucular ve biçim belirteçleri AYNEN korunmalı
# (str.format() çalışma anında uygular — kaybolursa sayı biçimi bozulur).
# ---------------------------------------------------------------------------
_EN_LOG = {
    # --- genel akış / özet ------------------------------------------------
    "Proje: {a0}": "Project: {a0}",
    "{a0} şema bulundu.\n": "{a0} schematic(s) found.\n",
    "\n· Antet / firma logosu gizlendi ({a0} sayfa).":
        "\n· Title block / company logo hidden ({a0} sheet(s)).",
    "\n· Antet gizleme istendi ama sayfalarda antet bulunamadı.":
        "\n· Title block hiding was requested but no title block was found.",
    "Pass 1: SchDoc yükleme + SVG render...":
        "Pass 1: loading SchDoc + rendering SVG...",
    "\nPass 2: Pozisyon çıkarımı (block pinleri dahil)...":
        "\nPass 2: extracting positions (including block pins)...",
    "\nToplam {a0} farklı net adı toplandı (tüm sayfalar).":
        "\n{a0} distinct net names collected in total (all sheets).",
    "\n{a0} net · {a1} komponent": "\n{a0} nets · {a1} components",
    "\n{a0} net · {a1} komponent ({a2} multi-part birleştirildi)":
        "\n{a0} nets · {a1} components ({a2} multi-part merged)",
    "  OK {a0}  ({a1} net, {a2} block)": "  OK {a0}  ({a1} nets, {a2} blocks)",
    "  ERR {a0}: {a1}": "  ERR {a0}: {a1}",
    "  + {a0}: {a1} kesin pozisyon": "  + {a0}: {a1} exact position(s)",
    "  Boyut: {a0:.1f} KB": "  Size: {a0:.1f} KB",
    "  build: {a0}  ({a1:.1f} MB)": "  build: {a0}  ({a1:.1f} MB)",
    "  build: {a0}  ({a1:.2f} MB)": "  build: {a0}  ({a1:.2f} MB)",
    "  ! Component okuma hatası ({a0}): {a1}":
        "  ! Component read error ({a0}): {a1}",
    "  ! Block okuma hatası ({a0}): {a1}": "  ! Block read error ({a0}): {a1}",
    "  · metin çözücü toleranslı moda alındı (cp1252 → UTF-8 fallback, {a0} modül)":
        "  · text decoder switched to tolerant mode (cp1252 → UTF-8 fallback, "
        "{a0} module(s))",
    "  ! Not: altium_monkey {a0} kullanılıyor. Dikey pin adları (STM32 vb.) {a1} "
    "öncesinde yatay render edilir. Güncelleme önerilir: pip install --upgrade "
    "altium-monkey":
        "  ! Note: altium_monkey {a0} is in use. Vertical pin names (STM32 etc.) "
        "are rendered horizontally before {a1}. Upgrade recommended: pip install "
        "--upgrade altium-monkey",

    # --- dosya çözümleme --------------------------------------------------
    "  · PrjPcb referanslarından {a0} SchDoc çözüldü (path normalize edildi).":
        "  · {a0} SchDoc resolved from PrjPcb references (paths normalized).",
    "  · PrjPcb referanslarından {a0} PcbDoc çözüldü (path normalize edildi).":
        "  · {a0} PcbDoc resolved from PrjPcb references (paths normalized).",
    "  · PrjPcb parse edilemedi: {a0}": "  · PrjPcb could not be parsed: {a0}",
    "  · PrjPcb PcbDoc için parse edilemedi: {a0}":
        "  · PrjPcb could not be parsed for PcbDoc: {a0}",
    "  · Klasörden taranıyor (*.SchDoc)...": "  · Scanning the folder (*.SchDoc)...",
    "  · {a0} SchDoc dosyadan bulundu.": "  · {a0} SchDoc found on disk.",
    "  · {a0} okunamadı: {a1}": "  · {a0} could not be read: {a1}",
    "  · {a0} PcbDoc adayından **{a1}** seçildi ({a2}).":
        "  · **{a1}** selected out of {a0} PcbDoc candidate(s) ({a2}).",
    "  · BOM/PnP için PCB sabitlendi: {a0}": "  · PCB pinned for BOM/PnP: {a0}",
    "  · PcbDoc bağlanamadı ({a0}) — kütüphane kendi seçimini kullanacak.":
        "  · Could not bind PcbDoc ({a0}) — the library will use its own choice.",

    # --- netlist -----------------------------------------------------------
    "\nNetlist derleniyor (pin→net bağlantısı)...":
        "\nCompiling netlist (pin→net connectivity)...",
    "  ! Proje netlist ayarları okunamadı, varsayılan: {a0}":
        "  ! Project netlist settings could not be read, using defaults: {a0}",
    "  ✓ {a0} net, {a1} pin bağlantısı çıkarıldı":
        "  ✓ {a0} nets, {a1} pin connections extracted",
    "  · {a0} bağlı olmayan (NC) pin eklendi.":
        "  · {a0} unconnected (NC) pin(s) added.",
    "\n! Netlist modülü import edilemedi: {a0}":
        "\n! Netlist module could not be imported: {a0}",
    "! Netlist derleme hatası: {a0}": "! Netlist compilation error: {a0}",
    "  · Netlist PCB'den doğrulanıyor: {a0} (büyük board'da sürebilir)...":
        "  · Verifying netlist against the PCB: {a0} (may take a while on large "
        "boards)...",
    "  ✓ Netlist PCB'den kuruldu: {a0} PCB neti ({a1} pad; {a2} pin adı şematikten "
    "eşleşti; {a3} otomatik ad şematik etiket/port adıyla değiştirildi) + {a4} "
    "şematik-yalnız net korundu.":
        "  ✓ Netlist rebuilt from the PCB: {a0} PCB nets ({a1} pads; {a2} pin names "
        "matched from the schematic; {a3} auto-generated names replaced with "
        "schematic label/port names) + {a4} schematic-only net(s) preserved.",
    "  ! PCB komponentleri şematikle örtüşmüyor ({a0}/{a1}) — yanlış PcbDoc olabilir, "
    "şematik netlist'i korunuyor.":
        "  ! PCB components do not overlap with the schematic ({a0}/{a1}) — this may "
        "be the wrong PcbDoc, keeping the schematic netlist.",
    "  · PCB'de net'e bağlı pad yok — şematik netlist'i korunuyor.":
        "  · No pads attached to nets on the PCB — keeping the schematic netlist.",
    "  ! PCB netlist doğrulaması atlandı: {a0}":
        "  ! PCB netlist verification skipped: {a0}",
    "  · PCB netlist doğrulaması atlandı (PCB okunamadı): {a0}":
        "  · PCB netlist verification skipped (PCB unreadable): {a0}",
    "  · PCB bulunamadı — netlist PCB ile doğrulanamadı (şematik esas).":
        "  · No PCB found — netlist could not be verified against a PCB (schematic "
        "is authoritative).",
    "! Pin bağlantısı bulunamadı.": "! No pin connections found.",

    # --- tasarım verisi (BOM / PnP / varyant) -----------------------------
    "\nTasarım verileri (BOM / Pick&Place / Varyant)...":
        "\nDesign data (BOM / Pick&Place / Variants)...",
    "  ✓ BOM: {a0} komponent": "  ✓ BOM: {a0} components",
    "  ! BOM hatası: {a0}": "  ! BOM error: {a0}",
    "  ✓ Pick&Place: {a0} yerleşim (mm)": "  ✓ Pick&Place: {a0} placements (mm)",
    "  · Pick&Place atlandı (PCB yok veya hata): {a0}":
        "  · Pick&Place skipped (no PCB or an error occurred): {a0}",
    "  ✓ {a0} varyant: {a1}": "  ✓ {a0} variant(s): {a1}",
    "  · Varyant tanımlı değil": "  · No variants defined",
    "  ! Varyant okuma hatası: {a0}": "  ! Variant read error: {a0}",
    "! AltiumDesign yüklenemedi: {a0}": "! AltiumDesign could not be loaded: {a0}",
    "\n! AltiumDesign API yok (eski altium_monkey sürümü) — BOM/PnP atlanıyor.":
        "\n! AltiumDesign API missing (old altium_monkey version) — skipping BOM/PnP.",
    "  {a0} komponent · {a1} parametre sütunu":
        "  {a0} components · {a1} parameter column(s)",
    "  {a0} yerleşim ({a1})": "  {a0} placements ({a1})",
    "! BOM verisi yok — CSV üretilemedi.": "! No BOM data — CSV not generated.",
    "! Pick&Place verisi yok (PCB dosyası gerekli) — CSV üretilemedi.":
        "! No Pick&Place data (a PCB file is required) — CSV not generated.",

    # --- Excel çıktıları ---------------------------------------------------
    "\nIC Bağlantı Haritası hazırlanıyor...": "\nPreparing IC Connection Map...",
    "\nMCU pin listesi hazırlanıyor: {a0} ({a1} pin)":
        "\nPreparing MCU pin list: {a0} ({a1} pins)",
    "  · Ana işlemci(ler): {a0}": "  · Main processor(s): {a0}",
    "  · Ana işlemci otomatik seçildi: {a0} ({a1} pin). Belirli bir IC istiyorsan "
    "main_designators parametresiyle ver.":
        "  · Main processor auto-selected: {a0} ({a1} pins). Pass main_designators "
        "if you want a specific IC.",
    "  ! Uyarı: '{a0}' ana işlemci olarak girildi ama projede bulunamadı, atlanıyor.":
        "  ! Warning: '{a0}' was given as a main processor but was not found in the "
        "project, skipping.",
    "  · Hariç tutulan önekler: {a0} ({a1} komponent atlandı)":
        "  · Excluded prefixes: {a0} ({a1} component(s) skipped)",
    "  {a0} IC · {a1} sinyal satırı · ana işlemci: {a2}":
        "  {a0} ICs · {a1} signal rows · main processor: {a2}",
    "  {a0} — {a1} pin yazıldı": "  {a0} — {a1} pins written",
    "! Netlist yok — IC haritası üretilemedi.":
        "! No netlist — IC map could not be generated.",
    "! Netlist yok — MCU pin listesi üretilemedi.":
        "! No netlist — MCU pin list could not be generated.",
    "! MCU designator boş — hangi entegrenin pin listesi çıkarılacak belirtilmeli "
    "(örn 'U2').":
        "! MCU designator is empty — specify which IC's pin list to extract "
        "(e.g. 'U2').",
    "! '{a0}' projede bulunamadı. Mevcut entegrelerden birini gir.":
        "! '{a0}' was not found in the project. Enter one of the existing ICs.",
    "! {a0} için pin bulunamadı.": "! No pins found for {a0}.",
    "! openpyxl yok, Excel üretilemedi: {a0}  (pip install openpyxl)":
        "! openpyxl is missing, Excel not generated: {a0}  (pip install openpyxl)",

    # --- PCB: cross-probe / katmanlar / geometri --------------------------
    "\nPCB cross-probe: {a0}": "\nPCB cross-probe: {a0}",
    "  ✓ {a0} komponent konumu · board {a1:.0f}×{a2:.0f}mm":
        "  ✓ {a0} component positions · board {a1:.0f}×{a2:.0f}mm",
    "\n· PCB dosyası bulunamadı — cross-probe atlanıyor.":
        "\n· PCB file not found — skipping cross-probe.",
    "\n! AltiumPcbDoc API yok — PCB cross-probe atlanıyor.":
        "\n! AltiumPcbDoc API missing — skipping PCB cross-probe.",
    "\nPCB (geometri): {a0}": "\nPCB (geometry): {a0}",
    "! PCB'de komponent bulunamadı (parse boş).":
        "! No components found on the PCB (empty parse).",
    "! PCB komponent konumu çıkarılamadı.":
        "! Component positions could not be extracted from the PCB.",
    "! PCB parse hatası: {a0}": "! PCB parse error: {a0}",
    "\n! PCB dosyası bulunamadı veya parse edilemedi.":
        "\n! PCB file not found or could not be parsed.",
    "! Geometri çıkarılamadı.": "! Geometry could not be extracted.",
    "  ! katman referansı okunamadı: {a0}":
        "  ! layer reference could not be read: {a0}",
    "  ✓ geometri: {a0} iz · {a1} yay · {a2} pad · {a3} via · "
    "{a4}+{a5} region/metin · {a6} katman":
        "  ✓ geometry: {a0} tracks · {a1} arcs · {a2} pads · {a3} vias · "
        "{a4}+{a5} regions/texts · {a6} layers",
    " ({a0} metin atlandı)": " ({a0} text(s) skipped)",
    "  · metin poligonları atlandı: {a0}": "  · text polygons skipped: {a0}",

    # --- 3D ----------------------------------------------------------------
    "  ✓ 3D: board {a0:.0f}×{a1:.0f}mm · {a2:.2f}mm · {a3} STEP + {a4} extrude gövde "
    "· {a5} gerçek delik":
        "  ✓ 3D: board {a0:.0f}×{a1:.0f}mm · {a2:.2f}mm · {a3} STEP + {a4} extruded "
        "bodies · {a5} real holes",
    "  ✓ 3D STEP: {a0} model tessellate edildi (~{a1} üçgen)":
        "  ✓ 3D STEP: {a0} models tessellated (~{a1} triangles)",
    "  · 3D çıkarılamadı: {a0}": "  · 3D could not be extracted: {a0}",
    "  · 3D: {a0} gövdenin yönelimi Altium'un gövde outline'ı / pad delikleriyle "
    "düzeltildi (model baş aşağı geliyordu)":
        "  · 3D: orientation of {a0} bodies corrected against Altium's own body "
        "outline / pad holes (the model came in upside down)",
    "  · 3D: {a0} gövde Altium'da tam saydam (opacity 0) — çizilmedi "
    "(mekanik hacim/gabari)":
        "  · 3D: {a0} bodies are fully transparent in Altium (opacity 0) — not drawn "
        "(mechanical volume/keepout)",
    "  · cascadio/trimesh yok — STEP yerine extrude gövdeler kullanılacak.":
        "  · cascadio/trimesh missing — extruded bodies will be used instead of STEP.",
    "  · gömülü model girişleri okunamadı: {a0}":
        "  · embedded model entries could not be read: {a0}",
    "  · STEP '{a0}' atlandı: {a1}": "  · STEP '{a0}' skipped: {a1}",
    "  ✓ 3D yüzey dokusu (geometriden): top {a0}KB + bot {a1}KB (gzip)":
        "  ✓ 3D surface texture (from geometry): top {a0}KB + bottom {a1}KB (gzip)",
    "  · yüzey dokusu atlandı: {a0}": "  · surface texture skipped: {a0}",
    "  · geometriden yüzey dokusu üretilemedi: {a0}":
        "  · surface texture could not be generated from geometry: {a0}",

    # --- birleşik görünüm ---------------------------------------------------
    "Birleşik görünüm: şematik + PCB toplanıyor...":
        "Combined view: collecting schematic + PCB...",
    "  · Şematik bilgisi alınamadı (yine de devam): {a0}":
        "  · Schematic data unavailable (continuing anyway): {a0}",
    "  · Cross-probe için {a0} net PCB adıyla eşleştirildi (ör. şematik etiketi ↔ "
    "NetU5_20 gibi otomatik PCB adı).":
        "  · {a0} nets matched to their PCB names for cross-probe (e.g. schematic "
        "label ↔ an auto-generated PCB name such as NetU5_20).",
    "  · PCB yok — birleşik görünümde sağ panel boş olacak.":
        "  · No PCB — the right panel of the combined view will be empty.",

    # --- çıktı satırları ---------------------------------------------------
    "\n✓ HTML üretildi: {a0}": "\n✓ HTML generated: {a0}",
    "\n✓ JSON üretildi: {a0}": "\n✓ JSON generated: {a0}",
    "\n✓ BOM CSV üretildi: {a0}": "\n✓ BOM CSV generated: {a0}",
    "\n✓ Pick&Place CSV üretildi: {a0}": "\n✓ Pick&Place CSV generated: {a0}",
    "\n✓ IC Bağlantı Haritası üretildi: {a0}":
        "\n✓ IC Connection Map generated: {a0}",
    "\n✓ MCU pin listesi üretildi: {a0}": "\n✓ MCU pin list generated: {a0}",
    "\n✓ PCB (geometri) görüntüleyici üretildi: {a0}":
        "\n✓ PCB (geometry) viewer generated: {a0}",
    "\n✓ Birleşik görünüm üretildi: {a0}": "\n✓ Combined view generated: {a0}",

    # --- üretimi durduran hata (GUI'de "HATA:" satırı olarak görünür) -----
    "3D STEP modelleri için gerekli bağımlılık(lar) eksik: {a0}.\n"
    "Kur:  py -3.12 -m pip install {a1}\n"
    "(Bu paketler olmadan birleşik görünümün 3D sekmesi gerçek STEP "
    "geometrisi yerine basit extrude kutular gösterir.)":
        "Dependencies required for 3D STEP models are missing: {a0}.\n"
        "Install:  py -3.12 -m pip install {a1}\n"
        "(Without these packages the 3D tab of the combined view shows simple "
        "extruded boxes instead of real STEP geometry.)",

    # --- kütüphane (altium_monkey) uyarı özetleri -------------------------
    " ({a0} kayıt)": " ({a0} records)",
    "  · İşaretsiz UTF-8 metin kurtarıldı{a0} — bir parametre/metin `%UTF8%` "
    "işareti olmadan UTF-8 kaydedilmiş (genelde datasheet'ten yapıştırılmış "
    "°C / ± gibi karakterler). **Veri kaybı yok**; uyarıyı kaldırmak için o "
    "sayfaları Altium'da açıp kaydetmek yeterli.":
        "  · Recovered unmarked UTF-8 text{a0} — a parameter/text was saved as UTF-8 "
        "without the `%UTF8%` marker (usually characters such as °C / ± pasted from "
        "a datasheet). **No data loss**; to clear the warning it is enough to open "
        "and re-save those sheets in Altium.",
    "  · Kütüphane uyarısı{a0}: {a1}": "  · Library warning{a0}: {a1}",

    # --- ilerleme çubuğu etiketleri (prog) --------------------------------
    "Şematik verisi toplanıyor": "Collecting schematic data",
    "Sayfa render: {a0}": "Rendering sheet: {a0}",
    "Pozisyon çıkarımı: {a0}": "Extracting positions: {a0}",
    "Netlist derleniyor": "Compiling netlist",
    "Tasarım verileri": "Design data",
    "PCB konumları (cross-probe)": "PCB positions (cross-probe)",
    "Şematik verisi hazır": "Schematic data ready",
    "HTML oluşturuluyor": "Building HTML",
    "Şematik HTML oluşturuluyor": "Building schematic HTML",
    "PCB okunuyor": "Reading PCB",
    "PCB geometrisi çıkarılıyor": "Extracting PCB geometry",
    "Geometri çıkarılıyor": "Extracting geometry",
    "Şematik komponent bilgisi": "Schematic component data",
    "3D verisi": "3D data",
    "Birleştiriliyor ve yazılıyor": "Merging and writing",
    "Tamamlandı": "Completed",

    # --- not taşıma (write_annotations) ---------------------------------
    "Bu dosya bir şematik görüntüleyici değil (not yuvası bulunamadı).":
        "This file is not a schematic viewer (no note slot found).",
}

_EN.update(_EN_LOG)


# ---------------------------------------------------------------------------
# Üretilen HTML görüntüleyicilerin arayüzü (şematik / PCB / geometri / 3D /
# birleşik kabuk). Anahtarlar viewer.py şablonlarındaki ⟪…⟫ işaretlerinin
# İÇİNDEKİ metinle BİREBİR aynıdır; `_tr_html()` üretim sonunda çevirir.
#
# KURAL: çeviri metni ' " < > karakterleri İÇERMEMELİ — bu metinler tek/çift
# tırnaklı JS dizgelerine ve HTML attribute'larına gömülür, tırnak kaçışı
# şablonu bozar. (Kapsama denetimi: tools/check_html_i18n.py)
# ---------------------------------------------------------------------------
_EN_HTML = {
    # --- ortak: araç çubuğu / gezinme -------------------------------------
    "Tam ekran aç / kapat ( F11 )": "Toggle full screen ( F11 )",
    "Tümü": "All",
    "Güç": "Power",
    "Sinyal": "Signal",
    "Hepsi": "All",
    "Kalan": "Remaining",
    "Temizle": "Clear",
    "Kapat": "Close",
    "Sıfırla": "Reset",
    "Sığdır": "Fit",
    "Yaklaş ( + )": "Zoom in ( + )",
    "Uzaklaş ( − )": "Zoom out ( − )",
    "Üst": "Top",
    "Alt": "Bottom",
    "Üst/Alt": "Top/Bottom",
    "Üst katmanlar": "Top layers",
    "Alt katmanlar": "Bottom layers",
    "Katmanlar": "Layers",
    "Katman": "Layer",
    "Netler": "Nets",
    "Komponentler": "Components",
    "Değer": "Value",
    "Açıklama": "Description",
    "Dönüş": "Rotation",
    "PCB Konumu": "PCB Position",
    "Şema Sayfası": "Schematic Sheet",
    "Sayfa…": "Sheet…",
    "Sayfaya git": "Go to sheet",
    "Zemin": "Background",
    "Zemin rengi": "Background color",
    "Görüntü": "Image",
    "Ölç": "Measure",
    "Çevir": "Flip",
    "Parçalar": "Parts",
    "Döndür": "Rotate",
    "Dışa": "Export",
    "İçe": "Import",
    "Kopyala": "Copy",
    "Paneli göster": "Show panel",
    "Paneli gizle ( B )": "Hide panel ( B )",
    "Sol paneli gizle / göster": "Hide / show the left panel",
    "Bu pencereyi aç / kapat": "Open / close this window",
    "Bu görünüm hakkında": "About this view",
    "Küçült / Büyüt": "Collapse / expand",
    "Sürükle: yeniden boyutlandır": "Drag: resize",
    "Seçimi temizle": "Clear the selection",
    "Görünümü sıfırla": "Reset the view",
    "Renk Pickers": "Color pickers",

    # --- arama -------------------------------------------------------------
    "Komponent / net": "Component / net",
    "Komponent / net ara...": "Search component / net...",
    "net ara... ( / )": "search net... ( / )",
    "komponent ara... ( / )": "search component... ( / )",
    "Arama kutusuna git": "Go to the search box",
    "Aramada ilk sonucu seç": "Select the first result in the search",
    "eşleşen yok": "no match",
    "eşleşen net yok": "no matching net",
    "eşleşen komponent yok": "no matching component",
    "komponent daha": "more components",
    "de bulunamadı:": " not found on:",
    "sayfa ara... ( / )": "search sheet... ( / )",
    "eşleşen sayfa yok": "no matching sheet",

    # --- şematik hiyerarşi (KiCad tarzı ağaç + sayfa gezinme) -------------
    "Hiyerarşi": "Hierarchy",
    "Şematik Hiyerarşi": "Schematic Hierarchy",
    "Şematik hiyerarşi ( H )": "Schematic hierarchy ( H )",
    "Hiyerarşi sekmesini aç": "Open the hierarchy tab",
    "Hiyerarşide sayfaya tık": "Click a sheet in the hierarchy",
    "O sayfaya git — alt sayfaları ok ile aç/kapat":
        "Go to that sheet — expand/collapse children with the arrow",
    "Block (sheet symbol) yazısına tık": "Click a block (sheet symbol) label",
    "Alt sayfaya gir (hiyerarşide o dala geçilir)":
        "Enter the child sheet (the hierarchy follows that branch)",
    "tıkla: alt sayfaya gir": "click: enter the child sheet",
    "tıkla: bu sayfaya git": "click: go to this sheet",
    "Üst sayfa": "Parent",
    "üst sayfa": "parent sheet",
    "hiyerarşi": "hierarchy",
    "sayfa": "page",
    "(bu projede yok)": "(not in this project)",
    "hedef SchDoc bu projede yok": "the target SchDoc is not in this project",
    "Üst sayfaya dön — hiyerarşide bir seviye yukarı":
        "Go up to the parent sheet — one level up in the hierarchy",
    "Üst sayfaya dön — hiyerarşide bir seviye yukarı ( Alt+Backspace )":
        "Go up to the parent sheet — one level up in the hierarchy ( Alt+Backspace )",
    "Ana (kök) sayfaya git": "Go to the root sheet",
    "Ana (kök) sayfaya git ( Alt+Home )": "Go to the root sheet ( Alt+Home )",
    "Kök": "Root",
    "Kök sayfa bulunamadı": "No root sheet found",
    "Sayfa geçmişinde geri / ileri": "Back / forward in the sheet history",
    "Zaten en üst sayfadasın": "Already at the top of the hierarchy",
    "Zaten ana sayfadasın": "Already on the root sheet",
    "Geçmişte daha geri gidilemez": "No earlier sheet in the history",
    "Geçmişte daha ileri gidilemez": "No later sheet in the history",
    "Tümünü aç": "Expand all",
    "Tümünü kapat": "Collapse all",

    # --- kısayol / yardım tabloları ---------------------------------------
    "Kısayollar (?)": "Shortcuts (?)",
    "Yardım ( ? )": "Help ( ? )",
    "tüm kısayollar": "all shortcuts",
    "Fare": "Mouse",
    "Klavye": "Keyboard",
    "Fare / Klavye": "Mouse / Keyboard",
    "Dokunmatik": "Touch",
    "Dokunmatik (telefon / tablet)": "Touch (phone / tablet)",
    "Sürükle": "Drag",
    "Tekerlek": "Wheel",
    "Tıkla": "Click",
    "Çift tıkla": "Double-click",
    "Tek dokunuş": "Single tap",
    "Çift dokunuş": "Double tap",
    "Dokun / çift dokun": "Tap / double tap",
    "Tek parmak": "One finger",
    "Tek parmak sürükle": "One-finger drag",
    "İki parmak": "Two fingers",
    "İki parmak (pinch)": "Two fingers (pinch)",
    "Kaydır": "Pan",
    "Kanvası kaydır (pan)": "Pan the canvas",
    "Mouse altına zoom": "Zoom under the mouse",
    "İmleç altına zoom": "Zoom under the cursor",
    "Yakınlaştır + kaydır": "Zoom + pan",
    "Parmakların ortasına zoom + aynı anda kaydır":
        "Zoom to the midpoint of the fingers + pan at the same time",
    "Fare tıklaması ile aynı (net / designator / block)":
        "Same as a mouse click (net / designator / block)",
    "Çift tıklama ile aynı (sayfayı sığdır, notu düzenle)":
        "Same as a double-click (fit the sheet, edit the note)",
    "Shift + tık": "Shift + click",
    "Sil (Del)": "Delete (Del)",

    # --- şematik görüntüleyici --------------------------------------------
    "Şematik": "Schematic",
    "Şematik + PCB": "Schematic + PCB",
    "Şematik + PCB ·": "Schematic + PCB ·",
    "Böl": "Split",
    "Sadece şematik ( 1 )": "Schematic only ( 1 )",
    "Yan yana ( 2 )": "Side by side ( 2 )",
    "Sadece PCB ( 3 )": "PCB only ( 3 )",
    "3D görünüm ( 4 )": "3D view ( 4 )",
    "Bir tarafta komponente tıkla → diğerlerinde otomatik gösterilir":
        "Click a component on one side → it is shown automatically on the others",
    "PCB hazırlanıyor…": "Preparing PCB…",
    "3D hazırlanıyor…": "Preparing 3D…",
    "Net adına tık (şema/sol panel)": "Click a net name (schematic/left panel)",
    "Net seç, bağlantıları göster": "Select a net, show its connections",
    "Çoklu net karşılaştırma (max 4)": "Compare multiple nets (max 4)",
    "Comps listesinde tık": "Click in the Comps list",
    "Komponente zoom + pulse + detay popup":
        "Zoom to the component + pulse + detail popup",
    "Designator'a tık (şema)": "Click a designator (schematic)",
    "Komponent detay popup'ı aç": "Open the component detail popup",
    "Sayfa kartına çift tık": "Double-click a sheet card",
    "O sayfayı ekrana sığdır": "Fit that sheet to the screen",
    "Tüm sayfaları sığdır": "Fit all sheets",
    "Son sayfaya fit zoom": "Fit zoom to the last sheet",
    "Sığdır · panel · temizle · yardım": "Fit · panel · clear · help",
    "Sayfalar arası yay rengi": "Inter-sheet arc color",
    "Sayfa içi eğri rengi": "Within-sheet curve color",
    "Yay renklerini anlık değiştir": "Change the arc colors instantly",
    "Toolbar'daki renkli kareler": "The colored squares in the toolbar",
    "tıkla: bağlantı yayları · Shift+tık: karşılaştır":
        "click: connection arcs · Shift+click: compare",
    "tıkla: detay + cross-probe": "click: detail + cross-probe",
    "parça (multi-part)": "part (multi-part)",
    "güç": "power",
    "toprak": "ground",
    "sinyal": "signal",
    "Bu komponent PCB\\'de bulunamadı.":
        "This component was not found on the PCB.",
    "Bu tarayıcı sıkıştırılmış şemayı açamıyor (DecompressionStream gerekli).":
        "This browser cannot decompress the schematic (DecompressionStream "
        "required).",
    "Bu tarayıcı sıkıştırılmış görünümü açamıyor (DecompressionStream gerekli).":
        "This browser cannot decompress the view (DecompressionStream required).",
    "Lütfen tarayıcıyı güncelleyin.": "Please update your browser.",
    "Bu tarayıcı sıkıştırılmış geometriyi açamıyor (DecompressionStream gerekli).":
        "This browser cannot decompress the geometry (DecompressionStream "
        "required).",
    "LOD: döndürme/zoom sırasında çözünürlük düşürülür (akıcılık), durunca "
    "netleşir":
        "LOD: resolution is lowered while rotating/zooming (smoothness) and "
        "sharpens when it stops",
    "html2canvas yüklenmedi": "html2canvas did not load",
    "Görünümü PNG indir": "Download the view as PNG",
    "Kopyalama hatası:": "Copy error:",

    # --- not / kutu (annotation) araçları ----------------------------------
    "Not / kutu araçları": "Note / box tools",
    "Toolbar: Not / Kutu": "Toolbar: Note / Box",
    "Tıklanan yere doğrudan yazı yaz / alanı kutu içine al (Esc iptal)":
        "Type directly where you click / box in an area (Esc cancels)",
    "Not ekle: butona bas, şemada istediğin yere tıkla ve DOĞRUDAN yaz (dışına "
    "tıkla = bitir, Enter = yeni satır). Sonradan: çift tık düzenle · sürükle "
    "taşı · seç + Del sil · A−/A+ yazı boyutu":
        "Add a note: press the button, click anywhere on the schematic and type "
        "DIRECTLY (click outside = finish, Enter = new line). Afterwards: "
        "double-click to edit · drag to move · select + Del to delete · A−/A+ "
        "font size",
    "Kutu içine al: butona bas, sürükleyerek çerçeve çiz (Esc iptal). Sonradan: "
    "kenarına tıkla seç → sürükle taşı · köşe tutamaçlarıyla boyutlandır · Del "
    "sil · −/+ kenar kalınlığı":
        "Box in: press the button and drag to draw a frame (Esc cancels). "
        "Afterwards: click its edge to select → drag to move · resize with the "
        "corner handles · Del to delete · −/+ border width",
    "Not ve kutuları HTML dosyasının içine göm ve kaydet. Chromium'da AÇIK "
    "DOSYANIN ÜSTÜNE yazabilir (ilk kayıtta dosyayı seç; aynı oturumda "
    "sonrakiler sessiz). Firefox'ta kopya indirir. Paylaşınca/başka bilgisayarda "
    "da görünür":
        "Embed the notes and boxes into the HTML file and save. On Chromium it "
        "can overwrite THE OPEN FILE (pick the file on the first save; later "
        "saves in the same session are silent). On Firefox it downloads a copy. "
        "They stay visible when shared or opened on another computer",
    "Not/kutuya tık + sürükle": "Click + drag a note/box",
    "Seç ve taşı · kutuda köşe tutamacı: boyutlandır":
        "Select and move · corner handle on a box: resize",
    "Nota çift tık": "Double-click a note",
    "Yerinde düzenle (boş bırak = sil)": "Edit in place (leave empty = delete)",
    "Seçiliyken Del · mini bar −/+": "Del while selected · mini bar −/+",
    "Sil · yazı boyutu / kenar kalınlığı": "Delete · font size / border width",
    "Kenardan sürükle: taşı · Köşe tutamacı: boyutlandır · Del: sil":
        "Drag the edge: move · Corner handle: resize · Del: delete",
    "Sürükle: taşı · Çift tık: düzenle · Seç + Del: sil":
        "Drag: move · Double-click: edit · Select + Del: delete",
    "Parmakla da çalışır (yaz, çiz, taşı, boyutlandır)":
        "Works with touch too (type, draw, move, resize)",
    "Yazı boyutu / kenar kalınlığı artır": "Increase font size / border width",
    "Yazı boyutu / kenar kalınlığı azalt": "Decrease font size / border width",
    "Renk (not yazısı / kutu kenarı)": "Color (note text / box border)",

    # --- PCB görüntüleyici --------------------------------------------------
    "Geometri tabanlı": "Geometry-based",
    "Bu katmanı en üste getir (tekrar bas: normal sıra)":
        "Bring this layer to the front (press again: normal order)",
    "Katman sırası normal": "Layer order is normal",
    "en üstte": "at the front",
    "Tüm katmanları göster": "Show all layers",
    "Tüm katmanları gizle": "Hide all layers",
    "Üst / alt katman setini değiştir ( T )":
        "Switch the top / bottom layer set ( T )",
    "Pad etiketleri · Üst/Alt katman seti": "Pad labels · Top/Bottom layer set",
    "Pad no + net ( P )": "Pad number + net ( P )",
    "Komponent seç (detay + cross-probe)":
        "Select a component (detail + cross-probe)",
    "Altındaki net'i vurgula": "Highlight the net underneath",
    "90° döndür ( R )": "Rotate by 90° ( R )",
    "Alt yüzden bakış / ayna ( X )": "View from the bottom / mirror ( X )",
    "Döndür / çevir (ayna)": "Rotate / flip (mirror)",
    "Ölçüm ( M )": "Measurement ( M )",
    "Ölçüm:": "Measurement:",
    "Ölçüm (mm/mil, pad merkezine yapışır)":
        "Measurement (mm/mil, snaps to the pad center)",
    "Ölçüm: iki noktaya tıkla (pad merkezine yapışır) · Esc iptal":
        "Measurement: click two points (snaps to the pad center) · Esc cancels",
    "· Esc kapatır": "· Esc closes",
    "● TOP katmanı": "● TOP layer",
    "● BOTTOM katmanı": "● BOTTOM layer",
    "primitif": "primitives",
    "Sürükle / tek parmak: kaydır · Tekerlek / iki parmak: zoom · Tıkla: "
    "komponent · Çift tık: net":
        "Drag / one finger: pan · Wheel / two fingers: zoom · Click: component "
        "· Double-click: net",

    # --- BOM / montaj paneli ------------------------------------------------
    "BOM · Montaj": "BOM · Assembly",
    "Montaj işaretlerini dosyaya kaydet": "Save the assembly marks to a file",
    "Kaydedilmiş işaretleri yükle": "Load saved marks",
    "Tüm işaretleri temizle": "Clear all marks",
    "Tum montaj isaretleri silinsin mi?": "Delete all assembly marks?",
    "komponent vurgulandi": "components highlighted",
    "grup dosyaya aktarildi": "groups exported to the file",
    "grup yuklendi": "groups loaded",
    "grup bu boardda yok": "groups are not on this board",
    # SVG sürümünde metin JS'te kaçışlıdır (board\'da) — anahtar ÇALIŞMA-ANI
    # biçimindedir, yani ters bölüyü İÇERİR (bkz. tools/check_html_i18n.py)
    "Gecersiz dosya": "Invalid file",
    "Kaydetme hatası:": "Save error:",
    "Export hatası:": "Export error:",

    # --- 3D görünüm ---------------------------------------------------------
    "Komponentleri gizle/göster — çıplak board'u incele":
        "Hide/show components — inspect the bare board",
    "Sürükle / tek parmak: döndür · Tekerlek / iki parmak: imlecin olduğu yere "
    "zoom · Sağ-sürükle veya iki parmak kaydır: taşı · Tıkla: komponent":
        "Drag / one finger: rotate · Wheel / two fingers: zoom to the cursor · "
        "Right-drag or two-finger pan: move · Click: component",
    "WebGL bu tarayıcıda kullanılamıyor.":
        "WebGL is not available in this browser.",
    "Bu projede 3D verisi bulunamadı.": "No 3D data was found in this project.",
    "Bu projede okunabilir PCB dosyası bulunamadı.":
        "No readable PCB file was found in this project.",

    # --- görsel doğrulamada yakalanan kalanlar ----------------------------
    "Not": "Note",
    "Kutu": "Box",
    "komponent": "components",
    "aramayla daralt": "narrow it down with the search",
    "Esc temizler": "Esc clears",
    "Kaydet": "Save",
    # canvas yardım tablosu — kaynakta çok satırlı, her satır ayrı anahtar
    "Değer+footprint grubuna tıkla → grubun tamamı":
        "Click a value+footprint group and the whole group is",
    "vurgulanır; ✓ ile montaj takibi (tarayıcıda saklanır, Dışa/İçe ile taşınır)":
        "highlighted; track assembly with ✓ (kept in the browser, moved with "
        "Export/Import)",
    "Board SVG olarak değil, ham geometri (iz/pad/via/":
        "The board is embedded as raw geometry (track/pad/via/",
    "region/metin) olarak gömülür ve canvas'a çizilir → dosya çok küçük,":
        "region/text) instead of SVG and drawn on a canvas → a much smaller file,",
    "her zoom'da akıcı.": "smooth at every zoom level.",

    # --- şematik: notları dışa/içe aktarma -------------------------------
    "Notları dosyaya aktar (proje_notlar.json iner). Yeniden üretilen HTML e ya da başka bilgisayara taşımanın tarayıcıdan bağımsız yolu — localStorage taşınmaz":
        "Export notes to a file (downloads project_notlar.json). The browser-independent way to move them into a regenerated HTML or onto another computer — localStorage does not travel",
    "Notları dosyadan yükle: _notlar.json VEYA notları gömülü eski bir HTML seçilebilir. Mevcut notlar silinmez, üzerine eklenir":
        "Load notes from a file: pick a _notlar.json OR an older HTML with embedded notes. Existing notes are kept and the imported ones are added",
    "Aktarılacak not yok": "No notes to export",
    "not dosyaya aktarıldı": "notes exported to file",
    "Dosyada not bulunamadı": "No notes found in the file",
    "not yüklendi — kalıcı olması için Kaydet":
        "notes loaded — press Save to make it permanent",
}

_EN.update(_EN_HTML)

## @brief Dil kodu → çeviri sözlüğü. Kaynak dilin girdisi yoktur (metin aynen döner).
_CATALOGS = {"en": _EN}

## @brief O anda etkin dil kodu.
_current = SOURCE_LANGUAGE


def language() -> str:
    """@brief Etkin dil kodunu döndürür ("tr" | "en").

    @return Dil kodu.
    """
    return _current


def set_language(code: str) -> str:
    """@brief Etkin dili değiştirir (bilinmeyen kod kaynak dile düşer).

    @param code Dil kodu ("tr" | "en")
    @return Gerçekten ayarlanan dil kodu.
    """
    global _current
    _current = code if code in LANGUAGES else SOURCE_LANGUAGE
    return _current


def tr(text: str) -> str:
    """@brief Metni etkin dile çevirir; karşılığı yoksa AYNEN döndürür.

    @param text Türkçe kaynak metin (katalog anahtarı)
    @return Çevrilmiş metin (ya da kaynak metnin kendisi)
    """
    if text is None:
        return text
    return _CATALOGS.get(_current, {}).get(text, text)


def missing_keys(sample_texts) -> list:
    """@brief Katalogda karşılığı olmayan metinleri listeler (geliştirme yardımcısı).

    @param sample_texts Denetlenecek Türkçe metinler (iterable)
    @return Çevirisi eksik metinler (sıralı, tekrarsız)
    """
    return sorted({t for t in sample_texts if t and t not in _EN})


# ---------------------------------------------------------------------------
# Widget metinlerinin yedeklenmesi / yeniden uygulanması
# ---------------------------------------------------------------------------
# Hangi widget sınıfında hangi özellikler çevrilir. QLineEdit'in "text"i
# KULLANICI VERİSİDİR — asla yedeklenmez/çevrilmez (yalnız placeholder).
def _translatable_props(widget) -> tuple:
    """@brief Bir widget için çevrilebilir Qt özelliklerini belirler.

    @param widget Qt widget'ı
    @return Özellik adları demeti (ör. ("text", "toolTip"))
    """
    from PyQt5 import QtWidgets

    props = ["toolTip"]
    if isinstance(widget, QtWidgets.QGroupBox):
        props.append("title")
    elif isinstance(widget, QtWidgets.QAbstractButton):  # QPushButton, QCheckBox…
        props.append("text")
    elif isinstance(widget, QtWidgets.QLabel):
        props.append("text")
    elif isinstance(widget, QtWidgets.QLineEdit):
        props.append("placeholderText")  # "text" KULLANICI VERİSİ → dokunma
    elif isinstance(widget, QtWidgets.QProgressBar):
        props.append("format")
    return tuple(props)


def snapshot_widgets(root, exclude=()) -> list:
    """@brief Bir pencere altındaki tüm çevrilebilir metinleri (KAYNAK dilde) yedekler.

    @details Dil değişiminde metinler bu yedekten yeniden çevrilir; aksi halde
    İngilizceye çevrilmiş metin bir sonraki geçişte anahtar olarak bulunamaz ve
    Türkçeye dönüş mümkün olmazdı.

    @param root Kök widget (genelde QMainWindow)
    @param exclude Metni ETİKET DEĞİL VERİ olan widget'ların objectName'leri
                   (ör. renk butonları "#4ec9b0" gösterir; yedekten geri
                   yazılırsa kullanıcının seçtiği rengi ezer)
    @return [(widget, özellik_adı, kaynak_metin), ...]
    """
    from PyQt5 import QtWidgets

    skip = set(exclude)
    snap = []
    widgets = [root] + root.findChildren(QtWidgets.QWidget)
    for w in widgets:
        if w.objectName() in skip:
            continue
        for prop in _translatable_props(w):
            if isinstance(w, QtWidgets.QMainWindow) and prop != "toolTip":
                continue  # pencere başlığı sürüm içerir, ayrı yönetilir
            value = w.property(prop)
            if isinstance(value, str) and value.strip():
                snap.append((w, prop, value))
    return snap


def apply_snapshot(snapshot) -> None:
    """@brief Yedeklenen kaynak metinleri etkin dile çevirerek geri yazar.

    @param snapshot snapshot_widgets() çıktısı
    """
    for widget, prop, source in snapshot:
        try:
            widget.setProperty(prop, tr(source))
        except RuntimeError:
            pass  # widget yok edilmiş (kapanış sırası) — sessizce atla
