
# Schematic Viz Generator (EN)

> A PyQt5 desktop application that converts Altium schematic and PCB projects into **interactive, single-file HTML viewers** — no server required.

![Version](https://img.shields.io/badge/version-2.25.0-blue.svg)
![Python](https://img.shields.io/badge/python-3.10%2B-3776AB.svg?logo=python\&logoColor=white)
![GUI](https://img.shields.io/badge/GUI-PyQt5-41CD52.svg?logo=qt\&logoColor=white)
![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Linux-lightgrey.svg)
![License](https://img.shields.io/badge/license-AGPL--3.0--or--later-orange.svg)
[![Buy Me A Coffee](https://img.shields.io/badge/Buy%20Me%20A%20Coffee-support-FFDD00.svg?logo=buymeacoffee\&logoColor=black)](https://buymeacoffee.com/cansizmikab)

---

## ❤️ Support

If this project helps you, consider supporting its development ☕

This tool is developed in my free time and your support helps me maintain and improve it.

<a href="https://buymeacoffee.com/cansizmikab" target="_blank">
  <img src="https://cdn.buymeacoffee.com/buttons/v2/default-yellow.png" alt="Buy Me A Coffee" height="45" width="163">
</a>

👉 [buymeacoffee.com/cansizmikab](https://buymeacoffee.com/cansizmikab)

---

## Project Overview

Select your project, click a button — and get a **double-clickable, single-file, portable HTML output**
(or Excel / CSV / JSON).

No web server, no installation, no internet required. Works directly via `file://`.

![Main UI](img/app.jpg)

---

## ✨ Key Features

* **Bilingual — Turkish / English**
  Switch language from **Settings → Language**; the choice is remembered. It applies
  everywhere: the desktop UI, the generation log and progress labels, **and the generated
  HTML viewers** — a viewer keeps the language it was generated in, so you can hand an
  English board to a colleague and a Turkish one to another.

* **Menu bar with keyboard shortcuts**
  File / Generate / View / Settings / Help — every generator is also reachable from the
  menu (`Ctrl+1..3` for the viewers), plus `Ctrl+O` open project, `Ctrl+B` open last
  output, `F11` full screen, `F1` about.

* **Interactive Schematic Viewer**
  All pages in a single pan/zoom canvas, clickable nets and components, selectable text like PDF.

* **Schematic Hierarchy panel (KiCad-style)**
  A sheet tree in the sidebar — root schematic → sheet symbols → child sheets, with page
  numbers and collapsible branches. Repeat channels appear as separate instances, so
  `Alt+Backspace` ("leave sheet") always returns to the right parent. Plus `Alt+Home`
  for the root and `Alt+←/→` for sheet history.

* **PCB Viewer (geometry / canvas)**
  Full-screen layered view similar to Altium — layer toggling, copper/net highlighting,
  cross-probing. Instead of embedding layer SVGs it embeds the raw board geometry
  (tracks/pads/vias/regions/text) and draws it on a `<canvas>`: much smaller files and
  smooth at any zoom, plus rotate/mirror, measurement and touch support.

* **Schematic + PCB + 3D in One HTML**
  Side-by-side layout with bidirectional cross-probing and real embedded **STEP 3D models**.

* **Excel & CSV Outputs**
  MCU pin list, IC connection map, BOM, Pick & Place.

* **AI/LLM Friendly JSON**
  Compact export with real electrical connectivity (pin → net), BOM, and variant data.

* **Annotation Tools**
  Add notes and highlights directly on schematics (PDF-like editing experience).

* **Touch / Mobile Ready**
  Works on phones and tablets: one-finger pan, two-finger pinch zoom, tap to select
  (schematic, PCB and 3D views alike), responsive sidebars.

* **Measure, Net Browser & PNG Export (PCB viewer)**
  Two-click distance in mm/mil that snaps to pad centers, searchable net list with
  power/ground/signal filters, one-click PNG of the current view, built-in help (`?`).

* **BOM · Assembly Panel (PCB viewer)**
  Components grouped by value + footprint; click a row to highlight the whole group
  on the board, tick it off while assembling (progress is saved in the browser),
  filter by Top/Bottom/Remaining, pin-1 marker on the selected part.

* **Cross-platform**
  Works on Windows and Linux. Fully OS-independent via `pathlib`.

---

## Screenshots

**Interactive schematic viewer**

![Schematic viewer](img/sch.jpg)

**PCB viewer**

![PCB viewer](img/pcb.jpg)

**3D board preview**

![3D board](img/3d.jpg)

---

## 📦 Outputs

The application generates eight types of outputs:

| Output                     | Format           | Description                       |
| -------------------------- | ---------------- | --------------------------------- |
| **Schematic Viewer**       | HTML (~30 MB)    | Single-file interactive schematic |
| **PCB Viewer**             | HTML (~3-8 MB)   | Canvas viewer from raw geometry, net highlighting |
| **Schematic + PCB + 3D ★** | HTML (~8-15 MB)  | Combined view with cross-probing  |
| **MCU Pin List**           | XLSX             | MCU-centric pin mapping           |
| **IC Connection Map**      | XLSX             | Signal/interface mapping          |
| **BOM**                    | CSV              | Full bill of materials            |
| **Pick & Place**           | CSV              | PCB placement coordinates         |
| **JSON**                   | JSON             | AI/LLM-friendly structured data   |

---

## ⚙️ Installation

### Requirements

* **Python 3.12**
* On Linux: `glibc ≥ 2.39` required due to dependency constraints

### Install dependencies

```bash
# Windows
py -3.12 -m pip install -r requirements.txt

# Linux
python3 -m pip install -r requirements.txt
```

---

## ▶️ Usage

```bash
# Windows
py -3.12 gui.py

# Linux
python3 gui.py
```

1. Select your Altium project (`.PrjPcb`)
2. Pick the language from **Settings → Language** (Türkçe / English) — this also decides
   the language of the HTML viewers you are about to generate
3. Click the desired output button (or use the **Generate** menu)
4. Generated files appear in the project directory

> Tip: If updates are not visible, refresh with **Ctrl+F5**

### Desktop shortcuts

| Key        | Action                       |
| ---------- | ---------------------------- |
| `Ctrl+O`   | Open project                 |
| `Ctrl+S`   | Choose output path           |
| `Ctrl+1-3` | Generate Schematic / PCB / Combined |
| `Ctrl+B`   | Open last output in browser  |
| `F11`      | Full screen on / off         |
| `F1`       | About / versions             |
| `Ctrl+Q`   | Quit                         |

---

## ⌨️ Shortcuts (HTML Viewer)

| Key              | Function                        |
| ---------------- | ------------------------------- |
| `/`              | Open search                     |
| `Enter`          | Select first result             |
| `B`              | Toggle sidebar                  |
| `H`              | Schematic hierarchy tab         |
| `Alt+Backspace`  | Leave sheet (go to parent)      |
| `Alt+Home`       | Go to root sheet                |
| `Alt+←` / `Alt+→`| Sheet history back / forward    |
| `0`              | Reset view                      |
| `F`              | Fit view                        |
| `Esc`            | Clear selection                 |
| `?`              | Show help                       |
| `1-4`            | Switch views                    |

In the combined view the top bar also has a full-screen button (same effect as the
browser's `F11`).

Touch: one finger = pan (rotate in 3D), two fingers = pinch zoom, tap = click,
double tap = double click.

---

## 🛠 Windows EXE Build

```bash
py -3.12 -m PyInstaller --noconfirm --onefile --windowed --name "SchematicViz" ^
    --collect-all altium_monkey --collect-all PyQt5 ^
    --collect-all openpyxl --collect-all cascadio --collect-all trimesh ^
    --collect-all numpy ^
    --icon icon.ico --add-data "gui.ui;." --add-data "icon.ico;." gui.py
```

---

## 🧠 Architecture Notes

* **Single-file HTML strategy** → fully portable, no backend needed
* **Real netlist generation** via `compile_netlist()`
* **Cross-platform path resolution**
* Robust file discovery for mixed OS workflows

---

## 🙏 Acknowledgements

Built on top of [`altium_monkey`](https://github.com/wavenumber-eng/altium_monkey)
by Eli Hughes / Wavenumber.

---

## 📄 License

Licensed under **AGPL-3.0-or-later**

Due to dependencies:

* `altium_monkey` (AGPL-3.0)
* PyQt5 (GPL v3)

The combined work must be distributed under AGPL.

> Generated outputs (HTML, CSV, JSON, Excel) are **NOT affected** by AGPL and can be freely shared.

---

## ⭐ If you like this project

Give it a star ⭐ on GitHub and consider supporting:

<a href="https://buymeacoffee.com/cansizmikab" target="_blank">
  <img src="https://cdn.buymeacoffee.com/buttons/v2/default-yellow.png" alt="Buy Me A Coffee" height="45" width="163">
</a>


-----------------------

# Schematic Viz Generator (TR)

> Altium şematik ve PCB projelerini tek dosyalık, sunucu gerektirmeyen **interaktif HTML görüntüleyicilere** dönüştüren PyQt5 masaüstü uygulaması.

![Version](https://img.shields.io/badge/version-2.25.0-blue.svg)
![Python](https://img.shields.io/badge/python-3.10%2B-3776AB.svg?logo=python&logoColor=white)
![GUI](https://img.shields.io/badge/GUI-PyQt5-41CD52.svg?logo=qt&logoColor=white)
![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Linux-lightgrey.svg)
![License](https://img.shields.io/badge/license-AGPL--3.0--or--later-orange.svg)
[![Buy Me A Coffee](https://img.shields.io/badge/Buy%20Me%20A%20Coffee-destek-FFDD00.svg?logo=buymeacoffee&logoColor=black)](https://buymeacoffee.com/cansizmikab)


## ❤️ Destek

Bu proje işinize yaradıysa bir kahve ısmarlayabilirsiniz ☕
Boş zamanımda geliştiriyorum; desteğiniz projenin bakımını ve yeni özellikleri
sürdürmemi sağlıyor.

<a href="https://buymeacoffee.com/cansizmikab" target="_blank">
  <img src="https://cdn.buymeacoffee.com/buttons/v2/default-yellow.png" alt="Buy Me A Coffee" height="45" width="163">
</a>

👉 [buymeacoffee.com/cansizmikab](https://buymeacoffee.com/cansizmikab)



## Proje

Projeyi seçin, bir düğmeye basın — çıktı olarak **çift tıkla açılan, tek dosya, portable** bir HTML
(veya Excel/CSV/JSON) alın. Ne web sunucusu, ne kurulum, ne internet gerekir; `file://` ile açılır.

![Schematic Viz Generator ana arayüzü](img/app.jpg)

---

##  Öne Çıkanlar

- **Türkçe / İngilizce arayüz** — **Ayarlar → Dil** menüsünden anında geçiş, seçim hatırlanır. Dil her yerde geçerlidir: masaüstü arayüzü, üretim log'u ve ilerleme etiketleri, **ve üretilen HTML görüntüleyiciler**. HTML dosyası üretildiği dili taşır; aynı projeden hem Türkçe hem İngilizce görüntüleyici üretip farklı kişilere verebilirsiniz.
- **Üst menü ve klavye kısayolları** — Dosya / Üret / Görünüm / Ayarlar / Yardım. Her üretim menüden de erişilebilir (`Ctrl+1..3` görüntüleyiciler), ayrıca `Ctrl+O` proje aç, `Ctrl+B` son çıktıyı aç, `F11` tam ekran, `F1` hakkında.
- **İnteraktif Şematik Viewer** — Tüm sayfalar tek pan/zoom kanvasında, tıklanabilir net'ler ve komponentler, PDF gibi seçilip kopyalanabilir metinler.
- **Şematik Hiyerarşi paneli (KiCad tarzı)** — Sol panelde sayfa ağacı: kök şema → sheet symbol'ler → alt sayfalar, sayfa numaralarıyla ve açılır/kapanır dallarla. Tekrar (Repeat) kanalları ayrı örnek olarak görünür; `Alt+Backspace` ("üst sayfaya dön") her zaman doğru üst sayfaya döner. Ayrıca `Alt+Home` kök sayfa, `Alt+←/→` sayfa geçmişi.
- **PCB Görüntüleyici (geometri / canvas)** — Altium benzeri tam ekran katman görüntüleyici; katman aç/kapa, bakır yol/net highlight, komponente tıkla → şematik ↔ PCB cross-probe. Katman SVG'leri yerine board'un ham geometrisi gömülüp canvas'a çizilir: dosya çok daha küçük, her zoom'da akıcı; döndürme/ayna ve dokunmatik dahil.
- **Şematik + PCB + 3D tek HTML'de** — Yan yana, çift yönlü cross-probe; gerçek gömülü **STEP 3D modelleriyle** board önizlemesi.
- **Excel &amp; CSV çıktıları** — MCU pin listesi, IC bağlantı haritası, BOM, Pick &amp; Place.
- **AI/LLM dostu JSON** — Gerçek elektriksel bağlantı (pin → net), BOM ve varyant verisiyle kompakt dışa aktarma.
- **Not &amp; kutu araçları** — Şematik üzerine PDF editörü tarzı not/işaret ekleme, kaydetme.
- **Dokunmatik / mobil** — Telefon ve tablette çalışır: tek parmak kaydırma, iki parmak yakınlaştırma, dokunarak seçme (şematik, PCB ve 3D); dar ekranda kayan sol panel.
- **Ölçüm · Net listesi · PNG (PCB)** — İki tıkla mesafe (mm + mil, pad merkezine yapışır), aranabilir net listesi (Güç/GND/Sinyal filtresi, tıkla → vurgula), tek tıkla görünümün PNG'si, `?` ile yardım.
- **BOM · Montaj paneli (PCB)** — Değer + footprint'e göre gruplanmış liste; satıra dokun → grubun tamamı board'da vurgulanır, ✓ ile montaj takibi (tarayıcıda saklanır), Üst/Alt/Kalan filtreleri, seçili parçada pin-1 işareti.
- **Cross-platform** — Windows ve Linux; kodun tamamı `pathlib` ile OS-bağımsız.

---

## Ekran Görüntüleri

**İnteraktif şematik viewer** — tıklanabilir net'ler, bağlantı yayları, sol panelde net/komponent listesi:

![Şematik viewer](img/sch.jpg)

**PCB görüntüleyici** — Altium benzeri katmanlı görünüm, bakır/net highlight, çift yönlü cross-probe:

![PCB görüntüleyici](img/pcb.jpg)

**3D board** — gerçek gömülü STEP modelleriyle interaktif board önizlemesi:

![3D board görünümü](img/3d.jpg)

---

##  Üretilen Çıktılar

Uygulama sekiz ayrı çıktı üretir:


| Çıktı                    | Format           | Açıklama                                                     |
| ------------------------ | ---------------- | ------------------------------------------------------------ |
| **Şematik Viewer**       | HTML (~30 MB)    | Gömülü SVG'lerle tek dosya interaktif şematik                |
| **PCB Görüntüleyici**    | HTML (~3-8 MB)   | Ham geometriden canvas PCB, net highlight, cross-probe       |
| **Şematik + PCB + 3D ★** | HTML (~8-15 MB)  | Üçü tek dosyada, çift yönlü cross-probe + 3D                 |
| **MCU Pin Listesi**      | XLSX             | MCU merkezli pin listesi (fonksiyon/arayüz otomatik tespiti) |
| **IC Bağlantı Haritası** | XLSX             | IC gruplarına göre sinyal/arayüz tablosu                     |
| **BOM**                  | CSV              | Tüm parametre sütunlarıyla malzeme listesi                   |
| **Pick &amp; Place**     | CSV              | PCB yerleşim koordinatları (PCB gerekir)                     |
| **JSON**                 | JSON             | AI/LLM analizine uygun kompakt veri (pin→net, BOM, varyant)  |


---

##  Kurulum

### Gereksinimler

- **Python 3.12** 
- Linux'ta `altium-monkey` bağımlılığı `wn-geometer` yalnızca `manylinux_2_39` wheel'i dağıttığından **glibc ≥ 2.39** gerekir (Ubuntu 24.04+ / Debian 13+). Eski dağıtımlarda `pip` `ResolutionImpossible` hatası verir.

### Bağımlılıklar

```bash
# Windows
py -3.12 -m pip install -r requirements.txt

# Linux
python3 -m pip install -r requirements.txt
```

`requirements.txt` tüm listeyi içerir: PyQt5, altium-monkey, openpyxl ve 3D görünüm için
zorunlu `cascadio` / `trimesh` / `numpy`.

> **Not:** Gerekli minimum `altium-monkey` sürümü **2026.8.11**'dir. Uygulama açılışta
> tüm bağımlılıkları denetler (`deps.py`); eksik/eski paket varsa hangi paketin sorunlu
> olduğunu ve kurulum komutunu söyleyen bir mesajla durur. Listeyi görmek için:
> `py -3.12 deps.py`

---

##  Kullanım

```bash
# Windows
py -3.12 gui.py

# Linux
python3 gui.py
```

1. Açılan pencereden Altium proje dosyanızı (`.PrjPcb`) seçin.
2. **Ayarlar → Dil** menüsünden dili seçin (Türkçe / English) — bu seçim üretilecek
   HTML görüntüleyicilerin dilini de belirler.
3. İstediğiniz çıktı düğmesine (ya da **Üret** menüsündeki karşılığına) basın.
4. Üretim bittiğinde çıktı proje klasörüne yazılır; HTML'ler tarayıcıda çift tıkla açılır.

### Masaüstü Kısayolları

| Tuş        | İşlev                                          |
| ---------- | ---------------------------------------------- |
| `Ctrl+O`   | Proje aç                                       |
| `Ctrl+S`   | Çıktı yolunu seç                               |
| `Ctrl+1-3` | Şematik / PCB / Birleşik üret                  |
| `Ctrl+B`   | Son çıktıyı tarayıcıda aç                      |
| `F11`      | Tam ekran aç / kapat                           |
| `F1`       | Hakkında / sürümler                            |
| `Ctrl+Q`   | Çıkış                                          |

> **İpucu:** HTML'i açtıktan sonra değişikliği görmüyorsanız **Ctrl+F5** ile cache'i temizleyerek yeniden açın.

### Klavye Kısayolları (HTML Viewer)


| Tuş               | İşlev                                       |
| ----------------- | ------------------------------------------- |
| `/`               | Aramayı aç + odaklan                        |
| `Enter`           | Aramada ilk sonucu seç                      |
| `B`               | Sol paneli gizle/göster                     |
| `H`               | Şematik hiyerarşi sekmesi                   |
| `Alt+Backspace`   | Üst sayfaya dön (hiyerarşide bir üst)       |
| `Alt+Home`        | Ana (kök) sayfaya git                       |
| `Alt+←` / `Alt+→` | Sayfa geçmişinde geri / ileri               |
| `0`               | Görünümü sıfırla                            |
| `F`               | Son öğeye sığdır                            |
| `Esc`             | Seçimi/aracı temizle                        |
| `?`               | Kısayol yardımını aç                        |
| `1 / 2 / 3 / 4`   | Birleşik görünümde Şematik / Böl / PCB / 3D |

Birleşik görünümün üst çubuğunda ayrıca **tam ekran düğmesi** vardır (tarayıcının
`F11`'i ile aynı işi yapar).

**Dokunmatik:** tek parmak sürükle = kaydır (3D'de döndür) · iki parmak = yakınlaştır
(pinch) + kaydır · tek dokunuş = tıklama · çift dokunuş = çift tıklama.


---

##  Windows EXE Paketleme

```bash
py -3.12 -m PyInstaller --noconfirm --onefile --windowed --name "SchematicViz" ^
    --collect-all altium_monkey --collect-all PyQt5 ^
    --collect-all openpyxl --collect-all cascadio --collect-all trimesh ^
    --collect-all numpy ^
    --icon icon.ico --add-data "gui.ui;." --add-data "icon.ico;." gui.py
```

Kolaylık için `build_exe.bat` çift tıklanarak da çalıştırılabilir (proje dizinine geçer,
PyInstaller yoksa kurar, tüm bağımlılıkları toplar).

> Fresh bir Windows'ta exe açılmazsa **MS VC++ Redistributable** gerekir:
> [https://aka.ms/vs/17/release/vc_redist.x64.exe](https://aka.ms/vs/17/release/vc_redist.x64.exe)

Linux için `build_linux.sh` betiği mevcuttur.

---

##  Proje Yapısı

```
├── viewer.py       # Tüm üretim mantığı (HTML/JSON/CSV/XLSX üreticileri, APP_VERSION burada)
├── gui.py          # PyQt5 ana pencere, üst menü, non-blocking üretim thread'i
├── gui.ui          # Qt Designer XML formu (menü çubuğu gui.py'de kodla kurulur)
├── i18n.py         # Türkçe → İngilizce çeviri kataloğu (arayüz + log + HTML)
├── deps.py         # Bağımlılık kataloğu ve başlangıç denetimi
├── tools/
│   └── check_html_i18n.py   # HTML çevirisi kapsama denetimi
├── requirements.txt
├── build_exe.bat   # Windows exe paketleme
├── build_linux.sh  # Linux paketleme
├── Doxyfile        # Doxygen dokümantasyon ayarı
└── CLAUDE.md       # Ayrıntılı mimari ve geliştirici notları
```

Geliştirici dokümantasyonu için `CLAUDE.md`; kaynak-kod dokümantasyonu için `doxygen Doxyfile`
(çıktı: `docs/html/index.html`).

---

##  Mimari Kısa Notlar

- **Tek-dosya HTML stratejisi**: SVG'ler gömülü, sunucu gerekmez, `file://` ile açılır — dosya büyük ama tamamen portable.
- **Gerçek netlist**: JSON/Excel çıktıları `compile_netlist()` ile derlenen gerçek pin→net bağlantısı içerir; PcbDoc varsa netler PCB'den yeniden kurularak fiziksel doğruluk sağlanır.
- **PyQt5** (PyQt6 değil): `app.exec_()` ve flat enum kullanımına dikkat.
- **SchDoc/PcbDoc bulma**: Üç kademeli, OS-bağımsız fallback — Windows'ta kaydedilip Linux'ta açılan projeler de sorunsuz çözülür.

---

##  Teşekkür

Bu proje [`altium_monkey`](https://github.com/wavenumber-eng/altium_monkey)
(Eli Hughes / [Wavenumber](https://github.com/wavenumber-eng)) kütüphanesi üzerine kuruludur.
Altium dosya formatlarının okunması bu kütüphane sayesinde mümkündür. Kendisine Teşkkürlerimi sunuyorum.

---

## 📄 Lisans

Bu proje **GNU Affero General Public License v3.0 veya üzeri (AGPL-3.0-or-later)** ile
lisanslanmıştır — tam metin için [`LICENSE`](LICENSE) dosyasına bakın.

Bu lisans bir tercih değil, zorunluluktur: çekirdek bağımlılık
[`altium_monkey`](https://github.com/wavenumber-eng/altium_monkey) **AGPL-3.0** ve GUI
kütüphanesi **PyQt5 GPL v3** olduğundan, birleşik eser AGPL-3.0 altında dağıtılmak
zorundadır. Diğer bağımlılıklar (wn-geometer, openpyxl, cascadio, trimesh, numpy — MIT/BSD)
izin vericidir ve sorun oluşturmaz.

**Uygulama kaynağını dağıtmak** (exe veya kod olarak) ya da **ağ üzerinden hizmet olarak
sunmak**, kaynak kodun AGPL-3.0 altında sunulmasını gerektirir.

> **Not:** Bu araçla **üretilen HTML/Excel/CSV/JSON çıktıları** programın *çıktısıdır* ve
> AGPL kapsamında türev eser sayılmaz — ürettiğiniz görüntüleyicileri serbestçe
> paylaşabilirsiniz. Bulaşıcılık yalnızca uygulamanın *kendi kaynağını* bağlar.

