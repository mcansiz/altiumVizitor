# Schematic Viz Generator

Altium şematik projelerini interaktif HTML viewer'a dönüştüren PyQt5 uygulaması.
Wavenumber'ın ticari "viz sch 1.0" ürününün açık-kaynak alternatifi.
[altium_monkey](https://github.com/wavenumber-eng/altium_monkey) kütüphanesi
(Eli Hughes / Wavenumber) üzerine kurulu.

**Mevcut sürüm**: `APP_VERSION` sabiti **`viewer.py`'de** tutulur (şu an 2.27.0);
`gui.py` oradan import eder (v2.9.29'da taşındı — HTML çıktıları da sürümü
gösterebilsin diye, tek kaynak). Yeni özellik/düzeltme ekleyince bu sabiti
güncelle (semver: major.minor.patch). Sürüm pencere başlığında, alt durum
çubuğunda, üretim log'unun başında, "Hakkında" diyaloğunda ve birleşik HTML'in
sağ üst rozetinde (`{proje} · v{APP_VERSION}`) görünür.

## Beş Dosya

- **`viewer.py`** — Tüm üretim mantığı. Ortak `_collect_data()` helper'ı sayfaları,
  netleri, komponentleri, sheet symbol'leri (block'ları), netlist'i (pin→net)
  ve BOM/PnP/varyant verilerini toplar. Altı public üretim fonksiyonu:
  - `generate_viewer(...)` → tek dosya interaktif HTML (sayfalar kanvasa
    çizilir — v2.27.0'da SVG DOM'u bırakıldı; BRK-210: 3.80 → 1.72 MB)
  - `generate_json(...)` → AI/LLM analizine uygun kompakt JSON (pin→net, BOM,
    varyant dahil)
  - `generate_bom_csv(...)` → malzeme listesi CSV (tüm parametre sütunlarıyla)
  - `generate_pnp_csv(...)` → Pick&Place yerleşim CSV (PCB gerekir)
  - `generate_ic_map_xlsx(..., min_pins=4, main_designators=None,
    exclude_prefixes=None)` → IC Bağlantı Haritası Excel (v2.9.30+: mcu.xlsx
    örneği düzeni — TEK tablo, IC grupları dikey birleşik hücrelerde):
    No | Kontrol Entegresi (değer+açıklama) | Desig | Sinyal Adı (Net) |
    Kontrol Arayüzü (SATIR bazında: I2C/SPI/USART/SWD/USB veya port ok
    yönünden GPIO_IN/GPIO_OUT) | I2C Adres ('-', elle doldurulur) |
    Entegre Portu | Pin Say. (komponentin toplam pin sayısı) | MCU Portu |
    Fonksiyonel Blok. Yalnız SİNYAL pinleri listelenir (güç/toprak netleri VE
    VDD/VBAT görevli pinler atlanır). **Ana işlemci grubu tablonun BAŞINDA**;
    bağlı olmayan pinleri de "NC" satırı olarak eklenir (şematik pin
    kataloğundan). 'MCU Portu' seri pasifler üzerinden izlenir (örn.
    `PC4 (R12 üzerinden)`). `exclude_prefixes` ("J,P,TP") designator HARF
    önekiyle komponent hariç tutar (GUI'de "Hariç tut" alanı; ana işlemci
    asla hariç tutulmaz). `main_designators` None ise en çok pinli U*
    otomatik; "U2" tek; ["U2","U7"] veya "U2,U7" çoklu işlemci.
  - `generate_mcu_pinout_xlsx(..., mcu_designator)` → MCU merkezli pin listesi:
    her MCU pini bir satır — pin no, pin adı, fonksiyon/arayüz (otomatik:
    I2C/SPI/USB/DRAM/GPIO vs), net, hedef IC portu. Hedefte seri pasifler
    ATLANIR (v2.9.30+): direnç yerine `IC6.9 (P0_0) [R12 üzerinden]`;
    pasif→güç bağlantıları `R5→+3V3 (pull-up)` / `C14→GND (filtre C)` diye
    raporlanır. Üstte fonksiyon dağılımı özeti. `mcu_designator` ZORUNLU.
  - `generate_pcb_canvas_viewer(...)` → **geometri tabanlı** PCB görüntüleyici —
    projedeki TEK PCB üreticisi (v2.12.0'da eklendi, v2.22.0'da katman-SVG'li
    klasik yol kaldırıldı). `extract_pcb_geometry()` ile ham primitive'ler
    (iz/yay/pad/via/region/metin) çıkarılıp gzip'lenerek gömülür, tarayıcıda
    `<canvas>`'a çizilir → **BRK-210: 8 MB yerine 3.3 MB, üretim 135 s yerine
    48 s**; her zoom seviyesinde akıcı (LOD gerekmez). Katman aç/kapa, komponent
    seç (popup + cross-probe), ize çift tık = net vurgusu, ölçüm (pad merkezine
    yapışma), döndür/çevir, pad etiketleri, PNG, BOM · Montaj paneli, dokunmatik.
    GUI'de **"PCB Görüntüleyici"** butonu (`mode='pcbgeo'`).
    **Bilinen kısıt**: solder mask / paste katmanları listelenmez — Altium onları
    pad'lerden türetiyor, dosyada primitive olarak yok.
  - `read_annotations(path)` / `write_annotations(path, items)` → şematik
    notlarını DOSYA düzeyinde oku/yaz (üretim yapmaz). Kaynak: `_notlar.json`,
    notları gömülü şematik HTML'i veya birleşik görünüm (iç şematik HTML'i
    gzip'ten çözülüp yazılır, yeniden sıkıştırılır). GUI'nin "Notları Eski
    Çıktıdan Taşı…" eylemi bu ikisini kullanır; `ts` şimdiye ayarlanır ki
    taşınan notlar bayat localStorage kaydına yenilsin.
  - `generate_combined_viewer(...)` → şematik + PCB tek HTML'de yan yana,
    çift yönlü cross-probe. İki viewer iframe içinde izole (her iframe'in HTML'i
    kabuğa JSON string olarak gömülür, runtime'da `iframe.srcdoc` ile yüklenir),
    `postMessage` ile haberleşir: birinde komponente tıkla → diğeri o komponenti
    gösterir. Ortada sürüklenebilir ayraç. Topbar'da görünüm modu düğmeleri
    **Şematik / Böl / PCB / 3D** (klavye: 1/2/3/4, odak kabuktayken) ve
    **tam ekran düğmesi** (`#vm-fs`, v2.24.0 — tarayıcının F11'iyle aynı).
    **Gizli panele gelen seçim BEKLETİLİR** (v2.24.0): `display:none` iframe'de
    her ölçüm 0 döndüğünden vurgu/odak çöp çıkıyordu; kabuk `setViewMode()`
    içinde görünür panele `pane-shown` yollar, iç viewer `pendingXpComp`'ı o an
    uygular (bkz. Çözülen Sorunlar).
    **Açılış modu SADECE Şematik** (v2.9.22+): PCB ve 3D iframe'leri tembel
    yüklenir — ilk o moda geçişte gzip'ten çözülür, o sırada "PCB/3D
    hazırlanıyor…" spinner'ı görünür (`.pane-loading`). Şematikte komponent
    seçilse bile PCB arka planda YÜKLENMEZ (`curMode` kontrolü); son seçim
    `lastSel`'de saklanır, moda geçince `repostSel` ile iletilir → açılışta
    ekstra yük yok, cross-probe kaybolmaz. Pane etiketleri (ŞEMATİK/PCB
    yazıları) v2.9.27'de tamamen kaldırıldı. Komponent seçilince mod
    DEĞİŞMEZ (cross-probe arka planda çalışır). PCB paneli her zaman geometri/
    canvas görüntüleyicidir (`to_layer_svgs()` HİÇ çağrılmaz — üretimin en pahalı
    adımı buydu: **BRK-210'da 402 s / 13.28 MB yerine 69 s / 7.27 MB**); 3D board
    yüzey dokusu (bakır izler + pad'ler + silkscreen çizim ve YAZILARI) aynı
    geometriden `_build_surface_from_geometry()` ile çizilir.
    `build_combined_shell()` kabuk sayfayı, köprü için her iki builder'a eklenen
    `crossProbeOut()` + message listener'ı kullanır.
    **Net cross-probe** (v2.18.0): komponentin yanında NET seçimi de paylaşılır —
    şematikte bir net adına (veya Nets listesinden bir net'e) tıklayınca PCB'de
    o net'in bakırı tüm katmanlarda vurgulanır, tersi de çalışır (PCB'de ize çift
    tık / Netler panelinden seçim → şematikte net yayları çizilir). Mesaj tipi
    `xprobe-net` (`{{source, net}}`, `net:null` = "bırak"); 3D'ye iletilmez (net
    verisi yok). Ad birebir tutmazsa büyük/küçük harf duyarsız eşleştirilir.
    Ping-pong'u `xpApplying` bayrağı keser: gelen mesaj uygulanırken hiçbir
    panel geri yayın yapmaz. Çoklu seçimde (Shift) EN SON seçilen net iletilir.
    **İKİ KRİTİK GÖMME KURALI** (bkz. Çözülen Sorunlar): (1) iç HTML JSON'unda
    `</` → `<\/` yapılır, yoksa iç viewer'ların `</script>`'i kabuğun satır-içi
    script'ini erken kapatır → paneller boş. (2) `srcdoc` kullanılır, Blob URL
    DEĞİL — `file://` altında origin "null" olur, `blob:null/...` engellenir.
- **`gui.py`** — PyQt5 ana pencere. `GeneratorThread` ile non-blocking üretim,
  `mode='html'|'json'|'bom'|'pnp'|'icmap'|'mcupin'|'pcbgeo'|'combined'` ile
  yedi ayrı buton. `GeneratorThread.progress_signal(int percent, str label)`
  üretim ilerlemesini taşır → `logGroup`'taki `progressBar`'a yansır. `percent < 0`
  = belirsiz/marquee (süresi kestirilemeyen adım). Üretici fonksiyonlar
  `progress=` callback'i alır (combined/pcbgeo/html).
- **`gui.ui`** — Qt Designer XML form. `uic.loadUi('gui.ui')` ile yüklenir.
  **Menü çubuğu burada DEĞİL** — `gui.py`'deki `_build_menu()` içinde kodla
  kurulur (bkz. "Üst menü + dil desteği").
- **`deps.py`** — Bağımlılık kataloğu + başlangıç denetimi (bkz. aşağıdaki bölüm).
- **`i18n.py`** — Arayüz dil desteği (TR kaynak → EN çeviri kataloğu, bkz. aşağı).

## Üst menü + dil desteği (TR/EN) — v2.20.0+

**Menü çubuğu** `gui.py` → `_build_menu()` içinde KODLA kurulur (gui.ui'de yok):
**Dosya** (Proje Aç `Ctrl+O`, Çıktı Yolu Seç `Ctrl+S`, Son Çıktıyı Tarayıcıda Aç
`Ctrl+B`, Çıktı Klasörünü Aç, **Notları Eski Çıktıdan Taşı…**, Log'u
Temizle, Çıkış `Ctrl+Q`) · **Üret** (üç
görüntüleyici `Ctrl+1..3` + beş veri çıktısı — hepsi mevcut buton slotlarını
yeniden kullanır) · **Görünüm** (Tam Ekran `F11`, işaretlenebilir) ·
**Ayarlar** (Dil alt menüsü, iki renk seçici) · **Yardım** (Hakkında `F1`,
Sürümleri Kopyala, Bağımlılık Durumu). Menü kodla kuruluyor çünkü
işaretlenebilir/dışlamalı dil eylemleri ve üretim sırasında toplu kilitleme
(`_menu_action_items`) Designer XML'inde ifade edilemez. Üretim başlayınca
butonlarla BİRLİKTE menü eylemleri de devre dışı kalır; "tarayıcıda aç"
buton+eylem ikilisi tek noktadan (`_set_open_enabled`) yönetilir.

**Tam Ekran (v2.23.0)**: `toggle_fullscreen()` + `changeEvent()`. İki ayrıntı:
(1) `showNormal()` maximize'i de kaldırdığından tam ekrana geçmeden önceki
durum `_was_maximized`'e alınır, çıkışta gerekiyorsa `showMaximized()`
kullanılır; (2) pencere durumu menü dışından da değişebilir (pencere yöneticisi)
→ `changeEvent`'te `WindowStateChange` yakalanıp eylem işareti `isFullScreen()`
ile eşitlenir (tek doğruluk kaynağı pencerenin kendisi). Görünüm eylemi
`_menu_action_items`'a GİRMEZ: üretim sürerken de tam ekrana geçilebilir.

**Dil** (`i18n.py`): kaynak dil **Türkçe**dir — kodda ve gui.ui'de metinler
Türkçe yazılır, katalog bu Türkçe dizgeyi ANAHTAR olarak kullanır
(`_EN = {"Altium Projesi": "Altium Project", …}`). `tr(metin)` karşılığı yoksa
metni AYNEN döndürür → çeviri eksikse arayüz bozulmaz, o satır Türkçe kalır.
Qt Linguist (.ts/.qm) yerine sözlük seçildi: derleme adımı (pylupdate5/lrelease)
yok, PyInstaller'a ek veri dosyası girmiyor (`import i18n` statik analizle
paketlenir), dil anında değişiyor. Seçim `QSettings("language")` ile kalıcı;
kayıt yoksa **Türkçe** (mevcut davranış korunur).

**İKİ KRİTİK KURAL** (ölçümle bulundu, bkz. Çözülen Sorunlar):
1. Widget metinleri açılışta HENÜZ TÜRKÇEYKEN yedeklenir
   (`i18n.snapshot_widgets` → `_ui_snapshot`), dil değişince
   `apply_snapshot` her metni KAYNAKTAN yeniden çevirir. Yerinde çeviri
   yapılsaydı İngilizceye geçince metin katalog anahtarı olmaktan çıkar,
   Türkçeye DÖNÜŞ imkânsız olurdu.
2. Yedek yalnız ETİKET taşıyan özellikleri alır: `QLineEdit`'ten yalnız
   `placeholderText` (metni KULLANICI VERİSİ), `QGroupBox`'tan `title`,
   butonlardan `text`. Metni veri olan widget'lar ada göre dışlanır —
   renk butonları (`interColorBtn`/`intraColorBtn`) seçili hex kodunu
   gösterir, yedeğe girseydi dil değişimi kullanıcının seçtiği rengi ezerdi.

**Kapsam**: PyQt arayüzü (menü, butonlar, diyaloglar) · `viewer.py`'nin üretim
log'u + ilerleme çubuğu etiketleri (v2.20.1) · **üretilen HTML görüntüleyicilerin
arayüzü** (v2.21.0). Üçü de tek dil ayarını izler; HTML'in dili ÜRETİM ANINDAKİ
seçime göre sabitlenir (tek dosya çıktı, sonradan değişmez).
`viewer.py`'deki 151 `log()`/`prog()` çağrısı AST güdümlü bir betikle `tr()`
içine alındı: `log(f"… {x} …")` → `log(tr("… {a0} …").format(a0=x)`.
`i18n._EN_LOG` (~145 şablon) bu metinleri taşır; anahtarlar `{a0}`, `{a1:.1f}`
gibi yer tutucuları ve biçim belirteçlerini AYNEN korur.
**Hâlâ Türkçe kalan**: `deps.py`'nin başlangıç hata mesajları (dil tercihi
okunmadan, uygulama açılmadan önce çalışır).

### HTML görüntüleyici arayüzü: ⟪…⟫ işaret yöntemi (v2.21.0+)

Şablonlardaki her arayüz metni kaynakta **⟪metin⟫** ile sarılıdır; her
`build_*_html()` çıktısını `_tr_html()`'den geçirir — o da `⟪(...)⟫`'yi
`tr(...)` ile değiştirip işaretleri kaldırır (`i18n._EN_HTML`, 205 anahtar —
v2.22.0'da klasik PCB şablonuyla birlikte 69 anahtar düştü).
- **Neden işaret, neden `{tr(...)}` değil**: şablonların bir kısmı f-string
  (`build_html`, `build_combined_shell`), bir kısmı ham
  `.replace()` şablonu (`_PCB_CANVAS_TPL`, 3D `tpl`). Tek işaret sözdizimi
  ikisinde de çalışır ve f-string'lerdeki `{{`/`}}` kaçış kurallarına dokunmaz.
- **Neden çıktı üzerinde değil kaynakta işaretleniyor**: üretilmiş HTML'de
  düz metin araması yapılsaydı çalışma-anı verisi (net adı, designator,
  komponent değeri, kullanıcı notu) yanlışlıkla çevrilebilirdi. İşaretler
  şablonda durduğu için veriyle çakışma imkânsız (veri asla ⟪⟫ içermez).
- **İşaret ASLA placeholder kapsamamalı**: f-string'de `{...}`, ham şablonda
  `__AD__`. Çeviri üretimin SONUNDA çalışır; placeholder o an gerçek veriyle
  dolmuştur ve anahtar tutmaz. Doğrusu: `⟪Şematik + PCB⟫ · {project_name}`.
- **Çeviri metni `' " < >` İÇEREMEZ**: bu metinler tek/çift tırnaklı JS
  dizgelerine ve HTML attribute'larına gömülür; tırnak şablonu bozar.
- **Denetim**: `py -3.12 tools/check_html_i18n.py` — her işaretin karşılığı
  var mı, çeviride yasak karakter var mı, katalogda ölü anahtar kalmış mı
  (çıkış kodu 1 = sorun). Yeni arayüz metni eklerken bunu çalıştır.
- **JS'te kaçışlı metin**: kaynakta `board\\'da` yazan bir dizge üretilen
  HTML'de `board\'da` olur → katalog anahtarı ÇALIŞMA-ANI biçimidir (ters
  bölüyü içerir). Denetim betiği iki biçimi de dener.

**Yeni metin eklerken**: Türkçe yaz, `tr()` ile sar, karşılığını `i18n._EN`
(arayüz) veya `i18n._EN_LOG` (üretim log'u) sözlüğüne ekle. Placeholder'lı
metinlerde `tr("… {ad} …").format(ad=x)` kullan (f-string DEĞİL — anahtar sabit
kalmalı ve çeviri sırayı değiştirebilmeli). `i18n.missing_keys([...])` çevirisi
eksik metinleri listeler. Yüzde-biçimli (`"%.2f" % x`) log satırlarında önce
`{a0}` şablonuna geç, sayıyı `f"{x:.2f}"` ile önceden biçimle.

## SchDoc Bulma Fallback'i — Cross-platform (ÖNEMLİ)

`_resolve_schdoc_paths()` üç kademeli, OS-bağımsız çalışır:
1. `project.get_reachable_schdoc_paths()` — projenin kendi çözümü
2. Boşsa: PrjPcb metnini oku, `DocumentPath=...SchDoc` satırlarındaki ters
   slash'i (`\`) ileri slash'e (`/`) çevir, dosya varsa kullan. Linux dosya
   sistemi büyük/küçük harf duyarlı olduğu için case-insensitive eşleştirme de
   yapar.
3. Son çare: PrjPcb klasöründe `rglob("*.SchDoc")` tara.

Bu olmadan Windows'ta kaydedilip Linux'ta açılan projeler (PrjPcb içindeki
`SCH\dosya.SchDoc` ters-slash referansı Linux'ta çözülemez) açılamaz. İleride
uygulama Linux için derlenirse bu fallback sayesinde bozulmaz. Kodda hardcoded
path ayracı yok — her yerde `pathlib.Path` kullanılıyor (OS'a göre çözülür).

## Bağımlılık Denetimi — eksik kütüphaneyle çalışmaz (v2.19.0+)

Kullanılan TÜM kütüphaneler `deps.py`'deki **`DEPENDENCIES`** tablosunda tek
kaynak olarak tutulur (dist adı, import adı, minimum sürüm, ne için gerektiği,
doğrudan mı/alt bağımlılık mı). `requirements.txt` bu tabloyla eşleşir
(`py -3.12 deps.py --requirements` ile karşılaştırılabilir).

- **Doğrudan**: PyQt5, altium-monkey (>= **2026.8.11**, bkz. sürüm notu),
  openpyxl, cascadio, trimesh, numpy
- **Alt bağımlılık** (olmazsa yine çöker): PyQt5-Qt5, PyQt5-sip, freetype-py,
  lxml, lz4, pillow, uharfbuzz, wn-geometer, et-xmlfile

**Kapı nerede kurulu**: `gui.py` HİÇBİR üçüncü-parti import'tan ÖNCE (PyQt5
dahil) `deps.enforce(gui=True)` çağırır → eksik varsa konsola + hata diyaloğuna
yazıp `SystemExit(1)`. `viewer.py` ise import edilir edilmez `deps.require()`
çağırır → `DependencyError`. Sıra kritiktir: `import deps` satırı PyQt5/
altium_monkey import'larının ÜSTÜNDE olmalı, yoksa kullanıcı açıklayıcı mesaj
yerine ham `ImportError` traceback'i görür. Sonuç `deps._CACHE`'te tutulur
(gui → viewer zincirinde ikinci denetim bedavadır).

- **Sürüm denetimi yalnız doğrudan bağımlılıklarda** ve yalnız minimum
  bildirilmişse yapılır; sürüm dizgesi ayrıştırılamazsa karşılaştırma ATLANIR
  (hatalı ayrıştırma geçerli bir kurulumu reddetmesin).
- **Frozen (PyInstaller) modda yalnız import edilebilirlik denetlenir**:
  paketlenmiş exe'de pip metadata'sı bulunmayabilir → sürüm/metadata denetimi
  yanlış "eksik" deyip exe'yi hiç açılmaz hale getirirdi. `sys.frozen` ile
  ayrılır; import adı olmayan paket (PyQt5-Qt5) frozen modda atlanır.
- **Konsol kodlaması**: mesajda Türkçe karakter + ✓/✗/→ var; Türkçe Windows
  konsolunda (cp1254/cp437) düz `print` UnicodeEncodeError fırlatıp ASIL hatayı
  gizler → yazma `deps._write()` üzerinden yapılır (kodlanamayan karakter '?'
  ile değiştirilir; CLI ayrıca stdout'u UTF-8'e almayı dener).
- **Kaçış kapağı**: `SCHVIZ_SKIP_DEP_CHECK=1` denetimi tamamen atlar.
- `build_exe.bat` ve `build_linux.sh` paketlemeden ÖNCE `deps.py` çalıştırır
  (çıkış kodu 1 ise paketleme durur) — PyInstaller eksik paketi yalnız uyarıyla
  geçip "başarılı" ama açılmayan exe üretiyordu.
- GUI'nin "Hakkında" diyaloğundaki sürüm listesi de `deps.status_table()`'dan
  üretilir (ikinci bir liste tutulmaz).

Listeyi görmek için: `py -3.12 deps.py` (tablo + eksik varsa çıkış kodu 1).

## Geliştirme Komutları

```bash
# Bağımlılıklar (Python 3.12) — requirements.txt tüm listeyi içerir
# (PyQt5, altium-monkey, openpyxl + 3D için zorunlu cascadio/trimesh/numpy)
# LINUX: wn-geometer (altium-monkey bağımlılığı) manylinux_2_39 wheel'i
# dağıttığından glibc >= 2.39 gerekir (Ubuntu 24.04+); eski dağıtımda
# pip ResolutionImpossible verir. Python >= 3.10 şart.
py -3.12 -m pip install -r requirements.txt

# Çalıştır
py -3.12 gui.py

# Windows exe paketle (--add-data ZORUNLU: gui.ui runtime'da yüklenir, yoksa exe açılmaz)
py -3.12 -m PyInstaller --noconfirm --onefile --windowed --name "SchematicViz" ^
    --collect-all altium_monkey --collect-all PyQt5 ^
    --collect-all openpyxl --collect-all cascadio --collect-all trimesh ^
    --collect-all numpy ^
    --add-data "gui.ui;." gui.py
```

Fresh Windows'ta exe açılmazsa **MS VC++ Redistributable** gerekir:
https://aka.ms/vs/17/release/vc_redist.x64.exe

## Dokunmatik / Mobil Destek (v2.10.0+)

Tüm HTML çıktıları telefon ve tablette çalışır. Ortak altyapı `viewer.py`'deki
**`_GESTURE_JS`** sabiti (`installGesture` + `installDrag` + `gTouchActive`) ve
**`_MOBILE_META`** (viewport meta etiketi); dört şablona da (şematik, PCB, 3D,
birleşik kabuk) enjekte edilir — f-string'lerde `{_GESTURE_JS}`, 3D'nin raw
şablonunda `__GESTURE__`/`__VIEWPORT__` placeholder'ı ile.

- **Jestler**: tek parmak sürükle = pan (3D'de döndürme), iki parmak = pinch
  zoom + aynı anda kaydırma, tek dokunuş = tıklama, çift dokunuş = çift tıklama.
- **`installDrag`**: ayraç/tutamaç gibi basit sürükleme öğeleri (birleşik
  kabuğun ayracı, popup boyutlandırma tutamaçları) — `setPointerCapture` ile
  fare + parmak tek yoldan.
- **Mobil düzen**: `@media (max-width:820px)` — sol paneller kanvasın ÜSTÜNE
  kayan katman olur (varsayılan kapalı; ilk açılışta `innerWidth < 820` ise
  otomatik katlanır), toolbar'lar sarar, dokunma hedefleri büyür, birleşik
  kabuğun üst çubuğunda açıklama/rozet gizlenir. `100dvh` eklendi (mobil adres
  çubuğu açılıp kapanırken `100vh` taşıyordu).

**ÜÇ KRİTİK KURAL** (bkz. Çözülen Sorunlar):
1. Jest yüzeyine CSS'te **`touch-action:none`** verilmeli — yoksa tarayıcı
   jesti kendi alır (sayfa kaydırma/zoom) ve `pointermove` hiç gelmez.
2. `pointerdown`da **preventDefault ÇAĞIRMA** — Chromium'da dokunuş sonundaki
   `click`i de bastırır (parmakla komponent/net seçilemez olur). preventDefault
   yalnız `pointermove`da yapılır.
3. Uyumluluk (compat) fare olaylarına karşı mevcut `mousedown` handler'ları
   **`gTouchActive()`** ile korunur (çift pan olmasın).
4. Köprü (bridge) modunda sentetik `mousedown` DOKUNULAN ÖĞEYE, sonraki
   `mousemove`/`mouseup` **JEST YÜZEYİNE** gönderilir: mousedown handler'ı
   çoğu zaman yeniden render eder (`annoSetSel` → `annoRender`) ve ilk hedef
   DOM'dan KOPAR; kopuk düğüme gönderilen olay window'a bubble ETMEZ
   (not/kutu taşıma bu yüzden hiç ilerlemiyordu).

## Kritik Kurallar

### PyQt6 değil, PyQt5

Bağımlılık uyumsuzluğu nedeniyle PyQt5'e geçtik. Yeni kod yazarken:
- Import: `from PyQt5 import QtWidgets, QtCore, QtGui, uic`
- Event loop: `app.exec_()` (underscore — PyQt6'daki çıplak `exec()` çalışmaz)
- `.ui` dosyasında enum'lar flat: `Qt::Horizontal` (PyQt6'daki scoped
  `Qt::Orientation::Horizontal` PyQt5'in `uic`'inde patlar)

### altium_monkey API detayları

viewer.py üzerinde çalışırken `.claude/rules/altium-monkey.md` otomatik
yüklenir — orada API gotcha'ları, attribute isimleri ve overbar notation
işlemesi var.

### Test akışı

Bir değişiklik yaptıktan sonra:
1. GUI'den projeyi **yeniden üret** (HTML ezildi mi kontrol et)
2. Tarayıcıda **Ctrl+F5** ile aç — cache problemi çok yaygın
3. Üretim saati artık sayfada GÖRÜNMEZ (v2.9.29: kullanıcı isteğiyle build
   damgaları kaldırıldı, sağ üstte yalnız sürüm rozeti var); eski HTML
   şüphesinde sekme BAŞLIĞINDAKİ (title) `HH:MM:SS` GUI log'uyla karşılaştırılır
4. JS davranışı yanlışsa **F12 → Console** — runtime hata orada

## HTML Viewer Özellikleri (özet)

- Grid layout (4 sütun), tüm sayfalar tek pan/zoom kanvasında
- **Not / kutu (annotation) araçları** (v2.9.38+, v2.9.39'da Foxit tarzına
  revize): toolbar'da **Not / Kutu / Kaydet**. Not: butona bas + tıkladığın
  yerde DOĞRUDAN yaz (typewriter, prompt yok; Enter = yeni satır, dışına
  tıkla = bitir, boş = eklenmez). Kutu: sürükleyerek ince (1.5) amber çerçeve.
  Tüm öğeler tıkla-SEÇ → sürükle-taşı; kutular köşe tutamaçlarından
  boyutlandırılır; seçiliyken **Del** siler; seçimde mini bar (−/+/renk/×)
  notta yazı boyutu (4–48), kutuda kenar kalınlığı (0.5–8) ve RENK (not
  yazısı / kutu kenarı — v2.9.40) ayarlar. Not KUTUSUZ çıplak yazıdır
  (v2.9.40; varsayılan koyu kırmızı #c62828). Nota çift tık = yerinde
  düzenle. Esc: araç → seçim sırasıyla bırakır. Otomatik kayıt
  localStorage'da (`schviz-anno:<proje>` anahtarı). **Kaydet** notları HTML'e
  gömüp Chromium'da AÇIK DOSYANIN ÜSTÜNE yazar (File System Access; ilk
  kayıtta dosya seçtirir, handle oturumda saklanır → sonrakiler sessiz ✓;
  v2.9.41). Firefox/engelli ortamda `{proje}_notlu.html` kopyası indirir.
  Yüklemede localStorage ile gömülü veriden `ts`'i yeni olan kazanır.
- **Notları taşıma — Dışa / İçe** (v2.26.0): toolbar'da iki düğme daha.
  **Dışa** notları `{proje}_notlar.json` olarak indirir; **İçe** bir dosyadan
  yükler ve o dosya `_notlar.json` DA olabilir, notları gömülü eski bir HTML de
  (JSON parse başarısızsa `anno-embed` yuvası regex'le ayıklanır). İçe aktarma
  EKLER, silmez: kimlik çakışırsa GELEN nota yeni `annoId()` verilir → mevcut
  notlar kaybolmaz. Geri bildirim `hierToast` ile. **Neden gerekli**:
  localStorage TARAYICIYA bağlıdır ve Chromium ile Firefox burada zıt davranır
  (bkz. Çözülen Sorunlar, v2.26.0) — HTML yeniden üretilince notların
  taşınabilir tek yolu dosyadır.
- **Sol panel katlanabilir** (v2.9.23+): sağ üst köşedeki küçük ◂/▸ ok butonu
  veya `B` kısayolu; kapalıyken 26px şerit kalır. Komponent popup'ı (panele
  dock'lu) açılırsa veya `/` ile arama açılırsa panel otomatik açılır. Durum
  `localStorage`'da (`schviz-ui` anahtarı) hatırlanır; file:// altında storage
  kısıtlıysa try/catch ile sessizce atlanır.
- Sol panel sekmeleri: **Nets** (power=orange, ground=green, signal=gray), **Comps**
  ve **Hiyerarşi** (aşağıdaki bölüm)
- **Net tipi filtre çipleri** (v2.9.25+): Nets sekmesinde Tümü/Güç/GND/Sinyal;
  aramayla birlikte çalışır, Comps sekmesinde gizlenir.
- **Arama katlanabilir** (v2.9.22+): "▸ Ara" başlığı altında, varsayılan KAPALI;
  `/` açar+odaklar, `Esc` kapatır (kapatınca filtre temizlenir). **Enter** görünen
  listedeki ilk sonucu seçer; sonuç yoksa "eşleşen yok" mesajı.
- **Şematik metinleri PDF gibi seçilebilir/kopyalanabilir** (v2.9.22+,
  v2.27.0'da metin katmanına taşındı): sayfa kanvasa çizilir, üstünde saydam
  `<span>`'lardan bir katman durur (`.tl span {user-select:text}`) — fare
  yazının üzerindeyken pan BAŞLAMAZ (native seçim çalışır), boş alanda pan
  normal. Sürükleyip seçim yapıldıysa click handler'ları aksiyonu tetiklemez
  (`window.getSelection()` kontrolü). Seçim vurgusu YARI SAYDAM ki altındaki
  kanvas yazısı okunmaya devam etsin.
- Metin katmanı span'ları tıklanabilir: net adı → bağlantı yayları; block
  (sheet symbol) → hedef sayfaya navigate; komponent designator → detay popup
- **Şematikte designator tıklamasında görünüm KAYMAZ** (v2.9.24+):
  `highlightComponent(desig, sheetId, focus=false)` — sadece kutu çizilir.
  Arama/Comps listesi ve cross-probe `focus=true` (varsayılan) ile ortalar.
- **Boş alana tıklama komponent seçimini iptal eder** (v2.9.24+): pan hareketi
  (`panMoved`, >3px eşiği), metin seçimi ve tıklanabilir öğeler hariç.
- **Hover bilgi balonu** (v2.9.25+): `#svg-tip` — komponentte değer+açıklama,
  net'te bağlantı sayısı+tipi, block'ta hedef; altında eylem ipucu.
- **Toolbar** (v2.9.25+): **Sayfa… açılır menüsü** (sayfaya git), **↰** üst sayfa
  (v2.25.0), **+/−** zoom, **Tümü** (tüm sayfaları sığdır, `fitAll`), anlık renk
  picker'lar (sayfa-arası ve sayfa-içi; seçim `localStorage`'a kaydedilir),
  PNG export, Reset, Clear
- **Yumuşak geçişler** (v2.9.25+): `smoothT()` — fit/reset/zoom butonları 0.35s
  ease; tekerlek/pan anlık kalır (gecikme hissi olmasın). Sidebar katlanması
  0.18s width transition.
- Komponent popup: tüm Altium parametreleri (Manufacturer, Part Number,
  Supplier, Stock, Pricing, …), URL'ler otomatik link, her satırda kopya butonu.
  **PCB cross-probe**: komponentin PCB konumu (X/Y mm, katman, dönüş) + board
  üzerinde **tüm komponentleri** yerleşim haritası olarak gösteren mini görsel
  (`collect_pcb_placement` → JS `drawPcbMap`). Seçili komponent büyük+halkalı,
  diğerleri küçük noktalar (TOP=yeşil, BOTTOM=mavi). Hepsi aynı board-relative
  koordinat çerçevesinde olduğundan hizalama garantili — ayrı bir board görseli
  raster'lanmaz (boyut şişmez, yanlış hizalanma riski yok). PCB proje klasöründen
  otomatik bulunur (Panel olmayan .PcbDoc tercih edilir).
- Çoklu net karşılaştırma: Shift+click (max 4, farklı renk)
- Klavye: `?` modal aç, `/` arama aç+focus, `Enter` (aramada) ilk sonucu seç,
  `B` sol paneli gizle/göster, `H` hiyerarşi sekmesi, `Alt+Backspace` üst sayfa,
  `Alt+Home` kök sayfa, `Alt+←/→` sayfa geçmişi, `0` reset view, `F` fit last,
  `Esc` clear
- PyInstaller paketi için gui.ui dosyası `sys._MEIPASS` üzerinden bulunur
  (gui.py'de fonksiyonla)

### Şematik Hiyerarşi paneli + KiCad tarzı sayfa gezinme (v2.25.0+)

Sol panelde üçüncü sekme: **Hiyerarşi** — KiCad'in "Schematic Hierarchy"
gezgininin karşılığı. Ağaç `build_sheet_hierarchy()` ile **Python'da** kurulur
(`build_html` çağırır, `SHEET_TREE` olarak gömülür); kaynak veri sayfalardaki
sheet symbol (block) referanslarıdır.

- **Ağaç kuralları**: hiçbir block'un hedefi OLMAYAN sayfalar KÖK; her block bir
  alt düğüm. Çocuklar sayfa numarasına göre sıralanır (KiCad da böyle), aynı
  numaralılar kayıt sırasını korur. Düğüm alanları kısa: `id · p` (ebeveyn,
  −1=kök) `· s` (sayfa id, ""=proje dışı) `· t` (etiket) `· n` (sayfa no)
  `· k` (çocuklar) `· miss` (hedef SchDoc projede yok) `· cyc` (döngü kesildi).
- **Aynı SchDoc birden çok kez örneklenebilir** (Altium Repeat kanalları:
  diffI2C_1/2/3 → aynı dosya): her ÖRNEK ayrı düğümdür, hepsi aynı sayfaya
  gider, hiyerarşi YOLU farklıdır. Bu yüzden gezinme sayfa id'siyle değil
  **aktif düğümle** (`curNodeId`) çalışır — yoksa kanaldan çıkarken yanlış üst
  sayfaya dönülürdü. `enterSheet()` hedefin AKTİF düğüm altındaki örneğini seçer.
- **Döngü koruması**: A→B→A referansında düğüm `cyc` ile işaretlenip alt ağaç
  tekrar açılmaz (sonsuz özyineleme olurdu). Yalnız döngü içinde kalan sayfalar
  hiçbir kökten görünmeyeceği için ayrıca kök olarak eklenir — hiçbir sayfa
  ağaçtan düşmez. Hiyerarşisiz (düz) projede her sayfa köktür → düz liste.
- **Sayfa numarası** = sayfanın viewer'daki grid sırası (1 tabanlı); aynı
  dosyanın tüm örnekleri aynı numarayı gösterir (dosya bir kez render ediliyor).
  Satır ipucunda hedef SchDoc adı da yazar (etiket designator olduğundan
  `diffI2C_2` ↔ `[07] - diffI2C` ayrımı görünsün diye).
- **Etkileşim**: satıra tık = o sayfaya git · ok = alt ağacı aç/kapat (durum
  `localStorage`'da `schviz-ui.hierClosed`) · `↰ Üst sayfa` / `⌂ Kök` / `+` / `−`
  düğmeleri · arama kutusu ağacı da filtreler (eşleşenler + ATALARI görünür).
  Aktif satır kalın+vurgulu, aynı sayfayı gösteren diğer örnekler halkalı nokta.
- **Klavye**: `H` sekmeyi aç · `Alt+Backspace` üst sayfa (KiCad "Leave Sheet") ·
  `Alt+Home` kök · `Alt+←/→` sayfa geçmişi (`navHist`, 80 kayıt). Üst sayfa yoksa
  / geçmiş bittiyse `#hier-toast` balonu uyarır. Alt dalı `Backspace` (not silme)
  dalından ÖNCE gelir; `Alt+←/→` tarayıcının geri/ileri gezinmesini bastırır.
- **İmleç her yoldan izler**: takip `fitToSheet()` sonundaki `noteSheetVisit()`
  ile yapılır → sayfa açılır menüsü, arama, kart çift tıklaması ve cross-probe
  da hiyerarşi imlecini taşır (tek nokta, her çağrı yerine yama gerekmez).
- **İKİ TUZAK** (bkz. Çözülen Sorunlar): (1) `#hier-list` `display:flex` aldığı
  için gizleme kuralı ID özgüllüğünde tekrar yazılmalı (`#hier-list.hidden`) —
  `.list-container.hidden` (0,2,0) ID seçicisine (1,0,0) yenilir. (2) `hierReady`
  **`var`** ile bildirilir: `fitToSheet` modül kurulmadan önce çağrılabiliyor,
  `let` olsaydı TDZ hatası verirdi (`__annoUi` deseninin aynısı).

### PCB Viewer: döndürme / ayna + montaj dışa-içe aktarma (v2.12.0+)

- **⟳ (R)** board'u 90° döndürür, **Çevir (X)** aynalar (alt yüzden bakış).
  Görüş merkezindeki nokta yerinde kalır. Dünya↔ekran dönüşümü tek noktada
  (`w2s`/`s2w`/`centerOn`, yönelim `setOrient(rot, mir)`); döndürme 90°'nin
  katlarıyla sınırlı olduğundan kutu (AABB) matematiği bozulmaz.
- **BOM · Montaj → Dışa / İçe**: işaretler `{proje}_montaj.json` olarak
  kaydedilir (grup anahtarı + değer/footprint/designator listesi) ve başka
  makinede/kişide geri yüklenir; bilinmeyen gruplar sayılıp bildirilir.
  (localStorage tarayıcıya bağlı olduğundan devretmenin tek yolu buydu.)

### Şematik render: tek `<canvas>` + draw-list + metin katmanı (v2.27.0+)

Şematik sayfaları artık **SVG DOM'u DEĞİL**, üretimde düzleştirilmiş bir çizim
listesi olarak taşınır ve tarayıcıda TEK kanvasa çizilir — PCB tarafında
v2.12.0'da uygulanan desenin şematik karşılığı. LOD makinesi tamamen kalktı.

- **Üretim**: `svg_to_drawlist(svg, img_table, font_faces, used_fonts)` sayfa
  SVG'sini düz dizilere çevirir — `ln` (çizgi), `rc` (dikdörtgen), `pg`
  (poligon), `el` (elips), `pt` (yay/path), `tx` (yazı), `im` (görsel), `cl`
  (clip dikdörtgenleri), `mt` (birim olmayan matrisler) + stil tabloları
  (`st` şekil, `ts` yazı). `build_html` hepsini tek gzip+base64 blob'unda
  (`DRAW_GZ`) gömer. altium_monkey'in SVG lehçesi bunun için biçilmiş kaftan:
  `<g>`'lerde HİÇ transform yok → koordinatlar mutlak, düzleştirme kayıpsız.
  Yine de parser bir CTM yığını tutar (bir gün transform çıkarsa koordinatlara
  pişirilir).
- **Tekilleştirme**: gömülü `<image>` (logo) ve `@font-face` blokları PROJE
  GENELİNDE bir kez taşınır; `@font-face` yalnız gerçekten kullanılan aile için
  (altium_monkey metrik-uyumlu bir yedek fontu hiç referans edilmese de gömüyor).
  64 sayfalık ölçüm: görseller 23.4 MB → 0.61 MB, fontlar 5.11 MB → 0 (kullanılmıyordu).
- **Çizim**: `dlPrep(d)` sayfa başına stil bazlı `Path2D` paketleri kurar (bir
  kez), `dlDrawSheet` bunları çizer, `schDraw` görünür sayfaları tarar (bbox
  culling). `applyT()` kanvası **SENKRON** çizer — DOM overlay'ler (kart
  çerçevesi, net yayları, notlar, vurgu kutusu) aynı `tx/ty/scale` ile CSS
  transform aldığından ikisi birebir hizalı kalır.
- **`smoothT()` artık JS tween'i** (eskiden CSS transition): kanvas ile DOM
  overlay'in AYNI karede hareket etmesi şart — CSS transition'la overlay
  animasyonla kayarken kanvas anında hedefe atlıyordu.
- **Metin katmanı (PDF.js deseni)**: kanvas yazıyı çizer ama seçilemez. Seçim /
  kopyalama / tıklama / hover için **yalnız görünür sayfalarda ve okunur
  zoom'da** (`TL_MIN_SCALE`, en çok `TL_MAX_SHEETS` sayfa) saydam `<span>`
  katmanı kurulur (`tlBuild`/`tlUpdate`, hareket durunca 140 ms sonra).
  Span'lar `clickable-net` / `block-link` / `comp-designator` sınıflarını
  taşır → mevcut sınıf tabanlı tıklama/hover kodu HİÇ değişmeden çalışır.
  Sınıflandırma `tlClasses(id)` ile draw-list üzerinden yapılır (eski
  `setupNetTexts` + `setupSheetTexts` yerine).
- **Span konumu ölçümle değil MATEMATİKLE** kurulur: font-size = SVG
  font-size (user birimi), `transform: matrix(...)` ile gövde px'ine taşınır;
  taban çizgisi ofseti `ctx.measureText` font metriklerinden hesaplanır
  (`tlMetrics`). Doğrulandı: 60/60 span kanvastaki glifin üstünde.
- **`schBoxToCanvas(sheetId, box)`**: SVG-viewBox kutusu → kanvas koordinatı,
  DOM ölçümü OLMADAN (sayfa kartı + viewBox'tan). Eski `svgBoxToCanvas`
  `getBBox`↔`getBoundingClientRect` eşlemesine dayandığından gizli panelde
  sıfır ölçümle çöküyordu (v2.24.0 yaması); o hata sınıfı yapısal olarak yok.

**İKİ İNCE NOKTA**:
1. `kx`/`ky` çizimde ZOOM'U DA İÇERİR (`bw = sp.w * scale`); metin katmanında
   İÇERMEZ (span'lar `#canvas`'ın CSS transform'u altında). Aynı formülü iki
   yerde kullanırken karıştırma.
2. `vector-effect="non-scaling-stroke"` genişliği `w * scale / k`'dır (SVG'de
   kalınlık viewBox→element eşlemesinden etkilenmez ama dış CSS zoom'undan
   etkilenirdi). `w / k` yazılırsa çizgiler ~zoom katı ince kalır ve **Altium'un
   ayrı kısa segmentlerle çizdiği kesikli oda çerçeveleri kopuk görünür**
   (yuvarlak uçlar boşluğu kapatamaz).

### PCB Viewer: paneller, ölçüm, PNG (canvas)

Sol panelde dört sekme: **Katmanlar · Netler · Komponentler · BOM · Montaj**.

- **Katmanlar**: aç/kapa, ↑ ile katmanı en üste getir (`topLayer` en sona
  çizilir — canvas'ta sonra çizilen üstte; tekrar basınca normal sıraya döner),
  Üst/Alt (`T`), Hepsi, Temizle.
- **Netler**: net adı + pad/iz sayısı, ara, Güç/GND/Sinyal filtrele, tıkla →
  net tüm katmanlarda vurgulanır (bakır ize çift tıklamakla aynı sonuç).
  Çoklu net vurgusu `selNets` + Set tabanlı filtreyle (`drawLayer(li, netSet)`)
  yapılır.
- **BOM · Montaj** (InteractiveHtmlBom / KiCad iBOM tarzı montaj akışı):
  komponentler değer + footprint ikilisine göre gruplanır (anahtar
  `değer\u0000footprint`), satıra tıkla → grubun TÜM komponentleri vurgulanır
  (`selComps`; tek seçimde ayrıca **pin-1 sarı halkası**), ✓ ile montaj takibi
  (`schviz-bom:<proje>` anahtarıyla localStorage'da, `N/M yerleştirildi` sayacı
  + Sıfırla), Tümü/Üst/Alt/Kalan filtreleri, arama, **Dışa / İçe** aktarma.
  Board'da komponent seçilince `bomMark()` ilgili satırı işaretleyip görünür
  kılar.
- **Ölçüm aracı** (`Ölç` / `M`): iki noktaya tıkla → mesafe mm + mil, Δx/Δy;
  imleç bir **pad/via üzerindeyse MERKEZİNE yapışır** — pad-pad ölçümü göz
  kararı olmaz. Esc iptal.
- **PNG dışa aktarma** (`Görüntü`): o anki görünüm (görünür katmanlar + vurgu +
  ölçüm) PNG olarak indirilir.
- **Yardım modalı** (`?`): fare/klavye, dokunmatik ve panel özeti.
- **Katlanabilir sol panel** (`#sb-toggle`, `B`) ve katlanabilir arama
  (`#search-box`, `/` açar, `Esc` kapatır) — şematik viewer'daki desenin aynısı.
- **Kısayollar**: `F` sığdır, `B` panel, `M` ölçüm, `R` döndür, `X` çevir,
  `P` pad etiketleri, `T` Üst/Alt, `/` arama, `?` yardım, `Esc` temizle.
- **Katman verisi** gzip+base64 gömülüdür, açılışta `DecompressionStream` ile
  çözülür; çok eski tarayıcıda (API yok) info-bar'da uyarı gösterilir.
- **CSS tuzağı** (bkz. Çözülen Sorunlar): gizleme kuralı `.panel.hidden,
  #chips.hidden { display:none !important; }` — `#chips` bir `.panel` DEĞİL,
  yalnız `.panel.hidden` yazılırsa net filtre çipleri her sekmede görünür.

### 3D Viewer: Parçalar butonu (v2.9.26+)

`#tb3d`'de **Parçalar** toggle'ı (varsayılan açık). Kapalıyken `userData.desig`
taşıyan TÜM mesh'ler (extrude gövdeler + STEP modelleri) gizlenir → çıplak
board (levha + bakır/silkscreen dokusu) incelenir. İki kritik detay:
- Three.js Raycaster `visible`'a BAKMAZ → `pick()` içinde
  `pickList.filter(m=>m.visible)` şart, yoksa görünmez parçaya tıklanabilir.
- Cross-probe ile seçim gelirse (`message` handler) parçalar otomatik geri
  açılır (`compBtn.onclick()`), seçim boşluğa düşmez. Gizlerken `setSel(null)`.

## JSON Çıktısı Yapısı

```json
{
  "project": {"name", "path"},
  "summary": {"sheet_count", "net_count", "component_count",
              "pin_connection_count", "has_netlist",
              "has_bom", "has_pnp", "variant_count"},
  "variants": ["...", ...],
  "sheets": [{"id", "name", "components": [{
      "designator", "value", "description"?, "footprint"?,
      "library_reference"?, "parameters"?,
      "pins"?: {"11": {"net": "ADC1_CS", "pin_name": "CS"}, ...}
  }]}],
  "nets": [{"name", "type": "power|ground|signal", "count",
            "sheets": {sheet_name: pin_count},
            "connections"?: ["U5.11 (CS)", "U2.7 (CS)", ...]}],
  "bom"?: [{"designator", "value", "footprint", "library_ref",
            "description", "parameters", "dnp"}],
  "pnp"?: [{"designator", "comment", "layer", "footprint",
            "center_x", "center_y", "rotation"}]
}
```

`bom`/`pnp` yalnızca veri varsa eklenir. SVG **dahil değil** (LLM'in işine
yaramaz, token israfı). Komponent parametreleri sadece boş değilse dahil edilir.

### Pin→Net bağlantısı (KRİTİK — netlist)

JSON artık **gerçek elektriksel bağlantı** içeriyor. İki yerden erişilir:
- Net bazlı: `nets[].connections` = o net'e bağlı tüm pinler
- Komponent bazlı: `sheets[].components[].pins` = pin no → bağlı net

Bu, `compile_netlist()` ile multi-sheet derlemeden gelir (bkz.
`.claude/rules/altium-monkey.md`). Eskiden JSON sadece "net X, Y sayfasında
geçiyor" diyordu; pin atamasını veremiyordu ve AI MCU port analizini
doğrulayamıyordu. Artık "U5.11 → ADC1_CS" gibi kesin bağlantı var.

v2.9.30'dan itibaren derleme projenin KENDİ netlist ayarlarıyla yapılır
(`NetlistOptions.from_prjpcb`) ve proje klasöründe PcbDoc varsa netler
**PCB'den yeniden kurulur** (`_merge_netlist_with_pcb` — kesin doğru bağlantı
+ fiziksel kanal designator'ları; ayrıntı: Çözülen Sorunlar). PCB yükleme
maliyeti nedeniyle netlist adımı PCB'li projelerde daha uzun sürer.

`has_netlist: false` ise netlist derlemesi başarısız olmuş demektir (JSON yine
üretilir ama `connections`/`pins` alanları boş kalır) — üretim log'unda hata
mesajına bak.

## Mimari Kararlar

- **Tek-dosya HTML stratejisi**: SVG'ler gömülü, server gerekmez (`file://` ile
  açılır). Dosya büyük ama portable.
- **İki-pass parse**:
  - Pass 1: SchDoc yükle, SVG render et, net adlarını topla
  - Pass 2: Her sayfanın SVG'sinde tüm net adları için pozisyon çıkar
    (`extract_label_positions`). SVG'de yakalanmayan net'ler için fallback
    sayfa merkezi (rx=0.5, ry=0.5).
- **Block navigation**: SVG-text-tarama YERINE Python tarafında
  `get_sheet_symbols()` ile kesin veri çıkar, JS'e `sheet_positions[id].blocks`
  olarak gönder. Daha güvenilir.
- **Komponent designator tıklama**: Sayfa-bazlı map (`compsBySheet[sheetId]
  [designator] = comp`), SVG text içeriği bu map'te varsa tıklanabilir.

## Bilinen Kısıtlar

- Net adı bir komponent designator ile çakışırsa net önceliği var (uncommon).
- BOM/PnP `AltiumDesign` API'sine bağlı; çok eski altium_monkey sürümlerinde
  bu API olmayabilir (graceful fallback var, "veri yok" der).

## Çözülen Sorunlar (tarihçe)

- **Chromium'da şematik gezinmesi 64 sayfalık projede kullanılamaz hale
  geliyordu — SVG DOM'u bırakıldı, kanvasa geçildi (v2.27.0, kullanıcı
  bildirimi: "cromium tabanlılarda şematik gerçekten çok yavaşlıyor, Firefox
  daha iyi; LOD ekledik ama 64 şemalık projede çok kötü. PCB tarafı akıcı
  çalışıyor.")**: v2.9.34-v2.15.0 arasındaki LOD yamaları 8 sayfada işe
  yarıyordu ama ölçekte iki maliyeti ÜST ÜSTE bindiriyordu.
  **Ölçüldü** (BRK-210'un 8 sayfası 8× kopyalanıp gerçek `build_html` ile 64
  sayfalık viewer üretildi, headless Edge): **180 512 SVG elemanı** (toplam
  186 338 DOM düğümü) + **132 MB LOD bitmap** + **29.05 MB HTML**; SVG'lerin
  enjeksiyonu 4.2 s, LOD bitmap'lerinin hazır olması +11.2 s. Ana iş parçacığı
  darboğaz DEĞİLDİ (`applyT` medyanı 0.1 ms) — v2.9.34'teki teşhis doğruydu:
  Chromium CSS-transform edilen dev SVG katmanını her zoom adımında CPU'da
  yeniden rasterize ediyor; Firefox/WebRender vektörü GPU'da çizdiği için
  akıcı. Yani LOD yanlış katmandaydı: SVG ağacı bellekte DURUYOR, üstüne
  bitmap ekleniyordu.
  **Çözüm** PCB'de v2.12.0'da yapılanın aynısı: geometri üretimde
  düzleştirilip (`svg_to_drawlist`) tek `<canvas>`'a çizilir; LOD makinesi
  (`buildLods`/`lodRetune`/`updateLod`/`lod-bitmap` + toolbar toggle'ı)
  TAMAMEN silindi. Ayrıntı: "Şematik render" bölümü.
  **Metin seçimi KAYBOLMADI** (v2.9.22'den beri var olan "PDF gibi kopyala"):
  PDF.js'in yöntemiyle, yalnız görünür sayfalar için saydam `<span>` katmanı
  kurulur — mevcut sınıf tabanlı tıklama/hover kodu hiç değişmeden çalışır.
  **Ölçülen sonuç** — aynı 64 sayfalık proje: DOM 186 338 → **877** (sayfa
  düğümü 180 512 → **128**), LOD bitmap 132 MB → **0**, HTML 29.05 → **8.92 MB**,
  kare çizimi **1.2 ms** (tüm sayfalar ekranda) / **0.8 ms** (tek sayfaya
  yakın), açılış 4.2 s → 0.4 s. Gerçek BRK-210 (8 sayfa): 3.80 → **1.72 MB**,
  sayfa DOM'u 22 596 → **16**, LOD 16 MB → 0; üretim süresi DEĞİŞMEDİ (41 s —
  maliyet `to_svg`'de). Birleşik görünüm 8.90 → **6.80 MB**.
  **Fidelity kanıtı** (kontrollü test — aynı sayfa, aynı piksel boyutu,
  tarayıcının KENDİ SVG rasterizeri vs kanvas): zoom 1.0/2.0/4.0'da farklı
  piksel **%0.31 / %0.38 / %0.35**, 8× küçültülmüşte ortalama fark 0.79/255,
  toplam "mürekkep" 0.0654 vs 0.0663 (%1.4). Kalan fark glif antialiasing'i.
  **Yol boyunca yakalanan iki hata**: (1) `vector-effect="non-scaling-stroke"`
  genişliği önce `w/k` yazılmıştı; doğrusu `w*scale/k` — SVG'de kalınlık
  viewBox→element eşlemesinden etkilenmez ama dış CSS zoom'undan etkilenirdi.
  İnce çizilince Altium'un ayrı kısa segmentlerle çizdiği **kesikli oda
  çerçeveleri kopuk** görünüyordu (yuvarlak uçlar boşluğu kapatamıyor).
  (2) `smoothT()` CSS transition'la kalırsa DOM overlay animasyonla kayarken
  kanvas anında hedefe atlıyor → 350 ms boyunca ikisi ayrı düşüyor; JS tween'e
  çevrildi.
  **Yan kazanç**: gömülü logo her sayfada tekrar gömülüyordu (64 sayfada
  23.4 MB → 0.61 MB) ve altium_monkey hiç referans edilmeyen bir yedek fontu
  (Arimo, 0.64 MB/sayfa → 64 sayfada 5.11 MB) gömüyordu — ikisi de proje
  genelinde tekilleştirildi, font yalnız gerçekten kullanılıyorsa taşınıyor.
  **Ayrıca düzelen**: komponent vurgu kutusu artık DOM ölçümünden değil
  matematikten geliyor (`schBoxToCanvas`) → v2.24.0'daki "gizli panelde ölçüm
  0" hata sınıfı yapısal olarak yok; v2.9.42'deki sayfalar arası SVG id
  çakışması da imkânsız (clip'ler sayfa içinde Python'da çözülüyor).
  **Doğrulama** (headless Edge + CDP): şematik 13/13 (BRK-210 8 ve 64 sayfa,
  Smart_MCU) · özellik regresyonu 10/10 (hiyerarşi, Alt+Backspace, arama,
  sayfa menüsü, not/kutu, localStorage, Kaydet klonu, panel katlama, seçim
  temizleme) · kaydedilen kopya round-trip + Python not taşıma 6/6 · birleşik
  görünüm 11/11 (çift yönlü cross-probe, net cross-probe, gizli panelde seçim,
  3D) · `node --check` temiz · `tools/check_html_i18n.py` 239/239, ölü
  anahtar 0 · İngilizce çıktıda görünen Türkçe metin 0.
  **Test notu**: kanvas `#viewport` genişliğindedir, `innerWidth` DEĞİL — CDP
  testinde `getImageData` koordinatı `(clientX - viewportRect.left) * dpr`
  ile hesaplanmalı; `innerWidth`'e göre ölçeklenince span/glif örtüşme testi
  yanlışlıkla 25/60 veriyordu.

- **Uygulama güncellenip HTML yeniden üretilince eski notlar yeni dosyaya
  gelmiyordu (v2.26.0, kullanıcı bildirimi)**: Notlar iki yerde durur —
  localStorage (`schviz-anno:<proje>`, her değişiklikte otomatik) ve "Kaydet"
  ile HTML'e gömülen `anno-embed` yuvası; açılışta `ts`'i yeni olan kazanır
  (taze üretilen HTML'de yuva `null` olduğundan localStorage kazanır).
  **Ölçüldü (headless, temiz profil)**: Chromium'da (Edge/Chrome) TÜM `file://`
  sayfaları TEK localStorage havuzunu paylaşır — dosya adı/klasörü değişse bile
  notlar gelir (`--allow-file-access-from-files` olmadan da). **Firefox tam
  tersi**: `file://` deposunu DOSYA YOLUNA + ADINA göre böler; profil klasöründe
  origin dizinleri `file++++C++…+eski+a.html` ve `file++++…+yeni+b.html` diye
  AYRI oluştu, ikinci dosya birincinin verisini okuyamadı (`SONUC_BULAMADI`).
  Yani Firefox'ta HTML yeniden üretilip adı/klasörü değişince notlar kaybolmuş
  GİBİ görünür (aslında eski adın deposunda durur) — kullanıcının bildirdiği
  durum tam olarak bu. localStorage tarafında JS ile yapılabilecek bir şey YOK:
  bölünen şey anahtar değil ORIGIN'in kendisi.
  **Çözüm iki katmanlı, ikisi de dosya düzeyinde** (tarayıcıdan bağımsız):
  (1) Şematik toolbar'ına **Dışa / İçe** düğmeleri — `{proje}_notlar.json`;
  içe aktarma HTML dosyası da kabul eder (gömülü yuvayı regex'le ayıklar) ve
  mevcut notların üstüne EKLER (kimlik çakışırsa gelene yeni kimlik).
  (2) GUI → **Dosya → Notları Eski Çıktıdan Taşı…** — kaynak (eski HTML veya
  `_notlar.json`) ve hedef HTML seçilir, notlar hedefin `anno-embed` yuvasına
  gömülür. Yeni `read_annotations` / `write_annotations` (viewer.py) bunu
  yapar; **birleşik görünüm de desteklenir**: şematik iç HTML'i `SCH_GZ`
  base64'ünden çözülüp yuvası yazılır ve yeniden sıkıştırılır (kabukta yuva
  yoktur, tepeden regex bulamaz). Hedefte not varsa GUI onay sorar; üretim
  sürerken eylem kilitlenir (`_menu_action_items` — çıktı dosyası o sırada
  yeniden yazılıyor olabilir).
  **Üç ayrıntı**: (i) gömülen JSON'da `<` → `\u003c` kaçırılır, yoksa not
  metnindeki bir script kapatma etiketi yuvayı erken kapatır (annoBuildHtml'in
  kuralının Python karşılığı); (ii) yazılan `ts` ŞİMDİ'dir — yoksa hedef
  makinede duran daha yeni localStorage kaydı taşınan notları ezerdi;
  (iii) okuma biçimi uzantıdan değil İÇERİKTEN anlaşılır, bozuk/yabancı
  kayıtlar süzülür (yalnız `k` = note/box ve sayısal x/y geçer).
  **Doğrulama**: dosya düzeyi 12/12 (round-trip, kaçış, JSON kaynak, bozuk
  kayıt süzme, yuvasız hedefte ValueError, ts tazeliği) · headless Edge + CDP
  21/21 (gömülü notların açılışta yüklenmesi, Dışa'nın indirdiği JSON'un adı ve
  içeriği, JSON'dan ve HTML'den içe aktarma, kimlik çakışması, geçersiz dosya,
  notsuzken indirme yapmama, 0 JS hatası) · birleşik görünüm 9/9 (combined
  yazma + tarayıcıda şematik iframe'inde notların görünmesi) · offscreen Qt
  14/14 (menü konumu, slot çağrısı, üretim kilidi, TR→EN→TR, eksik çeviri yok,
  gerçek taşıma, aynı dosya ve yuvasız hedef uyarıları) · TR/EN çıktı 17/17
  (`node --check` temiz, ⟪⟫ kalıntısı 0) · `tools/check_html_i18n.py` 240/240,
  ölü anahtar 0.
  **Test notu**: Chromium'da tüm `file://` sayfaları localStorage'ı paylaştığı
  için ardışık sayfa testlerinde önceki testin notları bir sonrakine SIZAR —
  "taze dosya boş olmalı" kontrolünden önce `localStorage.clear()` şart (ilk
  koşuda 3 test bu yüzden yanlış FAIL verdi).
  **Yapılmadı (aday iş)**: üretimde otomatik devralma (üzerine yazılacak
  dosyadaki yuvayı okuyup yeni HTML'e gömmek) — Chromium'da zaten sorun yok,
  Firefox'ta ise kullanıcı indirdiği `_notlu.html`'i çıktının üstüne
  kopyalamadıkça işe yaramaz; ayrıca notlar MUTLAK kanvas koordinatında
  olduğundan sayfa sayısı/sırası değişen projede kayar (kalıcı çözüm: notu
  sayfa id + orana bağlamak).

- **Şematik hiyerarşi paneli + KiCad tarzı sayfa gezinme (v2.25.0, kullanıcı
  isteği: KiCad 10'un "Şematik Hiyerarşi" panelinin ekran görüntüsü + "Alt+
  Backspace ile ana hiyerarşi şemasına dönme vb.")**: Viewer sayfa hiyerarşisini
  HİÇ göstermiyordu — block yazısına tıklayınca alt sayfaya gidiliyor ama geri
  dönmenin yolu yoktu ve tasarımın ağaç yapısı hiçbir yerde görünmüyordu.
  Ağaç zaten elimizdeki veriden (`sheets[].blocks` = sheet symbol referansları)
  türetilebiliyordu; yeni `build_sheet_hierarchy()` bunu düğüm listesine çevirip
  `SHEET_TREE` olarak gömüyor (ayrıntı: "Şematik Hiyerarşi paneli" bölümü).
  **Veri tarafında üç karar**: (1) hedefi projede OLMAYAN block'lar artık
  atılmıyor, "(bu projede yok)" düğümü olarak çiziliyor (ağaç eksiksiz görünsün;
  tıklanabilir link yine üretilmiyor); (2) çocuklar sayfa numarasına göre
  sıralanıyor — KiCad gezgininin sırası bu ve BRK-210'da kayıt sırasıyla da
  örtüşüyor; (3) döngü (A→B→A) `cyc` ile kesiliyor, yalnız döngüde kalan
  sayfalar ayrıca kök yapılıyor → hiçbir sayfa ağaçtan düşmüyor (düz projede
  her sayfa kök = düz liste).
  **Gezinme neden sayfa id'siyle DEĞİL düğümle**: BRK-210'da `[07] - diffI2C`
  üç kez örneklenmiş (diffI2C_1/2/3); sayfa id'siyle çalışan bir "üst sayfaya
  dön" her kanaldan aynı yere döner ve hangi kanalda olduğumuz kaybolurdu.
  Aktif düğüm (`curNodeId`) tutulunca `enterSheet()` hedefin AKTİF düğüm
  altındaki örneğini seçiyor, `leaveSheet()` o örneğin ebeveynine dönüyor
  (test: diffI2C_2'den Alt+Backspace → köke değil `U_[06] - MCU`'ya).
  İmleç `fitToSheet()` sonundaki `noteSheetVisit()` ile taşınıyor → sayfa
  menüsü / arama / kart çift tıklaması / cross-probe da hiyerarşiyi izliyor.
  **Üç tuzak**: (i) `#hier-list` `display:flex` aldığından `.list-container.hidden`
  (0,2,0) ID seçicisine (1,0,0) yeniliyordu → panel hiç gizlenmezdi; gizleme
  `#hier-list.hidden` olarak yeniden yazıldı (v2.14.0'daki `#chips.hidden`
  hatasının aynısı). (ii) `hierReady` **`var`** olmalı: `fitToSheet` modül
  kurulmadan çağrılabiliyor, `let` ile TDZ hatası verirdi. (iii) **Şablonlarda
  `<html lang="tr">` sabit yazılıydı** → İngilizce çıktıda CSS
  `text-transform:uppercase` TÜRKÇE büyütme kuralını uygulayıp "Hierarchy"yi
  **"HİERARCHY"** (noktalı İ) yapıyordu; `_tr_html()` artık dil etiketini etkin
  dile çekiyor (aynı hata mevcut "COLOR PİCKERS" başlığında da vardı — o da
  düzeldi).
  **Doğrulama** (headless Edge + CDP): TR şematikte **35/35** (ağaç yapısı,
  kanal düğümleri, panel/sekme görünürlüğü, ağaçtan gezinme, Alt+Backspace
  (kanaldan doğru üst sayfa dahil), kökte uyarı balonu, block yazısıyla dala
  girme, Alt+Home, Alt+←/→ geçmişi ve geçmişe kayıt eklememesi, aç/kapat +
  localStorage kalıcılığı, ağaç araması, `H` kısayolu, toolbar ↰, net/komponent
  seçimi regresyonu, 0 JS hatası) · EN + birleşik görünüm **15/15** (EN'de
  Türkçe karakter 0, dil etiketi `en`, birleşik görünümün şematik iframe'inde
  ağaç dolu, iframe içinde Alt+Backspace, Böl moduna geçiş, cross-probe
  regresyonu) · `node --check` temiz · `tools/check_html_i18n.py` 234/234,
  ölü anahtar 0.
  **Test notu**: birleşik görünümde `#hier-tree` srcdoc ayrıştırılır
  ayrıştırılmaz DOM'a giriyor ama SATIRLAR iframe script'i çalışınca doluyor —
  beklerken satır sayısına bakılmalı (ilk testte elemanın varlığına bakıldığı
  için "ağaç boş" sanıldı). `srcdoc` iframe üst sayfanın origin'ini miras
  aldığından DOM testleri `contentDocument` ile doğrudan yapılabiliyor
  (izole dünya gerekmiyor); `contentWindow` üzerinden yalnız `var` değişkenler
  görünür (`hierReady` görünür, `let/const` SHEET_TREE görünmez).

- **Gizli panele gelen cross-probe seçimi ŞEMATİKTE alakasız yeri gösteriyordu
  (v2.24.0, kullanıcı bildirimi: "PCB'de komponent seç → 3D doğru → Şematiğe
  geçince alakasız bir bölüm; Böl sayfasında her şey doğru")**: Tek-panel
  modlarında (Şematik / PCB / 3D) diğer paneller `display:none`'dır → o
  iframe'in İÇİNDEKİ her `getBoundingClientRect()`/`getBBox()` **SIFIR** döner.
  `highlightComponent` kutuyu `svgBoxToCanvas()` ile designator yazısının
  bbox↔ekran eşlemesinden türetiyor; ölçüler sıfır olunca ölçek 0 çıkıp kutu
  `(-tx/scale, -ty/scale)` gibi ALAKASIZ bir koordinata düşüyordu. Ölçüldü
  (headless Edge + CDP, Smart_MCU): gizliyken `schMarkerBox = {x:-138.3,
  y:-138.3, w:10, h:10}`; Şematiğe geçince kutu ekranda (318,−1) 3×3 px,
  U1'in gerçek yazısı ise (886,57) → kullanıcının gördüğü tam olarak bu.
  **Böl modunda iki panel de görünür olduğu için sorun YOKTU** (ölçüm doğru) —
  kullanıcının gözlemiyle birebir uyuşuyor. Aynı sınıf hata TERS yönde de
  vardı: şematikten seçim yapılıp PCB paneli gizliyken `showComp()`'un
  `centerOn()`'u 0×0 alana göre hesaplayıp komponenti sol-üst KÖŞEYE atıyordu
  (ölçüm: ekran (0,0), merkezden 785 px).
  **Çözüm** — iki viewer'da da PCB tarafındaki eski `pendingComp` deseninin
  aynısı: ölçüm yapılamıyorsa (`schMeasurable()` / `pcbMeasurable()`) seçim
  `pendingXpComp`'ta BEKLETİLİR, panel görünür olunca uygulanır. **Tetikleyici
  ResizeObserver DEĞİL** (yalnız yedek): ölçümle görüldü ki gizli iframe hiç
  render edilmediğinden gözlemci teslimatı gecikebiliyor/hiç olmuyor — kabuk
  `setViewMode()` içinde görünür olan panele açıkça **`pane-shown`** mesajı
  yollar, iç viewer bekleyen seçimi o an uygular (ölçü henüz gelmediyse 5×60 ms
  yeniden dener). Seçim temizleme mesajı bekleyen seçimi de düşürür (panel
  açılınca bayat seçim canlanmasın). Ayrıca `fitToSheet`/`fitAll`'a sıfır-ölçü
  koruması eklendi — sıfır alanla `scale = 0` hesaplanıyordu.
  **Doğrulama** (headless Edge + CDP): düzeltme ÖNCESİ derlemede hata birebir
  üretildi, sonrasında 8/8 regresyon geçti — Böl modunda sch→pcb/sch→3D,
  pcb→sch kutusu, seçim temizleme yayılımı, net cross-probe (gidiş + bırakma),
  gizliyken seçilip 3D'ye geçiş ve **3D → Şematik** (bildirilen senaryo).

- **Birleşik görünümün üst çubuğuna tam ekran düğmesi (v2.24.0, kullanıcı
  isteği)**: Mod düğmeleri ile sürüm rozeti arasında, dört köşe ikonlu
  `#vm-fs`. Tarayıcının F11'i ile aynı işi yapar (`requestFullscreen` /
  `exitFullscreen`); işaret durumu `fullscreenchange`'den, yani pencerenin
  GERÇEK durumundan okunur (kullanıcı Esc/F11 ile de çıkabilir). API yoksa
  düğme hiç gösterilmez, izin reddedilirse promise sessizce yutulur.
  **CSS ayrıntısı**: düğme mod grubunun DIŞINDA olduğundan `.vm-btn:first/
  last-child` köşe kuralları ona uymaz → `.vm-btn.fs-btn` ile kendi yuvarlaması
  verildi (eşit özgüllük, sonra geldiği için kazanır).
  **Doğrulama** (headless Edge + CDP, 6 kontrol): sayfa yüklenmeden önce
  `requestFullscreen`/`exitFullscreen` sahtelenip GERÇEK tıklama gönderildi —
  giriş 1 çağrı, tam ekrandayken tıklama 1 çıkış çağrısı, işaret her iki yönde
  senkron, konum (mod grubu ile rozet arası) ve mod düğmelerinin
  `.active` mantığı bozulmadı.

- **Menü çubuğuna Tam Ekran eklendi (v2.23.0, kullanıcı isteği)**: Yeni
  **Görünüm** menüsü (Üret ile Ayarlar arasında) + işaretlenebilir "Tam Ekran"
  eylemi, `F11`. **İki tuzak**: (1) `showNormal()` maximize durumunu da
  kaldırır → büyütülmüş pencereden tam ekrana geçip dönünce pencere küçülüyordu;
  geçişten önce `_was_maximized` saklanıp çıkışta `showMaximized()` çağrılıyor.
  (2) Pencere durumu menü dışından da değişebilir (pencere yöneticisi, OS
  kısayolu) → `changeEvent`/`WindowStateChange` ile eylem işareti
  `isFullScreen()`e eşitlenir; yoksa menüdeki ✓ gerçeği yansıtmaz. Eylem
  `_menu_action_items`'a KONMADI (üretim sürerken de tam ekran yapılabilsin).
  Menü çubuğu tam ekranda da görünür kaldığından çıkış yolu hep elde.
  **Doğrulama** (offscreen Qt, 7 kontrol): menü sırası, kısayol/işaretlenebilirlik,
  tetikle→tam ekran→geri, maximize korunumu, dışarıdan değişimde işaret senkronu,
  üretim kilidine dahil olmaması, TR→EN→TR gidiş-dönüşü.

- **Klasik (katman-SVG'li) PCB görüntüleyici kaldırıldı (v2.22.0, kullanıcı
  isteği: "hızlı pcb oluşturma daha yetenekli ve performanslı çalışıyor,
  eskisine gerek yok")**: İki PCB yolu paralel duruyordu — `to_layer_svgs()`
  çıktısını gömen klasik yol ve `extract_pcb_geometry()` + canvas kullanan
  geometri yolu. Geometri yolu her ölçüde önde (BRK-210: **51.9 s / 4.45 MB**
  ile klasik yolun 135 s / 8.0 MB'ı; birleşik görünüm **62.7 s / 8.88 MB** ile
  402 s / 13.28 MB'ı) ve özellik olarak da eksiği yok — üstüne ölçüm/döndürme/
  çevirme, her zoom'da akıcılık ve LOD gerektirmemek gibi fazlası var.
  **Silinenler** (viewer.py ~2 300 satır): `generate_pcb_viewer`,
  `build_pcb_html`, `collect_pcb_layers`, `_recolor_pcb_layer`,
  `_extract_svg_inner` ve yalnız klasik yolun kullandığı doku üreticileri
  `_build_board_surface` + `_svg_path_bbox`. `generate_combined_viewer`'ın
  `fast_pcb` parametresi ve iki dallı yapısı kalktı (PCB paneli HER ZAMAN
  canvas); GUI'de klasik buton (`pcbViewerBtn`) ve "Birleşikte hızlı PCB
  kullan" kutucuğu + eş menü eylemi kaldırıldı, kalan buton **"PCB
  Görüntüleyici"** adını ve `Ctrl+2` kısayolunu devraldı (birleşik `Ctrl+4`
  → `Ctrl+3`), çıktı adı `_PCB_hizli.html` → `_PCB.html`.
  **3D dokusu KAYBOLMADI**: `_build_surface_from_geometry()` (v2.14.0) aynı
  bakır/pad/silkscreen dokusunu geometriden çiziyor — BRK-210 ve Smart_MCU'da
  `surf.ok = 1` doğrulandı. **Tek gerçek kayıp**: solder mask / paste
  katmanları listelenmez (Altium onları pad'lerden türetiyor, dosyada
  primitive olarak yok) — zaten hızlı modun bilinen kısıtıydı.
  **i18n temizliği**: klasik şablonla birlikte ölü kalan **69 `_EN_HTML`**
  anahtarı, 21 `_EN_LOG` ve 7 GUI anahtarı silindi; `PCB geometrisi
  çıkarılıyor (hızlı mod)` → `PCB geometrisi çıkarılıyor` (artık tek mod).
  `tools/check_html_i18n.py`: **205/205 kapsandı, ölü anahtar 0**.
  **Doğrulama**: offscreen Qt ile 12 kontrol (kaldırılan widget'lar yok, menü/
  kısayol düzeni, `_BTN_LABELS` ↔ gui.ui birebir, TR→EN→TR gidiş-dönüşü,
  eksik çeviri yok, `fast_pcb` imzalardan düştü, viewer'da klasik semboller
  kalmadı) · Smart_MCU + BRK-210 için PCB / birleşik / şematik üretimi sorunsuz
  · birleşik çıktının PCB paneli canvas (`LAYER_GZ` yok), 3D `surf` dolu,
  8 satır-içi script `node --check` ile temiz, çıktıda ⟪⟫ kalıntısı 0.

- **Üretilen HTML görüntüleyiciler hep Türkçeydi (v2.21.0, kullanıcı isteği:
  "html de hangi dilde ise ona göre yapılsın")**: v2.20.1'de GUI ve log
  çevrildi ama üretilen HTML'in kendi arayüzü (şematik / PCB / geometri / 3D /
  birleşik kabuk) Türkçe kalıyordu. Ölçüm: beş şablon, ~5100 satır HTML/CSS/JS.
  **Yöntem seçimi**: (a) çıktı HTML'inde metin değiştirmek REDDEDİLDİ — net
  adı/designator/komponent değeri/kullanıcı notu gibi çalışma-anı verisi
  yanlışlıkla çevrilebilirdi; (b) her metni `{tr(...)}` ile sarmak da olmazdı,
  çünkü şablonların ikisi f-string DEĞİL (ham `.replace()` şablonu). Seçilen:
  **kaynakta ⟪metin⟫ işareti + üretim sonunda `_tr_html()`** — tek sözdizimi
  her iki şablon türünde çalışır, veriyle çakışma imkânsız.
  **İşaretleme dört geçişte yapıldı** (her geçiş bir öncekinin kör noktasını
  kapattı): (1) Türkçe'ye özgü harf (çğışöü) taraması — 237 konum; (2) bu
  harfleri İÇERMEYEN etiketler (`Katmanlar`, `Netler`, `Hepsi`, `Kaydet`,
  `Zemin`) için HTML bağlam taraması — 74 konum; (3) JS dizge sabitleri —
  canvas şablonunun **ASCII'ye indirgenmiş Türkçesi** buradan çıktı
  (`Tum montaj isaretleri silinsin mi?`, `grup yuklendi`, `Gecersiz dosya`);
  (4) headless tarayıcıda GÖRÜNEN metni döküp gözle tarama — çok satırlı
  yardım hücreleri, `▸ Ara`, `Kaydet` ve `88 komponent` sayaç satırı ancak
  burada yakalandı. Toplam **274 anahtar**.
  **Üç tuzak**: (i) işaret bir placeholder'ı kapsarsa (`{project_name}`,
  `__DATA__`) anahtar çalışma anında tutmaz → işaretler placeholder
  sınırlarında bölündü; (ii) f-string'e `}}` yerine `}` yazmak sözdizimini
  bozdu (değiştirme metnini f-string ile kurunca `}}` sadeleşti) — literal
  süslü parantez ÇİFT yazılmalı; (iii) JS'teki `board\\'da` gibi kaçışlı
  metinlerde kaynak biçimi ile çalışma-anı biçimi FARKLIDIR, katalog anahtarı
  çalışma-anı biçimidir (denetim betiği ikisini de dener). Çeviri metinlerinde
  `' " < >` yasak (tırnaklı JS dizgesi / HTML attribute'u içine gömülüyorlar).
  **Regresyon kanıtı**: Türkçe modda dört görüntüleyicinin çıktısı değişiklik
  öncesiyle **birebir aynı** (gzip başlığındaki mtime ve build saati
  normalize edilerek, iç içe gömülü HTML'ler çözülerek karşılaştırıldı) —
  yani işaretleme Türkçede tam bir no-op. **İngilizce doğrulama**: TR+EN
  toplam 24 satır-içi script `node --check` ile temiz; dört görüntüleyicide
  görünen 267 arayüz metni tarandı, Türkçe kalan **0**; BRK-210 (8.5 MB
  birleşik) sorunsuz üretildi, işaret kalıntısı yok. Kalıcı denetim:
  `tools/check_html_i18n.py` (274/274 kapsandı).

- **GUI İngilizceyken üretim log'u Türkçe kalıyordu (v2.20.1, kullanıcı
  bildirimi: "gui ingilizce ama log çıktıları türkçe")**: v2.20.0 yalnız PyQt
  arayüzünü çeviriyordu; log satırları ve ilerleme çubuğu etiketleri
  `viewer.py`'den geliyor. Ölçüm: **151 `log()`/`prog()` çağrısı, 136 benzersiz
  şablon** — çoğu f-string. Elle düzenleme yerine **AST güdümlü tek seferlik
  betik** (`scratchpad/rewrite_logs.py`; `add_doxygen.py` ile aynı desen)
  kullanıldı: her çağrının yalnız ARGÜMANI `tr("şablon").format(a0=…)` ile
  değiştirildi. **İki teknik ayrıntı**: (1) `ast` sütun ofsetleri UTF-8
  **BAYT** ofsetidir — Türkçe karakterli satırlarda karakter indeksiyle
  düzenleme kayar, bu yüzden dosya bayt olarak açılıp düzenlemeler SONDAN BAŞA
  uygulandı; (2) f-string'in sabit parçalarındaki literal `{`/`}` karakterleri
  `{{`/`}}` olarak kaçırılmalı, yoksa sonradan gelen `.format()` çağrısı
  patlar. Betiğin atladığı 5 çağrı elle yazıldı: 3'ü BinOp (`%`-biçimli veya
  koşullu ek içeren), 2'si zaten çevrilmiş etiketi geçiren lambda
  (`progress=lambda frac,label: prog(…, label)` — dokunulmamalıydı). Ayrıca
  `ast.Name` filtresine takılmayan `self.log(...)` çağrıları (kütüphane uyarı
  özetleri) ve 3D STEP bağımlılık `RuntimeError`'ı elle çevrildi.
  **Regresyon kanıtı**: 9 üretim modu (json/bom/pcbgeo/html/pnp/icmap/mcupin/
  pcbview/combined) değişiklik öncesi ve sonrası çalıştırıldı → Türkçe log
  **bit bit aynı** (tek fark build saati); BRK-210'da eski kod ile yeni kodun
  JSON çıktısı **aynı MD5** ve log birebir. **İngilizce kapsam**: iki projede
  259 log satırı tarandı, Türkçe karakter kalan satır **0**; ilerleme çubuğu
  etiketleri de çevriliyor (`5% Reading PCB … 100% Completed`).
  **Not**: dil `i18n` modül-global'inde tutulduğundan `GeneratorThread`
  (ayrı thread) ek bir şey yapmadan doğru dili kullanır; `tr()` sözlük okuması
  olduğu için thread-safe. viewer.py'yi kütüphane olarak import eden
  script'lerde dil seçilmediğinden metinler Türkçe kalır (davranış değişmedi).

- **Üst menü çubuğu + İngilizce dil desteği (v2.20.0, kullanıcı isteği)**:
  Arayüzde menü yoktu (her işlev yalnız butondan erişilebiliyordu, klavye
  kısayolu yoktu) ve tüm metinler Türkçeye gömülüydü. Eklenenler: dört menülü
  çubuk (Dosya/Üret/Ayarlar/Yardım, `Ctrl+O/S/B/Q`, `Ctrl+1..4`, `F1`) ve
  `i18n.py` sözlük tabanlı TR→EN çeviri katmanı (Ayarlar → Dil, anında geçiş,
  `QSettings` ile kalıcı; kayıt yoksa Türkçe → mevcut davranış korunur).
  **Tasarımda çözülen iki tuzak**: (1) Metinler yerinde çevrilseydi
  İngilizceye geçtikten sonra widget metni katalog ANAHTARI olmaktan çıkar,
  Türkçeye dönüş imkânsız olurdu → metinler açılışta Türkçeyken yedeklenip
  (`snapshot_widgets`) her dil değişiminde KAYNAKTAN yeniden çevriliyor.
  (2) Genel bir "tüm `text` özelliklerini çevir" taraması `QLineEdit.text`
  (kullanıcının yazdığı proje yolu) ve renk butonlarının metnini (`#4ec9b0`
  = seçili hex kodu, bir ETİKET değil VERİ) de yedekleyip dil değişiminde geri
  yazardı → yedek sınıf bazında kısıtlandı (QLineEdit'ten yalnız
  `placeholderText`) ve renk butonları ada göre dışlandı; test bu ikinci
  tuzağı yakaladı (`missing_keys` çıktısında `#4ec9b0`/`#ff9800` belirdi).
  Yan düzeltmeler: `pcbGeoBtn` üretim sırasında devre dışı kalanlar listesinde
  YOKTU (üretim sürerken tıklanabiliyordu) → eklendi; `_BTN_LABELS` değerleri
  gui.ui ile eşleşmiyordu (`generateBtn` bir üretimden sonra "Şematik Viewer
  üret" yerine "Şematik Viewer" oluyordu) → birebir eşitlendi ve testle
  bağlandı; renk seçici diyaloğunun başlığı "inter rengi" yerine anlamlı
  metin. **Doğrulama** (offscreen Qt, 22 kontrol + 5 ek): menü/eylem kurulumu,
  katalogda eksik çeviri yok, TR→EN→TR gidiş-dönüşü birebir, kullanıcı verisi
  (proje yolu, spin değeri, seçili renk) korunuyor, menü↔kutucuk senkronu,
  buton+menü ortak kilitleme, `QSettings` kalıcılığı, menü eylemlerinin
  gerçekten slotlarını çağırması. **Kapsam dışı**: üretilen HTML
  görüntüleyiciler ve `viewer.py` log satırları Türkçe kalır.

- **Kütüphane uyarıları GUI log'unda görünmüyordu, ham İngilizce olarak konsola
  düşüyordu (v2.19.3, kullanıcı: "bu uyarıyı MMCUD50A projesi için aldım")**:
  altium_monkey bazı tanılamaları Python `logging` ile veriyor (ör. 2026.8.11'den
  beri `Recovered unmarked UTF-8 in Altium text record (section 'FileHeader',
  record 641, pair 12, field 'Text'); rewrite the file to add a %UTF8% sidecar`).
  Kök logger'da handler olmadığından bunlar `lastResort` ile **konsola** yazılıyor,
  bizim `log()` geri çağrımızdan geçmiyordu → GUI log'unda yok, pencereli exe'de
  tamamen kayıp; kullanıcı konsolda görüp anlamlandıramıyordu. Yeni
  `_LibraryLogCapture` + `_with_library_logs` dekoratörü (dokuz public üretim
  fonksiyonuna uygulandı) üretim boyunca `altium_monkey` logger'ına bağlanır,
  mesajları ŞABLONA göre sayar ve blok sonunda tek satırlık Türkçe özet yazar:
  `· İşaretsiz UTF-8 metin kurtarıldı (112 kayıt) — … Veri kaybı yok; uyarıyı
  kaldırmak için o sayfaları Altium'da açıp kaydetmek yeterli.` `propagate`
  kapatıldığı için konsola ikinci kez basılmaz; iç içe çağrılarda (birleşik
  görünüm → `_collect_data`) yalnız EN DIŞTAKİ blok özet yazar (`_LIB_LOG_DEPTH`).
  **MMCUD50A teşhisi**: 70 SchDoc'un 70'i açıldı, **0 hata**; 6 dosyada 128 kayıt
  (proje kapsamında 112) bu metni taşıyor ve içerik CLAUDE.md'de v2.15.1'de
  kayıtlı olanın AYNISI: `－55℃＋125℃` (datasheet'ten yapıştırılmış tam genişlikli
  eksi/artı + ℃ karakterleri, komponentin çalışma sıcaklığı parametresi). Yani
  uyarı bir HATA değil, kurtarma bildirimi — 2026.8.1'de bu kayıtlar sayfayı
  komple düşürüyordu. Regresyon: BRK-210/Smart_MCU JSON çıktısı bit bit aynı.

- **Projede birden çok PcbDoc varsa YANLIŞ board seçiliyordu — cross-probe,
  netlist doğrulaması ve Pick&Place sessizce boş kalıyordu (v2.19.2, kullanıcı
  üretim log'u: "PCB'de komponent bulunamadı (parse boş)")**: BRK-209'un PrjPcb'si
  İKİ PcbDoc referanslıyor — `BRK-218` (2.3 MB, **0 komponent / 0 pad / 12 iz**,
  gabari-montaj dokümanı) ve `BRK-213` (34.7 MB, **947 komponent / 3308 pad /
  21868 iz**, gerçek board). Kodda ÜÇ FARKLI seçim kuralı vardı: cross-probe
  (`collect_pcb_placement`) ve netlist doğrulaması (`_merge_netlist_with_pcb`)
  "adında 'panel' geçmeyen İLK dosya"yı alıyordu → BRK-218'i seçip boş dönüyor;
  görüntüleyiciler (`generate_pcb_viewer` / geometri / birleşik) "komponenti olan
  ilk dosya"yı arayıp doğru board'u buluyordu. Sonuç: aynı üretimde PCB paneli
  doğru board'u çizerken cross-probe ve netlist yanlış dosyaya bakıyor, log
  "komponent bulunamadı" + "net'e bağlı pad yok" diyordu (ad "panel" içermediği
  için eski sezgisel kural devreye girmiyordu). **Çözüm**: tek yerde
  `_pick_pcbdoc(project_path, log)` — adayları (komponent, pad) sayısına göre
  puanlar, en yükseği kazanır; hiçbirinde komponent yoksa eski "panel olmayan
  ilk dosya" davranışına döner; seçim proje başına BİR kez yapılıp loglanır
  (`2 PcbDoc adayından **BRK-213…** seçildi (BRK-218…: 0 komponent; BRK-213…:
  947 komponent)`). Beş çağrı noktası da buna bağlandı. Yanına `_load_pcbdoc()`
  parse önbelleği kondu: aynı dosya süreç boyunca bir kez okunur (34.7 MB'lık
  board önceden cross-probe/netlist/geometri/3D için ayrı ayrı açılıyordu),
  kaybeden adaylar bellekten düşülür.
  **İkinci kök neden — Pick&Place 0 yerleşim**: `AltiumDesign.to_pnp()` seçici
  parametresi ALMIYOR; içeride hep `load_pcbdoc(selector=None)` çağırıp aday
  listesinin ilkini alıyor ("Multiple PcbDoc files found, using first: BRK-218"
  uyarısı kütüphaneden geliyordu) → PnP boş dönüyordu. Artık `AltiumDesign`
  yüklenir yüklenmez `design.load_pcbdoc` bizim SEÇTİĞİMİZ (ve zaten parse
  edilmiş) board'u döndürecek şekilde bağlanıyor → hem doğru sonuç hem 34 MB'lık
  dosyanın ikinci kez parse edilmemesi.
  **Sonuç (BRK-209, gerçek proje)**: cross-probe boş → **947 komponent**;
  netlist "PCB'de pad yok" → **906 PCB neti / 3164 pad eşleşti, 78 otomatik ad
  şematik adıyla değiştirildi**; net cross-probe eşleşmesi 0 → **471 net**;
  Pick&Place 0 → **947 yerleşim** (`has_pnp` false → true).
  **Regresyon**: tek PcbDoc'lu projelerde (BRK-210, Smart_MCU) JSON çıktısı
  bit bit AYNI.
  **Not — 3D'deki iki konsol mesajı**: `RWGltf_CafWriter skipped node
  'RAQ0012C_PIN1_AREA' without geometry data` ve `ERR StepReaderData :
  Unresolved Reference` cascadio'nun (OpenCASCADE) C katmanından gelir, Python
  logging'i değildir (bu yüzden GUI log'una düşmez). İlki STEP modelindeki
  geometrisiz işaret düğümü (pin-1 alanı) atlandı demektir, ikincisi bir STEP
  dosyasındaki çözülemeyen iç referanstır — ikisi de kurtarılabilir: BRK-209'da
  **935 gövdenin tamamı STEP mesh'i aldı (0 extrude yedeği)**, yani veri kaybı
  yok.

- **altium_monkey 2026.8.1 → 2026.8.11.post1 yükseltmesi (v2.19.1, ölçümle
  doğrulanmış)**: Üç sürüm geriden geliyorduk; yükseltme öncesi eski/yeni
  kütüphane yan yana çalıştırılıp fark ölçüldü.
  **Bizim için kazanç**: (1) 2026.8.11 `%UTF8%` önekisiz UTF-8 metni artık
  KÜTÜPHANE kurtarıyor (`decode_byte_array(b'Text=－55℃＋125℃')` eskiden
  `ValueError: Failed to decode cp1252`, şimdi metni aynen döndürüp
  `log.warning` ile "sidecar ekleyin" diyor) → v2.15.1'deki
  `patch_altium_text_decoding()` yamamız artık **emniyet ağı**; kaldırılmadı
  (eski kütüphaneyle de çalışılabilsin ve kütüphanenin kurtaramadığı bayt
  dizileri için son çare kalsın diye). Yama `patched(byte_array, *args,
  **kwargs)` imzalı olduğundan yeni `context=` parametresini sorunsuz geçirir.
  (2) 2026.8.11.post1 anotasyonsuz/aynı designator'lı komponent kimliğini
  düzeltti → BRK-210'da IC12 (BGA) **L8/M9/M10/N10 pinleri** artık PA7/PA5/PA4/
  PA6 adlarıyla ve MCU_SPI1_MOSI/SCLK/CS/MISO netleriyle geliyor (eskiden
  netlist'te HİÇ yoktu, yalnız PCB birleştirmesi kurtarıyordu); auto-named net
  78 → 74. (3) 2026.8.10 `compiled.physical_page_metadata` API'sini getirdi
  (fiziksel sayfa/kanal kimliği — bkz. "Yapılmadı" notu).
  **Regresyon kanıtı**: kullandığımız API yüzeyi birebir aynı (9 modül/sınıf,
  `compile_netlist` imzası, `NetlistOptions` alanları, PCB primitive kanalları;
  `__all__`'a 2 sembol eklendi, hiçbiri kaldırılmadı) · `altium_pcbdoc.py` ve
  `altium_text_to_polygon.py` HİÇ değişmemiş (PCB/geometri/3D yolu risksiz) ·
  8 sayfanın şematik SVG'si element element aynı · JSON çıktısı Smart_MCU'da
  bit bit aynı, BRK-210'da tek fark yukarıdaki 4 pin iyileşmesi · PCB geometri
  (19025 iz/1153 pad/557 via/18 katman) ve birleşik 3D (49 STEP modeli, 274
  yerleşim, 192 delik) üretimi sorunsuz.
  **Yan etkiler**: `compiled.compile()` 1.8 s → 4.5 s (toplam üretim ~50 s
  içinde önemsiz) · yükseltme **pillow'u 11.2.1 → 12.3.0'a zorlar**. Pillow
  yükseltmesi tek bir sayfada SVG'yi 12 bayt büyüttü — sebebi izlendi: şemaya
  GÖMÜLÜ PNG logo pillow 12'de 10 bayt farklı sıkıştırılıyor; **piksel içeriği
  birebir aynı** (RGBA 699×406, aynı piksel MD5), vektör/metin koordinatları
  değişmedi. **exe yeniden paketlenmeli** (pillow + altium_monkey ikilileri).
  **Ölçüm tuzağı (not)**: `to_physical_svg()` ilk çağrıda ~27 s, sonrakiler
  ~0.4 s sürüyor; bu bir SÜRÜM farkı DEĞİL, disk üstünde kalıcı font önbelleği
  — sırayı ters çevirince maliyeti hangi sürüm önce çalışırsa o ödüyor.
  **Yapılmadı (aday iş)**: `design.to_netlist()` (konsolide netlist: 251 net,
  1049 pin, **kanal-sonekli fiziksel designator'lar**, net başına `aliases` /
  `auto_named` / `hierarchy_paths`) bizim `compile_project_netlist` +
  `_merge_netlist_with_pcb` ikilisinin yerini alıp netlist için PcbDoc
  yüklemesini gereksiz kılabilir; `to_physical_svg(page_occurrence_ref)` +
  `physical_page_metadata` ile tekrar (Repeat) sayfaları her kanal için AYRI
  sayfa olarak fiziksel designator'larla çizilebilir (BRK-210: 8 mantıksal
  SchDoc → **10 fiziksel sayfa**, diffI2C 3 kanal) — v2.9.33'teki arama
  numarası ve v2.18.1'deki kanal takma-adı köprüsü bu eksiğin yamalarıydı.
  Ayrıca `to_layer_svgs(project_parameters=…)` / `substitute_pcb_special_strings()`
  PCB silkscreen'indeki `.PCBCODE` gibi özel stringleri gerçek değeriyle
  basar (BRK-210'da 50 proje parametresi çözülüyor, bu kartta yerine konacak
  metin yok; BRK-213'te var).

- **Sürüm karşılaştırması PyPI son eklerinde patlıyordu (v2.19.1)**:
  `_check_altium_monkey_version()` içindeki `int(x) for x in v.split(".")`
  `2026.8.11.post1` (ve `2026.7.26b1`) için ValueError verip `(0,)`'a düşüyordu
  → GÜNCEL kütüphanede bile her üretimde "eski sürüm, güncelleme önerilir"
  uyarısı basılıyordu. Artık `deps.parse_version()` kullanılıyor (regex ile
  yalnız baştaki sayısal kısım; ayrıştırılamazsa karşılaştırma atlanır).

- **Şematikte bazı net etiketleri tıklanamıyordu — üstlerinde Altium "Blanket"i
  var (v2.18.2, kullanıcı bildirimi: RS485AB_P aramada bulunuyor ama şemada
  seçilemiyor)**: Diferansiyel çift / net-class direktifleri Altium'da bir
  **Blanket** ile sarılır; bu, SVG'ye yarı saydam beyaz poligon olarak
  (`fill=#FFFFFF fill-opacity=0.49`) ve etiket yazısından SONRA çizilir → yazı
  görünür ama `elementFromPoint` poligonu döndürür, tıklama ona gider. Teşhis:
  yazının sınıfı/`data-net`'i DOĞRUydu ve olayı doğrudan `<text>`e göndermek
  seçimi yapıyordu; kaçıran tek şey hit-test'ti. Çözüm: şematikte etkileşimli
  olan tek şey yazıdır → `.sheet-body svg * {{pointer-events:none}}` +
  `.sheet-body svg text, .sheet-body svg text * {{pointer-events:auto}}`.
  Pan/boş-alan davranışı değişmez (mousedown hedefi artık `<svg>`'nin kendisi
  olur, mevcut kontroller aynı çalışır); metin seçme/kopyalama korunur.
  Doğrulama (CDP): blanket altındaki etiket hit-test'te en üstte, koordinattan
  tıklama net'i seçiyor; normal net / designator / boş-alan / metin seçme
  regresyonsuz (6/6).

- **Net cross-probe'u BAZI netlerde çalışmıyordu — İKİ ayrı ad uyuşmazlığı
  (v2.18.1, kullanıcı bildirimi: "ADC3_CS'i göstermiyor")**:
  (1) **Otomatik PCB adları**: şematik net listesi sayfadaki etiket/port
  adlarından kurulur (ADC3_CS); PCB ise aynı bakırı kendi otomatik adıyla tanır
  (BRK-213: 367 netin **253'ü** `NetU9_15` gibi). Ad eşleşmediği için PCB tarafı
  "bulunamadı" diyordu.
  (2) **Overbar (üst çizgi) gösterimi**: aktif-düşük sinyallerin ham adı
  `ADC3_C\S\` biçimindedir; `get_obj_text()` bunu şematik listesi için
  "ADC3_CS"e normalize ediyor ama netlist/PCB tarafında ham hali duruyordu →
  aday adların HİÇBİRİ tutmuyordu. Ölçüm: BRK-209'un 68 port adından 10'u
  (ADC1_CS, ADC3_CS, ADC_IRQ, PEX_INT, PEX_RST…) yalnız bu yüzden eşleşmiyordu
  — hepsi CS/IRQ/INT/RST, yani hepsi üst çizgili. `ADC3_C\S\` → PCB'de
  `NetR61_1`. Çözüm: takma ad ANAHTARLARI overbar işaretleri atılmış halde
  kurulur (değerler ham PCB adı kalır, PCB kendi adıyla arar) ve netlist artık
  her nete `labels` (net_label + port + sheet_entry + power_port endpoint
  adları, normalize) ekler → yeniden adlandırma yapılmamış netler de eşleşir.
  (3) **Kanal taban adı**: tekrar (Repeat) sayfası şematikte BİR kez çizildiği
  için etiket taban adıyla görünür (VSS_ADC) ama derlenen/PCB adı kanal sonekli
  olur (VSS_ADC_1..5). Taban ad kendisi bir PCB neti DEĞİLSE taban da anahtar
  yapılır → tıklayınca tüm kanallar birlikte vurgulanır.
  **Sonuç (BRK-209)**: eşleşen net 39 → 118; şematikteki 137 netin **135'i**
  PCB'de bulunuyor (kalan 2'si 'Analog PORT'/'Digital PORT' — bakırı olmayan
  harness portları). Ortak çözüm **takma ad köprüsü**:
  `_merge_netlist_with_pcb` her nete `pcb_name` (yeniden adlandırmadan ÖNCEki
  PCB adı) + `sch_labels` (o bakırı işaret eden tüm şematik etiketleri) ekler;
  `_collect_data` bunlardan `etiket → [PCB net adları]` haritası kurup
  `net_list[i]["pcb"]` olarak gömer. Şematik `xprobe-net` mesajına `pcbNet`
  dizisini de koyar, PCB tarafı önce görünen adı sonra PCB adlarını dener; ters
  yönde şematik gelen PCB adını takma ad listesinde arar. **Liste (tek ad değil)
  olmasının sebebi**: kanal-tekrarlı tasarımda bir etiket birden çok PCB netine
  denk gelebilir → `highlightNet` artık ad DİZİSİ kabul eder, canvas sürümünde
  `selNets` + Set tabanlı filtre (`drawLayer(li, netSet)`) ile hepsi birden
  vurgulanır.

- **Net seçimi panellere yayılmıyordu (v2.18.0, kullanıcı isteği)**: Cross-probe
  yalnız KOMPONENT taşıyordu; şematikte bir net seçilince PCB'de hiçbir şey
  olmuyordu. Yeni `xprobe-net` mesajı (`{source, net}`) şematik ↔ PCB arasında
  çift yönlü çalışır: şematikte net adına/liste satırına tıkla → PCB'de net tüm
  katmanlarda vurgulanır + Netler panelindeki satır işaretlenir; PCB'de ize çift
  tık veya Netler panelinden seçim → şematikte net yayları çizilir. Her iki PCB
  görüntüleyici (SVG + geometri/canvas) destekler; 3D'ye iletilmez (net verisi
  yok). **Üç ayrıntı**: (1) ping-pong'u `xpApplying` bayrağı keser — gelen mesajı
  uygularken `crossProbeOut`/`crossProbeNet` no-op olur, yoksa iki panel
  birbirini sonsuz tetiklerdi; (2) yayın `highlightNet`/`clearNetHighlight`
  İÇİNDE değil KULLANICI giriş noktalarında yapılır (highlightNet zaten
  clearNetHighlight çağırıyor → önce null sonra ad yayılır, karşı panelde
  komponent seçimi de silinirdi); (3) `netMark` panel henüz açılmadıysa listeyi
  bir kez render eder (tembel render yüzünden satır bulunamıyordu). Kabukta
  `lastNet` saklanır, PCB tembel yüklenince `repostSel` ile iletilir.
  Doğrulama (CDP, iki mod): SVG 8/8, geometri 7/7 PASS; komponent cross-probe
  ve 3D testleri regresyonsuz (12/12, 8/8).
  **Test notu**: CDP'de `element.dataset` boş obje olarak serileşir — doğrudan
  `dataset.net` (string) okunmalı, yoksa test yanlış FAIL verir.

- **3D: model geometrisi yerleşim başına yeniden kuruluyordu (v2.17.0, ölçüme
  dayalı optimizasyon — "A seçeneği")**: `buildModels` HER yerleşim için ayrı
  `BufferGeometry` kurup `computeVertexNormals()` çalıştırıyor ve GPU'ya ayrı
  yüklüyordu. Aynı kütüphane modeli board'da onlarca kez geçtiğinden (BRK-213:
  60 model → 695 yerleşim) aynı üçgenler **4.7 kez** taşınıyordu. Yeni
  `partGeometry(modelId, parçaIdx, pt)` önbelleği geometriyi (model, parça)
  başına BİR kez kurar; three.js aynı geometriyi birden çok Mesh'te paylaşır
  (dönüşüm mesh'in kendi matrisinde). **Materyal bilerek paylaşılmadı**: seçim
  karartması (`dimReg` → `userData.dDesig`) materyal üzerinden çalışıyor,
  paylaşılsaydı bir direnç seçilince aynı modeli kullanan 167 kopya birlikte
  yanardı. **Ölçüm (BRK-213, headless Edge + CDP)**: GPU geometrisi
  **2586 → 279**, JS yığını 91.7 → 72.2 MB, sayfa yükleme→sahne hazır
  **1.12 → 0.76 s** (3 yenilemenin medyanı), hover raycast 2.65 → 0.65 ms,
  `setSel` 3.6 → 1.0 ms. **Regresyon kanıtı**: mesh (2581), materyal (2586),
  draw call (2586) ve rasterize edilen üçgen (985 549) DEĞİŞMEDİ; 40 komponentin
  dünya bbox merkezi (3 hane) birebir aynı; aynı kameradan alınan ekran
  görüntüsü **bayt bayt özdeş** (MD5 eşit); seçimde yalnız R101_4'ün 4 mesh'i
  parlıyor, aynı modeli paylaşan 166 kopya etkilenmiyor.
  **Yapılmadı (bilinçli)**: draw call sayısı değişmez — onun için instancing
  gerekir (2580 Mesh → 273 InstancedMesh, ölçülen kare kazancı ~3.1×) ama
  InstancedMesh'te örnek başına emissive olmadığından seçim vurgusunun
  `setColorAt`/overlay ile yeniden yazılması gerekir; ayrı iş olarak duruyor.
  Ölçüm dosyaları: `scratchpad/an3d_*.py`, `test_sharedgeo.py`.

- **3D: silkscreen logosu yok + zoom hep merkeze (v2.16.2, kullanıcı bildirimi)**:
  (1) **Logo**: hızlı moddaki 3D doku üreticisi (`_build_surface_from_geometry`)
  silkscreen'den yalnız iz/yay/yazı çiziyor, **REGION'ları** yalnız bakır katman
  için alıyordu. Logo/amblem gibi vektör grafikler silkscreen REGION'u olarak
  saklanır (BRK-213'te "BARKO ELEKTRONİK" = 68 region) → 2D'de görünüp 3D'de
  kayboluyordu. Silk region'ları da (delikleriyle, evenodd) çizilir; doğrulama:
  68/68 region dokuda, üstten görünüm ekran görüntüsünde logo okunuyor.
  (2) **Zoom**: 3D tekerleği yalnız `orbit.r`'yi ölçekliyordu → hep ekran
  merkezine yaklaşıyordu (2D PCB imlece yaklaşırken). Yeni `zoomAt(mult,cx,cy)`:
  imlecin altındaki nokta P (ışının board düzlemi z=0 ile kesişimi) etrafında
  hem kamerayı hem orbit hedefini `f` ile ölçekler → bakış yönü ve mesafe oranı
  korunur, **P ekranda tam yerinde kalır** (perspektif kamerada matematiksel
  olarak kesin: P−kamera vektörü yalnız ölçeklenir). Mesh raycast'i YOK (board
  düz; yüzlerce mesh'te tekerlek başına raycast pahalı). Kenardan (teğet) bakışta
  kesişim çok uzağa düşerse (>4r) veya kesişim yoksa eski merkez-zoom'a düşülür.
  Aynı fonksiyon pinch'te de kullanılır (parmakların ortası). Doğrulama (CDP):
  üç farklı ekran noktasında P'nin NDC kayması 0.00000, mesafe tam yarıya iner;
  ekran merkezinden zoom'da hedef sabit (8/8 PASS).

- **Geometri viewer: TERS (inverted) yazılar dolu beyaz KUTU çiziliyordu
  (v2.16.1, kullanıcı bildirimi: J7_3 yanındaki +OUT / -OUT / OUT3-50A)**:
  `render_pcb_text()` bir glifi `outline` + **`holes`** olarak döndürüyor;
  `extract_pcb_geometry` yalnız `outline`'ı alıyordu. İki etkisi vardı:
  (1) Normal TrueType yazıda 'O','a','8' gibi harflerin iç boşluğu dolu
  çiziliyordu (fark edilmesi zor), (2) **ters yazıda TÜM METİN kayboluyordu** —
  Altium ters yazıyı "dolu dikdörtgen + harf biçimli DELİKLER" olarak
  modelliyor (`is_inverted=True, use_inverted_rectangle=True`; '+OUT' için
  5 noktalı kutu + 4 delik + 'O'nun ortasındaki ada ayrı kontur), delikler
  atlanınca geriye düz beyaz kutu kalıyordu. Çözüm: `[g.outline] + g.holes`
  konturlarının tümü aynı yola eklenir; canvas'ta `fill('evenodd')`, 3D doku
  SVG'sinde `fill-rule="evenodd"` deliği oyar, deliğin İÇİNDEKİ adayı yeniden
  doldurur (kontur sırası önemsiz — evenodd sarım yönüne bakmaz). Aynı
  düzeltme hızlı moddaki 3D board dokusuna da yansır (aynı `geo["texts"]`).
  Ek olarak 3D doku SVG'sinde bakır pour'ları da artık `r[3]` delikleriyle
  (anti-pad) evenodd çiziliyor. **Doğrulama** (BRK-213, headless Edge + CDP
  ekran görüntüsü): +OUT/-OUT/OUT3-50A ve .PCBCODE artık beyaz kutudan oyulmuş
  harfler olarak okunuyor (Altium/KiCad ile aynı). Yazı YÖNÜ zaten doğruydu:
  board'un üst kenarındaki kopyalar tasarımda gerçekten `rotation=180`, alt
  kenardakiler `rotation=0` (KiCad'deki görünümle birebir).

- **Cross-probe seçimi "yapışıyordu" + Parçalar toggle'ı kendiliğinden geri
  açılıyordu + board'u kaplayan mavi blok (v2.16.0, kullanıcı bildirimi)**:
  Üç ayrı şikâyet, üç ayrı kök neden.
  (1) **Bayat seçim**: şematikte boş alana tıklayıp seçimi bırakınca hiçbir yere
  haber verilmiyordu (`crossProbeOut` yalnız SEÇİMDE çağrılıyordu) → kabuktaki
  `lastSel` eski designator'da kalıyor, 3D/PCB'ye geçince `repostSel`/`setViewMode`
  onu geri gösteriyordu. Artık **seçim temizleme de bir mesaj**: designator'ı
  boş `xprobe` = "bırak". Yayan yerler: şematik boş-alan tıklaması +
  `clearSelection()` (Esc / Temizle), SVG PCB boş-alan tıklaması + Esc, canvas
  PCB boş-alan tıklaması + Esc, 3D boşluğa tıklama. Alan yerler: üç viewer'ın
  `message` handler'ı (kutu/popup/vurgu temizlenir), kabukta `lastSel = null`.
  (2) **Parçalar toggle'ı**: 3D'nin handler'ı GELEN HER mesajda `compBtn.onclick()`
  ile parçaları geri açıyordu; mod değiştikçe kabuk aynı seçimi tazelediği için
  kullanıcının kapattığı parçalar her sekme dönüşünde geri geliyordu. Artık
  gelen designator **son gelenle** (`lastXpSel`) karşılaştırılır; aynıysa hiçbir
  şey yapılmaz. Karşılaştırma `selectedDesig`'e DEĞİL `lastXpSel`'e bakar —
  çünkü parçaları gizlemek yerel olarak `setSel(null)` yapıyor, bu da tekrar
  mesajını "yeni seçim" gibi gösterirdi. Parçaları gizlemek artık diğer
  panellere seçim-bırak YAYMAZ (yerel görünüm tercihi).
  (3) **Board'u kaplayan açık mavi dikdörtgen**: PcbDoc'ta MECHANICAL1 üzerinde,
  komponente bağlı OLMAYAN (`component_index=65535`) iki serbest 3D gövde —
  202.7×85.1 mm, 20 mm + 22 mm yükseklik, `body_color_3d=16776960` (BGR → #00ffff),
  **`body_opacity_3d = 0.0`**. Altium bunları TAM SAYDAM çizer (muhafaza/gabari
  hacmi); biz opaklık alanını hiç okumadığımız için dolu blok olarak çiziyorduk.
  `_extract_3d` artık opaklığı okur: alan **azınlıkta** saydam ise (≤%25 — bazı
  dosyalarda alan hiç doldurulmamış olabilir, hepsi 0 ise ölçüt yok sayılır)
  opacity ≤0.02 gövdeler ÇİZİLMEZ (log'a sayısı yazılır), 0.02–0.98 arası
  gövdeler yarı saydam materyalle çizilir. BRK-213: 14 gövde atlandı (2 mekanik
  hacim + 12 MECH montaj donanımı), 695 STEP + 1 extrude kaldı; Smart_MCU
  etkilenmedi. Ayrıca "Parçalar" toggle'ı artık `userData.desig` yerine
  `userData.part` bayrağına bakar → designator'sız gövdeler de gizlenir
  (kullanıcı "kapattığım halde duruyor" diyordu).
  **Doğrulama** (headless Edge + CDP, iframe başına execution context):
  seçim/temizleme yayılımı + toggle kalıcılığı 12/12 PASS, PCB↔şematik temizleme
  6/6 PASS; dört şablonun JS'i `node --check` ile hatasız.

- **Gerçek projede İKİ ciddi veri kaybı: 5 sayfa hiç açılmıyor + 67 sayfada
  yalnız 18 komponent (v2.15.1, kullanıcı log'u)**:
  (1) **`ERR …: Failed to decode cp1252 content: byte 0x8d`** — altium_monkey
  `%UTF8%` öneki YOKSA kaydı KATI cp1252 ile çözüyor. Altium, datasheet'ten
  yapıştırılan metni ANSI alanına UTF-8 olarak yazabiliyor: bozuk kayıt
  `Text=` + `ef bc 8d 35 35 e2 84 83 …` yani **`－55℃＋125℃`** (tam genişlikli
  karakterler). cp1252'de 0x8D tanımsız → ValueError → O SAYFA TAMAMEN
  düşüyordu (67 sayfanın 5'i) ve aynı hata `AltiumDesign`i de düşürüp
  BOM/varyant verisini yok ediyordu. Çözüm: `patch_altium_text_decoding()` —
  `decode_byte_array` yamalanır, katı yol patlarsa sırayla (a) UTF-8
  (metin AYNEN kurtulur — doğrulandı: `－55℃＋125℃`), (b) Windows davranışı
  (cp1252'de tanımsız bayt kendi kod noktasına düşer, asla hata vermez).
  Yama `_collect_data` başında uygulanır; `from … import decode_byte_array`
  yapan modüllerde de isim değiştirilir (7 modül), yoksa eski katı sürüm
  çalışmaya devam ederdi.
  (2) **67 sayfa → 18 komponent**: birleştirme anahtarı DESIGNATOR'dı; bu
  tasarım ANOTASYONSUZ (designator'lar `C?`, `R?`, `D?`) olduğundan tüm
  sayfalardaki `C?` tek komponente çöküyordu. Artık yer tutucu designator'da
  (`…?`) kimlik olarak Altium **UniqueId**'si kullanılır (aynı sayfada bile
  benzersiz, ölçüldü: 14 komponent → 14 farklı uid). Anotasyonlu tasarımlarda
  davranış AYNEN korunur (BRK-210: 264 komponent, 1 multi-part — değişmedi),
  çünkü multi-part birleştirme designator'a bağlı kalır.
  **Sonuç** (kullanıcının projesi): 62/67 → **67/67 sayfa**, 18 → **1481
  komponent**, AltiumDesign hatası yok. Komponent listesindeki 1500'lük DOM
  sınırı da artık sessiz değil: "… N komponent daha (aramayla daralt)".
  **Bilinen kısıt**: anotasyonsuz tasarımda şema üzerindeki `C?` yazısına
  tıklamak o sayfadaki İLK `C?`'yi vurgular (SCH_BOXES designator'la
  anahtarlanıyor); listeden seçim doğru komponenti açar.


- **Şematik: etkileşim bitmap'i artık zoom'a göre üretiliyor (mip) — v2.15.0,
  "PCB'deki akıcılığı şematikte de alabilir miyiz?"**: Ölçüm önce yapıldı:
  BRK-210 şematiği **8 sayfa / 22 564 SVG elemanı** (3 086 metin, 14 008 çizim)
  — PCB'nin SVG DOM'undan kat kat hafif, üstelik şematikte v2.9.35'ten beri LOD
  var. Yani PCB'yi kurtaran şey (SVG DOM'unu tamamen bırakmak) burada aynı
  ölçüde gerekli DEĞİL; asıl eksik, etkileşim bitmap'inin SABİT çözünürlükte
  (`LOD_RES` ≈ 1.25-1.6) olmasıydı: yakın zoomda bulanıklaştığı için
  `scale > 4`'te devre dışı kalıyor, takılma orada geri geliyordu.
  **Çözüm**: `lodRender(body, res)` + `lodRetune()` — hareket durduktan 400 ms
  sonra YALNIZ GÖRÜNÜR sayfaların bitmap'i o zoom'a uygun çözünürlükte yeniden
  üretilir (`res = scale × dpr`, sayfa başına `LOD_MAX_PX=2800` uzun kenar
  sınırı → kartta res≈4). `updateLod` artık sabit eşik yerine "bitmap ekran
  çözünürlüğünün ≥ %55'i mi" (`LOD_SHARP`) diye bakar → bitmap ~7× zoom'a kadar
  kullanılır, ötesinde canlı SVG (bulanık göstermek yerine).
  **Kullanım hiç bozulmadı**: duran görünümde HÂLÂ canlı SVG var — metin seçme/
  kopyalama, tıklama, hover aynen çalışır (CDP ile doğrulandı, 12/12).
  Görünmeyen sayfalar taban çözünürlükte kalır (bellek).
  **Şematiği geometri→canvas'a çevirme YAPILMADI** (bilinçli): şematiğin ana
  içeriği metindir ve canvas'ta PDF gibi metin seçme/kopyalama kaybolur; ayrıca
  binlerce yazının poligonu yükü büyütür. Kazanç/kayıp dengesi PCB'dekinin
  tersi.


- **Hızlı (geometri) modda beş kullanıcı hatası (v2.14.0)**:
  (1) **3D board çıplaktı** — izler ve designator yazıları görünmüyordu. Doku
  klasik yolda katman SVG'lerinden türetiliyor, hızlı modda o adım hiç
  çalışmıyor. Yeni `_build_surface_from_geometry()` aynı dokuyu GEOMETRİDEN
  üretir. **Hizalama kritik**: geometri koordinatları board bbox'ının
  sol-üstünden (Y aşağı +), 3D dünya ise bbox MERKEZİNDEN (Y yukarı +) →
  `X_dünya = X_geo − W/2`, `Y_dünya = H/2 − Y_geo`; yani düzlem tam
  `[−W/2,W/2]×[−H/2,H/2]` aralığını kaplar → `surf.cx = surf.cy = 0`,
  viewBox `0 0 W H`. `addSurface`'in delik-delme eşlemesi de aynı formülü
  kullandığından delikler yerli yerinde kalır. `surf.ok` yalnız bbox board
  outline'ından geldiyse 1 (aksi halde delme kapalı — kayık dokuda hilal
  artefaktı olurdu).
  (2) Canvas görüntüleyicide **Üst/Alt · Hepsi · Temizle** butonları yoktu →
  eklendi (`T` kısayolu; SVG sürümüyle aynı semantik: yalnız "Top …"/"Bottom …"
  adlı katmanlara dokunur).
  (3) **Katmanı en üste getirme (↑)** yoktu → her katman satırına buton;
  `topLayer` en sona çizilir (canvas'ta sonra çizilen üstte), tekrar basınca
  normal sıraya döner.
  (4) **Net filtre çipleri (Tümü/Güç/GND/Sinyal) Katmanlar sekmesinde
  görünüyordu**: `.hidden` kuralı `.panel.hidden` olarak yazılmıştı, `#chips`
  bir `.panel` olmadığı için işlemiyordu. Aynı kök neden BOM panelinin de her
  sekmede görünmesine yol açıyordu (`.panel.nopad` kuralı sonra geldiği için
  eşit özgüllükte gizlemeyi eziyordu) → `.panel.hidden, #chips.hidden
  { display:none !important; }`.
  (5) Şematikte **seçili net etiketi "Sayfa…" açılır menüsünün üstüne
  biniyordu**. Mutlak konumlandırma (ortalı, sonra sola alma) dar pencerede
  kaçınılmaz çakışma üretiyordu → etiket TOOLBAR'IN İÇİNE alındı (flex
  yerleşimi çakışmayı yapısal olarak engeller, toolbar sarınca etiket de
  sarar); boşken `:empty` ile hiç görünmez.


- **Birleşik görünüm hâlâ eski (SVG) PCB'yi üretiyordu (v2.13.0, kullanıcı
  sorusu)**: v2.12.0'da geometri görüntüleyici ayrı bir butona bağlanmıştı ama
  `generate_combined_viewer` içindeki PCB paneli `collect_pcb_layers()` +
  `build_pcb_html()` yolunda kalmıştı — yani "Şematik + PCB + 3D" düğmesi
  hızlı yoldan yararlanmıyordu. Artık `fast_pcb` bayrağı var (GUI'de onay
  kutusu, varsayılan AÇIK). Hızlı yolda PCB
  dosyası bir kez açılır, `extract_pcb_geometry` + `build_pcb_canvas_html`
  kullanılır ve 3D verisi `_extract_3d()` ile DOĞRUDAN alınır; `to_layer_svgs`
  hiç çağrılmadığı için **3D yüzey dokusu üretilemez** (doku o SVG'lerden
  türetiliyor) — bu bilinçli takas, log'a ve kutucuğun ipucuna yazılı.
  Doğrulama (CDP): PCB panelinin geometri sürümü olduğu, BOM panelinin
  dolduğu, şematik→PCB ve PCB→şematik cross-probe'un çalıştığı, 3D panelinin
  yüklendiği ve dokunun beklendiği gibi bulunmadığı — 9/9 PASS.


- **Geometri (canvas) PCB görüntüleyici — metinler görünmüyordu: ÜÇ ayrı kök
  neden (v2.12.0)**: `extract_pcb_geometry` + canvas renderer ilk sürümünde
  silkscreen yazıları hiç çıkmıyordu. (1) `render_pcb_text()` iki FARKLI sonuç
  döndürüyor: TrueType için `characters` (glif poligonları), Altium'un
  varsayılan **stroke** fontu için `lines` (çizgi parçaları). Yalnız
  `characters` işlenince BRK-210'un 966 metninin 660'ı sessizce düşüyordu →
  ikisi de işlenip ayrı kanalda (`texts` / `stexts`) gömülür, canvas'ta biri
  dolgu diğeri kalemle çizilir. (2) **Birim tuzağı**: `render_pcb_text` çıktısı
  MİLİMETRE (kayıt `x_mils=2962.6` → ilk segment `75.2499` mm ile birebir
  doğrulandı); mil sanılıp mil→mm dönüşümünden geçirilince yazılar board'un
  ~25 katı uzağına düşüyordu (ekranda hiç görünmüyor) → metinler için ayrı
  `XM/YM` dönüşümü. (3) **Görünürlük**: Altium `comment_on`/`NameOn` kapalı
  yazıları basmaz; filtre olmadan silkscreen gizli değer/açıklama yazılarıyla
  doluyordu. DİKKAT: designator görünürlüğü **`name_on`** alanıdır —
  `designator_on` bu dosyalarda HER komponentte False (legacy alan); ona
  bakılırsa tüm designator'lar kaybolur.

- **PCB'de board döndürme/ayna (v2.12.0)**: Ekran↔kök dönüşümü tek noktaya
  alındı (`rootToScreen`/`screenToRoot`/`centerOnRoot`) ve dönüşüm
  `t + s·R(rot)·diag(mir,1)` olarak tanımlandı. Döndürme **90°'nin katlarıyla
  sınırlı** olduğundan `getBoundingClientRect` ekran AABB'si kök uzayda YİNE
  AABB kalır → mevcut kutu matematiği (komponent vurgusu, pad etiketi, ölçüm)
  değişmeden doğru çalışır (CDP: 6 yönelimde gidiş-dönüş hatası 9e-15, pad
  merkezi yönelimden bağımsız 0.0000 mm). Overlay YAZILARI ters/aynalı
  okunmasın diye `.upright` sınıfıyla kendi çapaları etrafında geri döndürülür;
  doğrulama Chromium'da `getScreenCTM` CSS transform'u İÇERMEDİĞİ için
  bileşik matris (CSS × element) hesaplanarak yapılır.


- **PCB çıktısı 65 MB'a çıkıyordu — katman SVG'leri ham gömülüydü (v2.11.0)**:
  `to_layer_svgs()` çıktısı HTML'e olduğu gibi yazıldığından BRK-210 için
  **65.1 MB** dosya üretiliyordu (yavaş açılış, yüksek bellek; birleşik görünüm
  bundan etkilenmiyordu çünkü iç HTML'i zaten gzip'liyor). Katman içerikleri
  tek gzip+base64 blob'una alındı → **8.0 MB**. Yerleşim değişmedi: her katman
  için boş `<g>` placeholder korunur, çözülünce içerik enjekte edilir.
  Doğrulama (CDP): varsayılan açık katmanlar dolu, kapalı katman hâlâ tembel,
  `ensureLayerLoaded` ile açılınca yükleniyor; net highlight / BOM grup vurgusu
  / pad etiketleri regresyonsuz.
  **Ölçüm notu — mimari alternatif**: aynı board'un HAM GEOMETRİSİ
  (19 025 iz + 963 region + 1 153 pad + 557 via + 207 arc + 966 metin)
  kompakt JSON'da **1.2 MB, gzip 250 KB**. Yani SVG yerine geometriyi gömüp
  `<canvas>`'a çizen bir renderer (KiCad InteractiveHtmlBom yaklaşımı) dosyayı
  ~30× daha küçültebilir ve LOD hilelerine gerek bırakmaz. altium_monkey
  primitive erişimi buna hazır (`pcb.tracks/arcs/pads/vias/regions/texts`);
  zor kısım pad şekilleri, pour delikleri ve METİN (Altium stroke font →
  `altium_text_to_polygon`). Yapılmadı — ayrı, büyük iş olarak duruyor.

- **Mobil tarayıcıda (Android Firefox) parmakla yakınlaştırma ve benzeri
  hiçbir etkileşim çalışmıyordu (v2.10.0, kullanıcı bildirimi)**: Dört
  görüntüleyicinin de pan/zoom kodu YALNIZCA `mousedown`/`mousemove`/`wheel`
  ile yazılmıştı; faresi olmayan cihazda hiçbiri tetiklenmiyordu (şematikte
  kaydırma/zoom, PCB'de aynısı, 3D'de döndürme, birleşik kabukta ayraç).
  Üstüne `<meta name="viewport">` de yoktu → mobil tarayıcı 980px'lik sanal
  düzen genişliği varsayıp arayüzü minicik gösteriyor, `100vh` yerleşimi
  taşıyordu. **Çözüm**: ortak `_GESTURE_JS` (`installGesture`: pointer
  olaylarıyla tek parmak pan + iki parmak pinch; `installDrag`: pointer
  capture'lı basit sürükleme) + `_MOBILE_META` dört şablona da enjekte edildi;
  masaüstü fare kod yolu OLDUĞU GİBİ korundu. **Üç kritik ayrıntı, CDP
  dokunma emülasyonuyla ölçülerek bulundu**: (1) Jest yüzeyine
  `touch-action:none` verilmezse tarayıcı jesti kendi alır, `pointermove`
  akışı hiç başlamaz. (2) `pointerdown`da `preventDefault()` compat fare
  olaylarını bastırıyor AMA Chromium'da dokunuş sonundaki `click`i de
  bastırıyor → ilk denemede parmakla net/komponent seçmek İMKÂNSIZ oldu
  (teşhis: olay günlüğünde `click` hiç yoktu); preventDefault yalnız
  `pointermove`a alındı, compat olaylara karşı mevcut `mousedown`
  handler'larına `gTouchActive()` koruması eklendi (çift pan yok — ölçüm:
  100px sürüklemede tx tam 100). (3) Not/kutu araçları mouse tabanlı
  olduğundan jest "köprü" (bridge) modunda sentetik fare olayları üretir →
  annotation kodu değişmeden mobilde de çalışır. Mobil düzen: `@media
  (max-width:820px)` ile sol paneller kayan katman (dar ekranda varsayılan
  kapalı), toolbar sarma, `100dvh`. **Doğrulama** (headless Edge + CDP,
  390×844 `mobile:true` + `setTouchEmulationEnabled`): şematik 9/9, PCB 7/7,
  birleşik (mod düğmeleri + iframe içi pan/pinch + 3D döndürme/pinch + ayraç
  sürükleme) 11/11 PASS. **Test notu**: iç viewer'ların `let`/`const`
  değişkenleri `iframe.contentWindow` üstünde GÖRÜNMEZ (global lexical scope)
  → CDP'de `Runtime.executionContextCreated` ile o frame'in context id'si
  alınıp orada değerlendirme yapılmalı (ilk test yanlış yere yazıp "pan
  çalışmıyor" sanmıştı). Ayrıca fit ölçeği < 0.85 iken şematikte LOD bitmap
  SVG'yi örttüğünden dokunmayla eleman seçmek için önce yakınlaşmak gerekir
  (tasarım gereği; o zoom'da yazı zaten okunmaz).

- **PCB: BOM · Montaj paneli — iBOM tarzı grup seçimi + checklist (v2.10.0,
  kullanıcı isteği)**: Kullanıcı InteractiveHtmlBom tabanlı bir viewer'ın
  board görünümü/seçimini örnek gösterdi. Eklenenler: sol panelde
  Katmanlar/BOM sekmeleri, değer+footprint gruplaması, satıra tıkla → grubun
  TÜM komponentlerini aynı anda vurgula, ✓ ile montaj işareti
  (localStorage `schviz-bom:<proje>`) + ilerleme sayacı, Tümü/Üst/Alt/Kalan
  filtreleri, aramanın BOM'u da filtrelemesi, board seçimiyle satırın
  senkronu, tek komponentte pin-1 halkası. Çoklu vurgu için `highlightComp`
  → `highlightComps(desigs)` genelleştirildi (`rootBox`/`compBounds`
  yardımcıları ayrıldı; `updateMarkerMetrics` artık tüm kutu/etiketlerde
  döner). Doğrulama: headless Edge + CDP 16/16 PASS (gruplama toplamı =
  komponent sayısı, çoklu kutu, pin-1, checklist kalıcılığı sayfa
  yenilemesinden sonra da, filtreler, arama).

- **Şematik: çok satırlı metin çerçeveleri (DESIGN NOTE kutuları) görünmüyordu —
  sayfalar arası SVG id çakışması (v2.9.42, kullanıcı bildirimi)**: Kırmızı
  çerçeve çiziliyor ama içindeki metin YOK; pan/zoom sırasında bir an görünüp
  hareket bitince tekrar kayboluyordu. Kök neden: altium_monkey her sayfayı
  BAĞIMSIZ SVG dokümanı sayıp id'leri sayfa yerelinde numaralıyor
  (`ClipRect1..N`); Altium "Text Frame" nesnesinin her satırı `clip-path=
  "url(#ClipRectN)"` ile çerçeveye kırpılıyor. Viewer 8 sayfayı TEK HTML
  dokümanına gömdüğünden aynı id 4-8 kez tanımlanıyor ve tarayıcı referansı
  **dokümandaki İLK** tanıma çözüyor → BRK-210'da 175 clip referansının
  **128'i yanlış sayfanın dikdörtgenine** düşüyor; DS1683 notu (metin y=218)
  sayfa 0'ın `y=443..587` dikdörtgeniyle kırpılıp TAMAMEN görünmez oluyordu.
  **Pan/zoom'da görünmesinin sebebi LOD**: `buildLods` sayfa SVG'sini
  `XMLSerializer` ile TEK BAŞINA serileştirdiğinden bitmap'te id'ler doğru
  (yerel) çözülüyor — bu yüzden metin yalnız hareket anındaki bitmap'te
  görünüyordu (v2.9.35/36 LOD davranışı; LOD'un kendi hatası DEĞİL, çakışmayı
  görünür kılan ipucu). **Çözüm**: yeni `namespace_svg_ids(svg, prefix)` —
  `to_svg()` çıktısında hem TANIMLI hem REFERANSLI id'ler sayfaya özgü
  `s{idx}__` önekiyle benzersizleştirilir (`url(#id)` ve `href="#id"`
  referansları da yazılır; `_collect_data`'da render'dan hemen sonra çağrılır
  → HTML/birleşik görünüm/LOD hepsi aynı SVG'yi kullandığından tek noktadan
  düzelir). Referanssız id'lere (scene, DocumentItemsGroup, TPL00001 …)
  DOKUNULMAZ: hiçbir CSS/JS onlara bakmıyor ve metin içeriğinde geçen
  `id="..."` benzeri dizilerde yanlış eşleşme riski böylece sıfırlanır.
  **Doğrulama** (BRK-210, 8 sayfa): yanlış çözülen referans 128 → **0**,
  175/175 referans tek tanıma çözülüyor; headless Edge + CDP ile canlı SVG'de
  (LOD kapalı, durgun) not metni `elementFromPoint`'te hit alıyor
  (`clipRect=[1171,201,358,78]`, `ayniSvg=true`) ve ekran görüntüsünde
  Altium'la aynı şekilde okunuyor — düzeltmesiz HTML'de aynı noktada
  `polygon` (zemin) çıkıyor, kutu boş. **PCB görüntüleyici etkilenmiyor**:
  katman SVG'lerinde `url(#…)` referansı YOK (0), tekrarlı id'ler
  (`pcb-pad-*-hole`, `scene`, `board-outline`) referanssız → render doğru,
  namespace uygulanmadı.

- **Annotation: Kaydet artık açık dosyanın ÜSTÜNE yazabiliyor (v2.9.41,
  kullanıcı isteği)**: Kaydet her seferinde `_notlu.html` kopyası indiriyordu;
  kullanıcı var olan dosyanın üstüne kaydetmek istedi. Tarayıcı güvenliği
  `file://` sayfanın kendi dosyasına SESSİZCE yazmasına izin vermez — çözüm
  **File System Access API** (Chromium; `window.showSaveFilePicker` bu
  ortamda `file://` altında da mevcut, headless'ta doğrulandı): (1) İlk
  Kaydet'te kayıt diyaloğu açılır, `suggestedName` = açık dosyanın adı
  (`location.pathname`'den; srcdoc iframe'de yok → `{proje}_notlu.html`);
  kullanıcı mevcut dosyayı seçince üstüne yazılır. (2) Dönen handle
  `annoFileHandle`'da oturum boyunca saklanır → sonraki Kaydet'ler DİYALOGSUZ
  aynı dosyaya yazar (`queryPermission`/`requestPermission` 'granted'
  kontrolüyle; hata olursa handle düşürülüp normal akışa dönülür). Başarıda
  buton 1.5s '✓' gösterir. (3) `AbortError` (vazgeçme) hiçbir şey yapmaz;
  BAŞKA hata (örn. `NotAllowedError` — user-activation/iframe kısıtı) ve API
  yokluğu (Firefox) eski indirme fallback'ine düşer. Klon üretimi
  `annoBuildHtml()` fonksiyonuna ayrıldı; onclick async oldu (testlerde
  `await onclick()` gerekir). CDP 5/5: sahte picker ile ilk kayıt (picker 1
  kez + içerik + ad + ✓), ikinci kayıt sessiz (picker sayısı sabit), iptal
  (yazma/indirme yok), API yok → indirme, NotAllowedError → indirme.

- **Annotation: kutusuz not + renk seçici + min yazı 4 (v2.9.40, kullanıcı
  geri bildirimi 2)**: (1) Notun sarı arka plan kutusu KALDIRILDI — çıplak
  yazı (Foxit typewriter görünümü). Tıklama/sürükleme yüzeyi için ölçülen
  bbox boyutunda görünmez hit-rect eklendi: `fill='rgba(0,0,0,0)'` — şeffaf
  ama "painted" olduğundan pointer-events yakalar (`fill:none` YAKALAMAZ,
  bilinen SVG tuzağı). (2) Mini bar'a `<input type=color>` eklendi
  (`annoColorInp`): seçili notun yazı rengini / kutunun kenar rengini canlı
  değiştirir (`a.color`; not varsayılanı #c62828 koyu kırmızı, kutu #ffb300
  amber — eski veri alansızsa varsayılan uygulanır, geriye uyumlu). Bar
  gösterilirken input değeri seçili öğenin renginden set edilir; yerinde
  yazma editörü de notun rengini `style.color` ile gösterir. Editör arka
  planı sarıdan yarı saydam beyaza (`rgba(255,255,255,0.72)` + gri kesik
  kenar) alındı — kutusuz görünümle tutarlı. (3) Yazı boyutu alt sınırı
  8→**4** (adım 2 aynı). CDP testi 7/7: kutusuz render (tek rect=anno-hit),
  hit-rect ile seçim, renk değişimi not+kutu, min fs 4, editör rengi,
  localStorage kalıcılığı. Test betiği notu: `Runtime.evaluate` üst kapsamı
  değerlendirmeler arası KALICI — `const` isimleri çakışır, her testi IIFE
  ile sarmala.

- **Annotation Foxit tarzına revize: yerinde yazma + seçim/taşıma/boyutlandırma
  + Del ile silme (v2.9.39, kullanıcı geri bildirimi)**: v2.9.38'in prompt'lu
  akışı ve kalın kutu kenarı beğenilmedi (Foxit PDF editör referans gösterildi).
  (1) **Typewriter**: not eklerken prompt yerine tıklanan yerde contenteditable
  div (`#anno-editor`, `plaintext-only`; desteklenmezse `true` fallback) —
  canvas İÇİNDE olduğundan zoom/pan ile birlikte ölçeklenir; Enter = yeni
  satır (SVG'de tspan'ler, `white-space:pre` ile birebir), blur/Esc = bitir,
  boş = eklenmez/silinir. Editör keydown'ı `stopPropagation` (Del/B gibi ana
  kısayollar karışmasın); nota çift tık aynı editörü açar. (2) **Seçim
  modeli**: tıkla-seç (`annoSel`) → kesikli mavi çerçeve + kutuda 4 köşe
  tutamacı (ekran-sabit boyut, `__annoUi` `applyT`'den her karede çağrılır —
  `var` ile bildirilir ki modül kurulmadan önceki applyT çağrıları `typeof`
  guard'ından güvenle geçsin, `let` TDZ tuzağı YOK). Sürükle = taşı (3px
  eşik), köşe tutamacı = boyutlandır (min 2), mouseup'ta tek `annoStore`.
  `annoLayer` mousedown'ı `stopPropagation` ile pan'i keser; taşıma sonrası
  click `annoJustDrew` bayrağıyla yutulur. (3) **Del/Backspace** seçiliyken
  siler (aktif eleman input/select/contenteditable ise DEĞİL); Esc önce araç,
  sonra seçim bırakır. "N.Sil" (tümünü sil) butonu kullanıcı isteğiyle
  KALDIRILDI. (4) **Mini bar** (`#anno-bar`, ekran uzayında seçili öğenin
  üstünde, pan/zoom'da izler): −/+ notta yazı boyutu (8–48, adım 2), kutuda
  kenar kalınlığı (0.5–8, adım 0.5); × sil. (5) Kutu kenarı 3→**1.5** ve
  ayarlanabilir (`a.sw`); ince kenar seçilebilsin diye görünmez geniş
  hit-rect (`.anno-hit`, `pointer-events:stroke`, min 6) eklendi — görünür
  rect `pointer-events:none` oldu; tutamaç kuralı `rect.anno-handle` yazılır
  (özgüllük `.anno-box rect` ile eşit, SONRA geldiği için kazanır). Kutu
  çizimi bitince otomatik seçilir. Not yüksekliği artık satır sayısı×fs×1.3
  (+10) — eski tek satır 14px ≈ 28 korunur (v2.9.38 verisiyle uyumlu; fs/sw
  eksikse varsayılan). Kaydet klonu temizliğine `#anno-editor` + `#anno-bar`
  eklendi. Headless Edge + CDP: 13 etkileşim testi (typewriter çok satır,
  yerinde düzenleme, boş=sil, bar ±, mouse-event simülasyonlu taşı/boyutlandır,
  Del/Esc, editörde Del güvenliği, temiz klon) + kayıtlı kopya round-trip
  yeniden PASS.

- **Şematik: not ekleme + kutu içine alma + temizleme + notlu HTML kaydetme
  (v2.9.38, kullanıcı isteği)**: Toolbar'a dört düğme: **Not** (tıklanan yere
  yapışkan sarı not), **Kutu** (sürükleyerek amber çerçeve), **N.Sil** (tümünü
  temizle, confirm'li), **Kaydet** (notlar gömülü HTML kopyası indir). Veri
  KANVAS koordinatında yeni `#anno-layer` SVG'sinde tutulur (arc-layer gibi
  canvas ile transform olur → pan/zoom'da şemayla birlikte hareket eder; LOD
  bitmap modunda da canlı kalır). Araç aktifken `#viewport.anno-mode` →
  crosshair imleç + şema SVG'leri ve mevcut `.anno`'lar pointer-events:none;
  pan mousedown'ı `if (annoTool) return` ile kilitli; boş-alan-tık
  seçim-temizleme `annoTool || annoJustDrew` korumalı (kutu çizimini bitiren
  click'i mouseup'taki setTimeout(0)'lık bayrak yutar — click aynı görevde
  timer'dan ÖNCE dispatch edilir). Esc yalnız araçtan çıkar, seçime dokunmaz
  (keydown'da öncelikli dal). Nota çift tık düzenler (boş = sil), kutu
  KENARINA çift tık siler — kutu içi tıklamayı yutmasın diye rect
  `pointer-events:stroke`. **Kalıcılık iki katmanlı**: (1) her değişiklikte
  localStorage `schviz-anno:<proje>` (`build_html`'e yeni `project_name`
  parametresi, iki çağrı noktası da geçirir; kayıt `ts` damgalı); (2)
  **Kaydet** canlı DOM'u klonlayıp runtime durumunu temizler (lod-bitmap +
  lod-ready, sch-hl-overlay, anno-layer, hit/comp-highlight sınıfları, canvas
  transform/lod sınıfları, arc-layer içeriği, popup/tip/sidebar durumu) ve
  notları baştan beri template'te duran `<script type="application/json"
  id="anno-embed">` slotuna gömüp `{proje}_notlu.html` olarak indirir
  (listeler/LOD kopyada script'lerce yeniden kurulur). Yüklemede localStorage
  ile gömülü veriden `ts`'i YENİ olan kazanır (aynı makinede son düzenleme,
  yeni makinede gömülü veri görünür). **İki kritik gömme detayı**: (a) gömülü
  JSON'da `<` → `\\u003c` kaçışı (not metninde script kapatma etiketi geçse
  bile tag erken kapanmaz; JSON string'inde geçerli escape); (b) inline
  script İÇİNE literal script-kapatma etiketi YAZILAMAZ — ilk denemede bir
  YORUM satırında geçen etiket HTML parser'ı erken kapattı (node --check ile
  yakalandı, yorum yeniden yazıldı). Birleşik görünümdeki şematik iframe'i
  özelliği otomatik taşır (aynı build_html); oradaki Kaydet şematik-tek HTML
  indirir. Headless Edge + CDP doğrulama (18 kontrol): render/store, reload
  sonrası localStorage'dan yükleme, gömülü-veri önceliği, araç aç/Esc kapat,
  kaydedilen kopyanın KENDİSİ açılıp gömülüden notları yüklüyor + LOD
  yeniden kuruluyor + zoom çalışıyor; `</script>`+`<` içeren not metni
  round-trip'te birebir korunuyor (3 script tag'i sabit).

- **Performans: LOD PCB + 3D'ye taşındı, her viewer'a LOD toggle butonu
  (v2.9.37, kullanıcı isteği — GUI checkbox yerine HTML arayüzünde)**:
  (1) **PCB LOD** (`pcbLodBuild` vd.): pan/tekerlek serisi BOYUNCA görünür
  katmanların tek bitmap'i (`#lod-canvas`, uzun kenar 2600px, `k=2600/max(VIEW)`)
  gösterilir; svg'nin ALTINDA durduğundan overlay'ler (net-hl, hl-marker, pad
  etiketleri) üstte canlı kalır; katmanlar `visibility:hidden` (inline `display`
  katman aç/kapa durumunu taşıdığından ona dokunulmaz). Şematikten farklar:
  dinlenmede HEP canlı SVG (PCB'de uzak zoom'da da tıklama yaygın); bitmap
  kendi çözünürlüğünün ~4 katı zoom'a kadar kullanılır (`lodK*4/dpr`), ötesinde
  canlı SVG (görünür alan küçük → raster ucuz). Katman aç/kapa (layer item,
  Hepsi/Temizle, Üst/Alt, ↑ en-üste) `pcbLodInvalidate()` → `lodGen` sayacı
  (üretim SIRASINDA eskirse `done`'da yeniden tetiklenir), 500ms sakinlikte
  yeniden üretim; hazır olana dek canlı SVG. Bilinen kısıtlar: bitmap'te
  `vector-effect:non-scaling-stroke` uygulanmaz (sayfa CSS'i SVG-image'a
  geçmez — hareket anında iz kalınlıkları mm-gerçek görünür) ve net highlight
  karartması bitmap'e yansımaz; ikisi de yalnız hareket anında, durunca aynı.
  (2) **3D LOD = dinamik çözünürlük**: döndürme/pan/zoom boyunca
  `renderer.setPixelRatio(min(basePR,0.6))` + `resize()` (~6× az piksel),
  220ms sessizlikte tam çözünürlük. `Döndür` (autoRot) etkilenmez.
  (3) **Toggle butonları**: şematik+PCB toolbar'da `#lod-toggle` (.tool-btn.active
  — şematik CSS'ine .active stili eklendi), 3D `#tb3d`'de `#v-lod` (.b3d.on).
  Tercihler localStorage'da: şematik `schviz-ui.lod`, PCB `schviz-ui.pcbLod`,
  3D `schviz-3dlod` anahtarı. Kapatınca her zaman canlı SVG/tam çözünürlük;
  şematik bitmap'leri yine üretilir (aç/kapa anında etkili), PCB bitmap'i
  kapalıyken üretilmez, açınca üretilir. GUI değişikliği YOK (kullanıcı
  runtime HTML toggle'ını tercih etti).

- **Performans: yakın zoom'da da etkileşim sırasında bitmap (v2.9.36,
  kullanıcı testi 2)**: v2.9.35 LOD'u uzak zoom'u akıcı yaptı ama kullanıcı
  yazı okumak için yakınlaşınca (scale > LOD_OFF → canlı SVG) takılma geri
  geliyordu — yakın zoom'da da her zoom adımı/pan karosu re-raster. Çözüm
  **harita uygulaması deseni**: pan sürüklemesi ve tekerlek zoom SERİSİ
  boyunca (`panInteract` — .panning ile birlikte; `wheelInteract` —
  `lodWheelTouch`, 180ms sessizlikte biter) `scale <= LOD_MAX_I = 4` iken
  bitmap gösterilir (harekette hafif yumuşak ama akıcı); hareket durunca
  canlı SVG'ye dönülür → tıklama/metin seçimi/hover DURAN görünümde aynen.
  `updateLod` artık `rest(histerezis) || (etkileşim && scale<=4)` mantığında.
  **Beyaz parlama önlemi**: bitmap→SVG dönüşünde `.lod` kalkar ama `.lod-fade`
  sınıfı bitmap'i 160ms daha ÜSTTE tutar (bitmap DOM'da svg'den sonra) →
  Chromium SVG karolarını bitmap'in arkasında rasterize eder, boş karo/flash
  görünmez. `LOD_RES` alt sınırı 1.25'e çekildi (etkileşim bitmap'i scale ~2'de
  okunur kalsın; ~2-3MB/sayfa). scale > 4'te etkileşimde de canlı SVG (bitmap
  oraya yetmez; görünür alan küçük olduğundan raster zaten ucuz). Headless
  Edge + CDP doğrulaması: scale 2 durunca '', tekerlek serisinde 'lod',
  seri bitince ~0.5s'te '', scale 6'da seri açıkken '' (üst sınır), 0.3'te
  'lod'. PCB viewer'a taşıma hâlâ aday iş.

- **Performans: şematik LOD — uzak zoom'da sayfa bitmap'leri (v2.9.35,
  kullanıcı testi sonrası)**: v2.9.34'ün hızlı iyileştirmeleri Chromium'da
  belirgin fark yaratmadı; `chrome://gpu` "Hardware accelerated" doğrulandı →
  darboğaz Chromium'un mimarisi (GPU raster açıkken bile her scale değişiminde
  görünür karolar Skia display-list'ten yeniden rasterize edilir; binlerce
  `<text>` glifli SVG'de kare süresini aşar). Çözüm **LOD**: `buildLods()`
  sayfa yüklendikten sonra idle'da (`requestIdleCallback`, 800ms timeout
  fallback'li) her sayfanın SVG'sini `XMLSerializer`→`Image`→`canvas` ile BİR
  KEZ bitmap'e çevirir (`.lod-bitmap`, kart-body boyutu × `LOD_RES =
  min(1.6, devicePixelRatio)` — kart 700×470 olduğundan sayfa başına ~1.3-2MB).
  `scale < 0.85`'te (`LOD_ON`) `#canvas.lod` sınıfıyla bitmap gösterilir, SVG
  `visibility:hidden` olur (display:none DEĞİL — highlight/aramanın
  getBoundingClientRect ölçümleri bozulmasın); `scale > 1.05`'te (`LOD_OFF`,
  histerezis) canlı SVG'ye dönülür — tıklama/metin seçimi/hover zaten o
  zoom'da yapılır (fitToSheet ~1.9 scale ürettiğinden sayfa okuma HEP canlı
  SVG'dedir). Bitmap'i kaydırıp ölçeklemek compositor'da bedavaya yakın →
  overview/çok-sayfa gezinmesi Chromium'da da akıcı. Net yayları (arc-layer,
  Python-önhesaplı pozisyon) ve kart çift-tık navigasyonu LOD'da çalışır;
  SVG-içi tıklama/hover uzak zoom'da devre dışı (zaten okunmaz). `Image`
  yüklemesi önce blob URL, `onerror`'da data: URI fallback (file:// ortam
  farkları); üretilemeyen sayfa canlı SVG'de kalır (davranış regresyonu yok).
  `preserveAspectRatio="none"` sayesinde drawImage hedef boyuta gerilir, ekran
  görünümüyle birebir. Headless Edge 150 + CDP (`--remote-debugging-port` +
  `Runtime.evaluate`; `--dump-dom` bu makinede sessizce boş çıktı verdi) ile
  file:// altında doğrulandı: 2 sahte sayfada bitmap üretimi + `.lod-ready`,
  scale 0.3→`lod` sınıfı var, scale 2→kalkıyor, 0.3'e dönünce geri geliyor.
  PCB viewer'a taşınmadı (aday iş — kullanıcı test sonucuna göre).

- **Performans: Chromium'da pan/zoom takılması — 3 hızlı iyileştirme (v2.9.34,
  kullanıcı bildirimi)**: HTML çıktı Firefox'ta akıcı, Chromium tabanlılarda
  (Edge/Chrome/Yandex) gezinirken takılıyordu. Mimari fark: Firefox (WebRender)
  vektör/metni her karede GPU'da çizer; Chromium ise `will-change:transform`
  katmanını CPU'da karolara rasterize eder — her scale değişiminde görünür
  karoların TAMAMI yeniden rasterize olur, pan'de yeni karolar anlık çizilir
  (binlerce `<text>` içeren SVG'de pahalı). Üç düzeltme (şematik + PCB viewer):
  (1) **Pan sırasında hit-testing kapalı**: gerçek pan başlayınca (hareket eşiği
  aşılınca, mousedown'da DEĞİL) viewport'a `.panning` sınıfı eklenir → şematikte
  `.sheet-body svg`, PCB'de `#pcb-svg` `pointer-events:none` olur; mouseup'ta
  kalkar. Böylece sürükleme boyunca her mousemove'daki binlerce-eleman hit-test'i
  ve `:hover` stil/repaint zinciri kesilir. Sınıf harekette eklendiğinden
  hareketsiz tıklamanın hedef elemanı değişmez (şematikte metin/tıklanabilir
  öğeler pan'i zaten başlatmaz; PCB'de pan-sonrası tıklama `moved` bayrağıyla
  yutulur). Şematikte pan başlarken `#svg-tip` balonu da gizlenir (asılı
  kalmasın). (2) **`.sheet-card`'a `contain:layout paint`**: hover/highlight
  repaint'i tek karta sınırlanır, tüm kanvas katmanını boyatmaz (kartın kendi
  box-shadow'u containment'tan etkilenmez — descendant değil). (3) **Tekerlek
  zoom rAF birleştirme**: zoom çarpanları `wheelF`'te birikir, kare başına TEK
  transform uygulanır (`requestAnimationFrame` + `wheelPend` bayrağı) — yüksek
  çözünürlüklü tekerlek/trackpad kare başına birden çok event üretip her birinde
  tam re-raster tetikliyordu; tek event/kare durumunda matematik birebir aynı.
  **Kod dışı notlar**: Chromium'da asıl büyük şüpheli yazılım rasterizasyonu —
  `chrome://gpu`'da "Rasterization: Hardware accelerated" olmalı (Win10 + eski
  Intel iGPU sürücüsünde blocklist'e takılıp software'e düşer). Firefox'un ~2GB
  RAM'i bu boyutta (30-50MB, gömülü SVG + three.js) tek dosya HTML için normal
  (WebRender retained display list + süreç modeli), sızıntı değil. Köklü çözüm
  (yapılmadı, aday iş): LOD — uzak zoom'da sayfa başına bitmap `<img>`, yakında
  canlı SVG.

- **Arama/cross-probe: hiyerarşik kanal designator'ları (R103 ↔ R103_diffI2C_1)
  (v2.9.33, kullanıcı sorusu)**: Repeat'li projede şematik MANTIKSAL designator
  gösterir (R103), board'da her kanal kopyası FİZİKSEL ad alır
  (`$Component_$RoomName$Index` → R103_diffI2C_1..3; BRK-210'da 30 böyle
  komponent). PCB araması birebir eşleşme yaptığından R103 "bulunamadı" diyordu;
  şematik→PCB/3D cross-probe da bu parçalarda sessizce çalışmıyordu. Dört nokta
  düzeltildi: (1) PCB araması: tam eşleşme yoksa `channelCopies()` (AD_ öneki)
  ile kanal kopyaları bulunur; Enter'a her basışta SIRADAKİ kopyaya geçilir
  (R103 → _1 → _2 → _3 → _1…). (2) PCB xprobe-in: mantıksal ad gelirse ilk
  kanal kopyası vurgulanır. (3) 3D xprobe-in: aynı önek çözümlemesi
  (meshByDesig üzerinde). (4) Şematik xprobe-in: fiziksel ad gelirse mantıksal
  tabana iner — önce `_<sayı>` kanal indeksi atılır (U2_1→U2), olmadıysa
  `_<oda>_<indeks>` soneki atılır (R103_diffI2C_1→R103); v2.9.30 Excel
  taban-designator fallback'iyle aynı kural. Multipart çözümleme
  (`resolveCompDesignator`, IC2A→IC2) değişmedi. Şematik template'inde regex
  `\d` Python string'inde `\\d` yazılır (komşu kodla tutarlı; py3.12
  SyntaxWarning'i önler).

- **3D: delikler artık GERÇEK delik (v2.9.32, kullanıcı isteği)**: Delikler board
  yüzeyinde koyu boyalı disk olarak duruyordu (v2.9.6 doku yaklaşımı); kullanıcı
  gri arka planın delikten görünmesini istedi. Üç parçalı çözüm: (1) `_extract_3d`
  yeni **`drills`** listesi üretir: ≥0.6mm çaplı YUVARLAK delikler (THT pad +
  büyük via; `hole_shape==0` şartı slot/kare delikleri eler, küçük via'lar
  kesilmez — dokudaki koyu nokta tented-via görünümü olarak kalır, earcut de
  şişmez; >1200 olursa büyükler öncelikli kırpılır). Eleman: `[x, y, r, plated]`
  (board-merkezli mm; plated = `pad.is_plated`, via=1). Delik çemberi board
  bbox'ının TAMAMEN içinde değilse atlanır + (x,y) 0.1mm'de dedupe edilir —
  earcut ASLA throw etmediğinden bozuk girdi (kenar kesen/çakışan delik)
  sessizce bozuk üçgenleme üretir, JS try/catch'i bu modu yakalayamaz; emniyet
  Python'da. (2) JS `buildScene`: delikler board `ExtrudeGeometry`'sinden
  **`shape.holes`** ile gerçekten kesilir (curveSegments=16). **Delik yönü
  CCW (`absarc(..., false)`) ŞART**: r128 hole-winding normalizasyonu yalnız
  dış kontur CCW gelip ters çevrildiğinde çalışır; bu board'ların outline'ı CW
  geldiğinden CW delikler duvar normallerini ters bırakıyordu (NPTH duvarı
  görünmez — adversarial review yakaladı, gömülü r128 kaynağından kanıtlandı).
  Kenar çizgisi DELİKSİZ geometriden üretilir (192 delik çemberi çizgi
  kalabalığı yapmasın). Kaplamalı deliklere **altın barrel**: tek
  `InstancedMesh` (CylinderGeometry openEnded, rotateX(π/2), DoubleSide;
  scale(rr, rr, th+0.04), rr = min(r·0.96, r−0.05) — mutlak ≥50µm boşluk küçük
  deliklerde z-fight'ı önler; **`frustumCulled=false` ŞART** — r128 instanced
  mesh'i birim-silindir bounding sphere'iyle cull edip köşe zoom'unda tüm
  barrel'ları kaybettiriyordu). NPTH montaj delikleri barrel almaz (çıplak FR4
  duvar). (3) `addSurface`: doku kanvasında delik içleri `destination-out` ile
  ŞEFFAF delinir (altın annular ring korunur; r·k+0.8px pay koyu delik boyasının
  AA kalıntısını temizler). Dünya→kanvas eşlemesi düzlem yerleşiminden türetilir
  (`u=(x−(s.cx−w/2))·cw/s.w`, `v=((s.cy+h/2)−y)·chh/s.h`) — üst ve alt doku aynı
  XY eşlemesini kullandığından (v2.9.4) tek formül iki yüzde de çalışır; sayısal
  doğrulandı (<0.1px sapma, 36/36 delik). Delme yalnız `surf.ok=1` iken yapılır:
  `_build_board_surface` outline'ı güvenle bulamayıp merkezleme fallback'ine
  düşerse doku dünya-gerçeğinden kayabilir — dünya-demirli delme o durumda koyu
  delik boyasını hilal olarak açığa çıkarırdı; delme kapatılınca eski (boyalı)
  görünüm korunur. Sonuç: delikten bakınca barrel'ın altın iç duvarı + arka plan
  görünür (Altium/KiCad 3D gibi). Eski tarayıcı (DecompressionStream yok): doku
  zaten yok, geometri delikleri yine kesilir. `D.drills` guard'lı — eski/PCB'siz
  veride davranış değişmez.

- **3D: KESİN Altium yerleşim semantiği — tüm sezgiseller kaldırıldı (v2.9.31,
  kullanıcı bildirimi: BRK-210'da GYK-J2/GYK-J3/D7 yönleri KiCad'e göre yanlış)**:
  GYK-J2/J3 (D-sub, BOTTOM katman) yüzleri ters, D7 (P600 bükük-bacak aksiyel
  diyot, rx=90/ry=270) uzun ekseni etrafında 90° yuvarlanmıştı. Kök neden İKİ
  katmanlı: (1) v2.7.0'dan beri `model_3d_rotz` "tutarsız" sanılıp atılmıştı —
  aslında SORUN ROTASYON SIRASIYMIŞ. Ampirik tarama (8 aday sıra × 67
  sıra-ayırt-edici parça, outline-bbox eşleşmesi) kesin sırayı verdi:
  **R = Rz(rotz)·Ry(roty)·Rx(rotx)** (67/67; eski varsayım Rx·Ry yalnız 41/67).
  rotz içte değil dışta ama Rx en içte — rotz atılınca tilt'li parçada eksik Rz
  ROLL hatasına dönüşüyordu (D7'nin bacakları yana bakıyordu); outline-fit/flip/
  J4-özel-durumu hep bunun yamalarıydı. (2) Alt katman `scale.z=-1` AYNAydı
  (det=-1) — simetrik parçalarda görünmez ama D-sub gibi yönlü parçada yüz 180°
  ters + D-şekli ters elli. Doğrusu **anchor'dan geçen X ekseni etrafında 180°
  proper rotation** (GYK-J2 pad skoru: Rx(180)=0.98mm vs Ry(180)=24.9mm —
  tartışmasız). Konum да kesinleşti: **anchor = `model_2d_x/y`** (birim 0.1µmil
  → ×1e-4 mil), **dikey = `model_3d_dz`** (model orijini board yüzeyinin dz
  üstünde; 257/274 parçada zmin+dz≈0, THT'lerde zmin+dz = standoff = pin
  çıkıntısı — birebir). **Doğrulama: bacak↔pad hizalaması** — BRK-213/210: 274
  STEP gövdede ort. 0.33mm (kalan sapmalar artefakt: D7 bacak ucu 0.33mm ama
  bacak orta-segmentinde verteks yok; GYK-J3'ün 4.4mm'lik iki pad'i modelde
  metali olmayan kasa delikleri); Smart_MCU: 75/75 < 0.8mm. **Kaldırılanlar**:
  `_model_inplane_angle`, `_model_body_base`, outline-fit `ang/zdeg`, `flip`,
  J4 `zdeg+=180` özel durumu, `pins_up`/`zu`, pad-merkez konumlama, standoff/
  zb-clamp seating — hepsi kesin veriyle gereksizleşti (v2.9.17-28'in tilt/
  flip/seating yamaları bu sınıfın tamamını kapsıyordu). JS `buildModels`
  sadeleşti: quaternion q = Qz·Qy·Qx (+ altta Qx(π) premultiply), konum
  (cx, cy, ±(th/2+dz)). `model_2d` yoksa (0,0) outline-centroid fallback;
  anchor-centroid MESAFESİ kötü-veri sinyali değildir (origin'i kenarda
  modellenmiş Smart_MCU P1/U1'de 31-33mm meşru fark var — mesafe eşiği
  denendi ve kaldırıldı).

- **Excel: NC pinler + Desig/Pin Say. sütunları + MCU başta + önek hariç tutma
  + KRİTİK ad-çakışması düzeltmesi (v2.9.30, kullanıcı geri bildirimi 2)**:
  (1) **NC satırları**: netlist yalnız bağlı pinleri içerir; bağlı olmayan
  MCU pinleri artık `compile_project_netlist`'in yeni `all_pins` kataloğundan
  (her komponentin TÜM pinleri: `AltiumSchComponent.children` içindeki
  `AltiumSchPin`'lerden; multipart soneki `IC2A→IC2` normalize edilir) eklenir:
  Sinyal Adı "NC", hedef "(bağlı değil / NC)" (net='' iç işareti). Hem MCU pin
  listesinde hem IC haritasının ana işlemci grubunda. (2) **KRİTİK: port-adı
  yeniden adlandırması ad çakışması yaratıyordu** — seri direncin arkasındaki
  otomatik adlı PCB neti (NetR162_1) de 'SPI_MISO' port adını alınca ada göre
  kurulan `net_terminals` sözlüğünde GERÇEK SPI_MISO'yu eziyor, U5.22/23 (MISO/
  MOSI) listeden kayboluyordu. Çözüm: `taken_names` koruması — aday ad başka
  bir PCB net'inde kullanılıyorsa yeniden adlandırma YAPILMAZ (otomatik ad
  kalır; bağlantı zaten pasif-izlemeyle görünür). (3) IC haritasına iki yeni
  sütun: **Desig** (Kontrol Entegresi yanında, dikey birleşik, ana işlemcide
  "★ ANA") ve **Pin Say.** (Entegre Portu yanında, komponentin TOPLAM pin
  sayısı — all_pins kataloğundan, kanal-sonekli parçalarda taban designator
  fallback'i). (4) **Ana işlemci grubu tablonun BAŞINA** alındı (sort key:
  `it[0] not in main_set`). (5) **`exclude_prefixes` parametresi + GUI alanı**
  (`excludePrefixEdit`, mcuSettingsFrame'de): "J,P,TP" gibi designator HARF
  önekleriyle çok pinli ama gereksiz komponentler (konnektör/header/testpoint)
  IC haritasından çıkarılır; ana işlemci asla hariç tutulmaz.

- **Excel: port adları sinyal adı olarak + GPIO_IN/GPIO_OUT yönleri + güç
  pinleri IC haritasından çıkarıldı (v2.9.30, kullanıcı geri bildirimi)**:
  (1) PA4'ün neti "NetU5_20" görünüyordu; şematikte o tel bir PORT'a
  (PWR_ARM_MCU) bağlı ama portlar net'e AD VERMEZ (Altium'da da öyle).
  `compile_project_netlist` artık her nete `ports` listesi ekler (endpoints
  role=='port' + şematik dokümanlardan `get_ports()` ile io_type zenginleştirme
  — endpoints'te io_type YOK). `_merge_netlist_with_pcb` PCB'nin otomatik adlı
  netlerini ("Net...") şu öncelikle yeniden adlandırır: tek şematik etiket adı >
  en yaygın port adı > PCB adı → PA4 neti "PWR_ARM_MCU", PC4 "ADC1_CS" oldu
  (BRK-209'da 69 net bu yolla adlandı). (2) **Yön**: şematik port ok yönü
  (`PortIOType` INPUT/OUTPUT/BIDIRECTIONAL) `_net_port_dir()` ile okunur; aynı
  isimli port birden çok sayfada olabileceğinden ANA İŞLEMCİNİN sayfasındaki
  port tercih edilir (yön MCU perspektifi: PWR_ARM_MCU→GPIO_IN, PEX_RST→
  GPIO_OUT). IC haritasında "Kontrol Arayüzü" sütunu artık SATIR bazında
  (dikey birleşik değil): net/pin adından arayüz tespiti (SCL→I2C, SPI_SCK→SPI,
  SWDIO/SWO→SWD, MCU_TX/RE/DE/RS485→USART; CS/IRQ tekil hatları GPIO kalır —
  mcu.xlsx örneğiyle uyumlu), arayüz değilse GPIO_IN/GPIO_OUT/GPIO. MCU pin
  listesinin "Fonksiyon/Arayüz" sütunu da aynı mantığı kullanır (`func_with_dir`).
  (3) IC haritasında güç pinleri artık hiç listelenmez: net tipi (power/ground)
  filtresine EK olarak pin fonksiyonu "Güç —" olanlar da atlanır (VDD/VBAT
  pinleri otomatik adlı filtre netlerinde kaçıyordu); `classify_net`/
  `is_power_net`/`_infer_pin_function`'a AVSS/AVDD/VBAT eklendi.

- **Netlist: hiyerarşik projelerde sahte NC pinler + kanal designator uyumsuzluğu
  → proje ayarlı derleme + PCB-doğrulamalı yeniden kurulum (v2.9.30)**:
  BRK-209 (hiyerarşik, kanal-tekrarlı Repeat sayfalı) projede MCU'nun 23 pini
  sahte "NC" çıkıyordu; mcu.xlsx el tablosuyla karşılaştırınca yakalandı.
  ÜÇ katmanlı kök neden ve çözüm:
  (1) `compile_project_netlist` `compile_netlist(schdocs, project)` çağırıyordu —
  `options=None` → `NetlistOptions()` varsayılanı (GLOBAL scope), projenin KENDİ
  ayarları okunmuyordu. Hiyerarşik projede port↔sheet-entry köprüleri kurulmaz,
  kanal designator'ları da yanlış formatta (U2A vs PCB'deki U2_1) çıkar. Artık
  `NetlistOptions.from_prjpcb(project)` geçiliyor (Altium'un derlemesini izler).
  (2) Bu bile yetmiyor: altium_monkey'in hiyerarşik derlemesi BAZI port
  köprülerini kaçırıyor (BRK-209'da MCU sayfasının SCL/SDA/PEX_INT/PEX_RST
  portları — üst sayfa BRK-211 üzerinden IC6'ya gidenler) ve kanal-tekrarlı
  sayfalarda kanal indeksi SIRASI Altium'un board annotasyonundan farklı
  olabiliyor (şematikte Q2_2 = fiziksel board'da Q2_5 → union-merge iki kanalı
  tek nete karıştırır, DENENDİ ve reddedildi).
  (3) **Kalıcı çözüm: `_merge_netlist_with_pcb()`** — PCB dosyası (rotalanmış
  board) Altium'un kendi derlemesinin sonucu = kesin doğru. PCB varsa netler
  PCB pad listesinden YENİDEN kurulur (net adı = PCB net adı, designator =
  fiziksel/silkscreen designator); pin adları şematikten tamamlanır (önce tam
  designator, yoksa kanal soneki atılmış taban: U2_1→U2 — sembol pinleri
  kanaldan bağımsız). PCB'de pad'i olmayan şematik netler korunur. Yanlış
  PcbDoc korumalı (designator örtüşmesi <%50 → no-op); PCB yoksa şematik esas.
  `_collect_data`'da netlist derlemesinden hemen sonra çağrılır → HTML/JSON/
  Excel TÜM çıktılar düzelir. **Doğrulama** (BRK-209 + mcu.xlsx): PA15→IC6.32
  INT, PC10→IC6.28 RESET, SCL/SDA'da IC6+IC1+U6, PC4→U2_1.CS — hepsi PCB ile
  birebir; 2767/2783 pin adı eşleşti. Smart_MCU regresyonsuz (252/252).
  IC haritasında kanal-sonekli parçalar için meta'ya taban-designator
  fallback'i eklendi (U2_1 → U2'nin değer/açıklaması).

- **Excel: MCU pin listesi + IC haritası mcu.xlsx formatına revize, seri pasif
  izleme (v2.9.30)**: Kullanıcı örnek bir el-yapımı tablo (mcu.xlsx) verdi:
  MCU pinlerinde karşı-uç olarak DİRENÇ listelenmesi anlamsızdı — sinyalin
  ulaştığı gerçek IC portu + net adı görünmeliydi (örn. PC4 → ADC1_CS → MCP3564
  CS). Çözüm: yeni **`_trace_net_endpoints()`** helper'ı — net'i 2-pinli seri
  pasifler (`_JUMPABLE_RE`: R/C/L/FB/F + rakam, pin sayısı==2 şartı RN/CN gibi
  çok-pinlileri doğal eler) üzerinden BFS ile izler (max 4 atlama), gerçek
  uç noktaları `via` zinciriyle döndürür; pasif üzerinden güç/toprak net'ine
  varış pull-up/pull-down (son pasif C ise 'filtre C') olarak ayrıca raporlanır.
  **generate_mcu_pinout_xlsx**: hedef sütunu artık izlenmiş IC portlarını yazar
  (`Y2.1 (IN/OUT) [R1 üzerinden] ; R27→+3.3V (pull-up)`); IC'ler önce,
  konnektörler sonra, testpoint'ler sonda (`_endpoint_sort_key`); izleme boş
  dönerse ham komşu listesine düşer. **generate_ic_map_xlsx**: eski IC-başına
  ayrı başlık/tablo yerine mcu.xlsx düzeninde TEK tablo — IC grupları dikey
  birleşik hücrede (Kontrol Entegresi/Arayüz/I2C Adres), yalnız sinyal pinleri,
  'MCU Portu' sütunu pasif-izlemeli, ana işlemci grubu en sonda, grup üst
  kenarı kalın çizgi + alternatif zemin. I2C adresi şematikten türetilemez —
  sütun '-' ile durur, elle doldurulur. Fonksiyon imzaları değişmedi (gui.py
  dokunulmadı). Smart_MCU ile doğrulandı: kristal pini `PD1-OSC_OUT (R1
  üzerinden)`, GPIO'larda `R27→+3.3V (pull-up) ; R28→GND (pull-down)` çıkıyor.

- **UX: build saati yerine sürüm rozeti, tek yerde (v2.9.29)**: HTML çıktılarında
  "build 17:36:58" birden çok yerde görünüyordu (birleşik kabuk rozeti, şematik
  sol panel `.build-tag`, `#brand` sonundaki saat, PCB sidebar `build-info`).
  Kullanıcı isteğiyle: kabuk sağ üst rozeti artık `{proje} · v{APP_VERSION}`;
  şematik `.build-tag` div+CSS silindi, `#brand` yalnız "altium_monkey", PCB
  `build-info` yalnız board boyutu. `APP_VERSION` gui.py→**viewer.py**'ye taşındı
  (gui import eder; döngüsel import yok çünkü gui→viewer tek yönlü). Üretim saati
  hâlâ `<title>`'da (eski-HTML/cache teşhisi sekme başlığından yapılır).

- **3D: alttan-monte (bükük bacaklı) SSR gövdesi board ÜSTÜNE kaldırılıyordu
  (v2.9.28)**: BRK-213'te kütüphane SSR modeli "Bukum-CPC40055ST" (bükük bacaklı,
  board ALTINA yatarak monte edilen varyant, rx=180 + standoff=−2.05mm) olarak
  değişince kullanıcı SSR1_x'lerin yanlış yerde olduğunu bildirdi. XY konum ve
  in-plane açı DOĞRUYDU (Altium `model_2d_x/y` + `rotz` ile birebir doğrulandı);
  sorun dikeydeydi: v2.9.19'un oturma kuralı `z0eff=max(z0,−zb)` "gövde her zaman
  board üstüne oturur" varsaydığından, kasıtlı board-altı gövdeyi "gömülü" sanıp
  ÜSTE kaldırıyordu (bacaklar havada yukarı bakıyordu). **Reddedilen aday**:
  flip'i kaldırmak (fixB) — parçayı düzlemde 180° döndürüyor, kullanıcı reddetti;
  doğrusu yönelimi KORUYUP gövdeyi Z'de alta indirmek (fixC, kullanıcı onaylı).
  **Çözüm**: `_model_body_base` artık `(zb, zt, pins_up)` döndürür — `zt` gövde
  ÜSTÜ (son geniş kesit bölgesinin tavanı), `pins_up` alttan-monte tespiti:
  yönlendirme sonrası ince uzantılar (bacaklar) YALNIZ gövde üstünde (üstte ≥1mm
  ince kısım, ilk geniş bölge altında ≤0.3mm) VE parça flip'li ise → parça ancak
  alttan monte edilebilir. Bu parçalara placement'ta `zu=−(th+zt)` eklenir; JS
  `buildModels` `pl.zu` tanımlıysa max-clamp yerine doğrudan `z0eff=zu` kullanır →
  gövde üstü board alt yüzüne yaslanır, bükük bacaklar delikten yukarı çıkıp
  üstte ~1mm taşar (KiCad görünümüyle eşleşir). **flip şartı kritik**: onsuz
  altı-düz gövde + üstte ince tel çıkıntısı olan L8 trafosu (42mm, flip=False,
  board üstünde doğru duran) yanlış pozitif oluyordu. **XY konumu da farklı**:
  bükük parçada bacaklar gövdenin BİR kenarından çıktığından v2.9.20'nin
  pad-merkezi kuralı gövdeyi bacak sırasına merkezleyip ~8.5mm kaydırıyordu
  (tam HTML'de kullanıcı fark etti: gövde sarı maske açıklığından kayık) →
  `pins_up` parçalarda konum pad merkezi DEĞİL **gövde-outline centroid'i**
  (Altium'un çizdiği yer, maske açıklığıyla eşleşir). **Statik doğrulama**
  (BRK-213): 865 STEP parçadan yalnız 9'u (SSR1_1..7, SSR2, SSR3) `zu` aldı,
  gövde üstleri tam board alt yüzünde (−0.80), cy pad(±46.21)→outline(±37.68);
  L8 dahil 856 parça DEĞİŞMEDİ.
  **Hızlı izole test tekniği**: tam üretim yerine `_extract_3d`+`build_3d_html`
  ile tek komponent + tüm diğer parçalar gri extrude referans kutu olarak ~35s'de
  test HTML'i üretilebilir (scratchpad `ssr1_test.py`/`l8_test.py`; çıktılar
  proje `PCB PROJECT/` klasörüne yazıldı) — ağır projede 3D yerleşim hatası
  ayıklarken kullan.

- **UX: Böl modunda ŞEMATİK/PCB pane etiketleri kaldırıldı (v2.9.27)**: Etiketler
  önce sol panelle çakışıyordu (üst-orta konuma taşınıp yalnız Böl moduna
  kısıtlanmıştı), kullanıcı gereksiz buldu → span'ler, `.pane-label` CSS'i ve
  setViewMode'daki gösterme/gizleme JS'i TAMAMEN silindi (ölü kod bırakılmadı).

- **UX: Şematik desenleri PCB viewer'a taşındı + 3D Parçalar toggle'ı (v2.9.26)**:
  PCB: katlanabilir panel (#sb-toggle, B, localStorage `pcbSidebar`), katlanabilir
  arama (/, Esc), +/− zoom, boş alana tık → net highlight temizle (SVG içi boş
  hedef VEYA canvas-wrap zemini, `moved` pan koruması). 3D: "Parçalar" butonu
  desig'li tüm mesh'leri gizler; Raycaster visible'a bakmadığından `pick()`
  `filter(m=>m.visible)` ile kısıtlandı; cross-probe seçimi gelirse otomatik
  geri açılır. Ayrıntılar: "PCB Viewer'a taşınan UX özellikleri" ve "3D Viewer:
  Parçalar butonu" bölümleri.

- **UX: 9 iyileştirme paketi (v2.9.25)**: (1) `smoothT()` — fit/reset/zoom
  butonlarında 0.35s yumuşak geçiş (tekerlek/pan anlık kalır); (2) toolbar'a
  Sayfa… açılır menüsü; (3) +/− zoom + Tümü (`fitAll`); (4) `#svg-tip` hover
  bilgi balonu (komponent/net/block); (5) Nets'te Tümü/Güç/GND/Sinyal filtre
  çipleri; (6) aramada Enter → ilk sonucu seç + boş durum mesajları;
  (7) `localStorage` kalıcılığı (panel durumu + yay renkleri, `schviz-ui`);
  (8) kabukta 1/2/3/4 mod kısayolları (odak kabukta olmalı — iframe içinden
  bubble etmez); (9) PCB/3D ilk yüklemede `.pane-loading` spinner'ı.

- **UX: küçük ok butonu + etiket çakışması + seçim davranışları (v2.9.24)**:
  (1) Kocaman "Paneli gizle" butonu → sağ üstte 20×20 ◂/▸ ok butonu; ŞEMATİK
  pane etiketi sol paneli eziyordu → üst-ortaya taşındı ve yalnız Böl moduna
  kısıtlandı (v2.9.27'de tamamen kaldırıldı). (2) Boş alana tek tık komponent
  seçim kutusunu (spotlight) temizler — `panMoved` (>3px), metin seçimi ve
  tıklanabilir öğe korumalarıyla. (3) `highlightComponent(..., focus=false)`:
  şematikte designator'a tıklayınca görünüm ortalanıp UZAKLAŞMAZ (kullanıcı
  zaten oraya bakıyor); arama/liste/cross-probe focus=true ile ortalamaya
  devam eder.

- **UX: sol panel tamamen katlanabilir (v2.9.23)**: 26px şerit + ▸ butonu,
  `B` kısayolu, kısayol modalına eklendi. `/` (arama) ve `showCompPopup`
  (panele dock'lu) panel kapalıysa otomatik açar — işlev boşluğa düşmez.

- **UX: açılış sadece-şematik + kopyalanabilir metin + katlanabilir arama
  (v2.9.22)**: (1) Birleşik görünüm "Böl" yerine "Şematik" modunda açılır;
  `requestIdleCallback` ile PCB ön-yüklemesi KALDIRILDI, PCB/3D tembel yüklenir
  (`curMode` korumalı `ensurePcbLoaded`, `lastSel`+`repostSel` cross-probe'u
  korur). (2) Şematik SVG metinleri PDF gibi seçilip kopyalanır: text'te
  `user-select:text`, metin üstünde pan başlamaz, sürükleyerek seçim varsa
  click aksiyonları tetiklenmez. (3) Arama kutusu "▸ Ara" altında katlanabilir,
  varsayılan kapalı; `/` açar, `Esc` kapatır+filtreyi temizler.

- **3D: J4 düzlem-içi 180° + SSR/çok-bölgeli parça oturması (v2.9.21)**: İki düzeltme.
  (1) **J4 in-plane**: `ry=180` (rx=0) ayak-izini X'te AYNALADIĞINDAN (yansıma)
  `_model_inplane_angle`'ın işaretli-φ'si düzlem-içi açıyı 180° ters veriyordu
  (J4: zdeg=−90 ama doğru=+90=`model_3d_rotz`). Bu grupta (tilt dağılımında yalnız
  J4) `zdeg += 180` uygulanır. MOV (rx=90,ry=180) bunu flip ile telafi ettiğinden
  HARİÇ. (2) **SSR oturma (flanş-atlama)**: SSR modelinin en altında GENİŞ ama İNCE
  bir montaj flanşı var, üstünde BOŞLUK, sonra gövde. `_model_body_base` en alt geniş
  bölgeyi (flanş) gövde tabanı sanıp gövdeyi ~3mm havada bırakıyordu. Artık geniş
  (>=%30) kesit bölgeleri bulunur; en alt bölge KISA (<=2 dilim) + üstündeki bölgeye
  KÜÇÜK boşlukla (<1.5mm) bağlıysa (montaj flanşı) BİR KEZ atlanır → gövde board'a
  oturur, flanş içeri iner. Boşluk BÜYÜKSE (ör. TB tabanı↔üst özelliği ~9mm) o bölge
  gövdenin TABANIDIR, atlanmaz (TB regresyonu önlendi). **Doğrulama** (BRK-213):
  SSR gövde tabanı havada(3.9)→board üstü(0.80); J4 zdeg 270→90 + oturur; MOV
  DEĞİŞMEZ (z0eff=−19.5, disk uzun bacakla 6.5mm havada — kullanıcı onaylı); TB1_1
  tabanı board'a oturur; C11/U7_5/L SMD oturması aynı. Tek havada kalan: 16 MOV
  (onaylı). Clamp yalnız 18 gömük/offset parçayı (C×11, SSR×5, J, L) kaldırır.

- **3D: J4 flip'i yanlış + gövde-outline pad'lerden kayık (SSR konum) (v2.9.20)**:
  İki ayrı bug. (1) **Flip fazlalığı**: v2.9.18'in flip kuralı `rx%360==180 or
  ry%360==180` idi; **saf ry=180** (rx=0) olan J4 (kenar konnektörü) de flip'leniyordu
  ama J4 için Altium'un `ry=180` yönelimi ZATEN doğru → J4 3D'de **180° ters** çıkıyordu
  (kullanıcı bildirdi). MOV (rx=90,ry=180) ve SSR/L (rx=180) flip'e gerçekten muhtaç.
  Kural daraltıldı: `flip = (rx==180) or (rx==90 and ry==180)` → J4 (rx=0) artık
  flip'lenmez, MOV/SSR/L değişmez. (Not: rx≠0 & ry≠0 olan TEK grup MOV olduğundan bu
  ayrım güvenli.) (2) **Konum kayması**: bazı kütüphane footprint'lerinde 3D
  gövde-**outline**'ı pad'lerden KAYIK çiziliyor (SSR ~11mm, J4 ~6.8mm, terminal blok
  TB ~4mm, J2 ~2mm); model outline centroid'ine oturtulduğu için yanlış yere düşüyordu
  (SSR pad'lerinin 11mm yanında). `_extract_3d` artık `pcb.pads`'ten komponent **pad
  merkezini** hesaplayıp STEP placement konumunu (cx,cy) buradan alır (yoksa outline
  centroid fallback). Pad merkezi fiziksel doğru yer + Altium `model_2d` ile ~1mm içinde
  eşleşir (KiCad ile aynı). **Doğrulama** (BRK-213): flip seti 24→23 (J4 çıktı; MOV×16
  SSR×5 L×2 kaldı); SSR konumu outline(−77.3)→pad(−66.0) 11mm düzeldi; MOV konumu
  (−72,−54) DEĞİŞMEDİ (pad=outline); 21 kayık-outline parça (SSR/J4/TB/J2) pad'lerine
  oturur, kalan 719 parça pad≈outline (<2mm) → dokunulmaz.

- **3D: negatif standoff parçayı board'a gömüyor (SSR yükseklik) (v2.9.19)**: v2.9.18
  MOV baş-aşağı sorununu çözdü; kullanıcı SSR'nin **yükseklik/oturma** sorununu
  bildirdi (KiCad 3D ile karşılaştırmalı görsel). Kök: bu kütüphanede bazı parçaların
  `standoff_height_mils` değeri **negatif** (SSR −80mil=−2.05mm, MOV −767mil=−19.5mm,
  bir non-flip parça −34.5mm). Kod `outer.z = th/2 + z0` ile bunu doğrudan uyguluyordu
  → SSR gövdesi board üst yüzünün ~2mm ALTINA gömülüyor, pinleri board'un altından
  çıkıyordu (dünya-z tabanı −1.25, board üstü +0.80). MOV'un büyük negatif standoff'u
  diskini board yakınına oturttuğu için (havada, gömük değil) MOV "düzgün" görünüyordu.
  `overall_height` da güvenilmez (SSR 4.32mm ama mesh 6.4mm) — KiCad geometriyle
  oturtuyor. **Çözüm**: yeni `_model_body_base()` — buildModels'in yönlendirmesini
  (tilt+flip+recenter) replike edip modelin **gövde tabanı** yerel z'sini (`zb`,
  kesit XY-alanı tepe %30'una ulaşan ilk z-dilimi) bulur; placement'a `zb` eklenir.
  JS'te `z0eff = max(z0, −zb)` → gövde tabanı board üst yüzünün altına inecekse
  KALDIRIR, aksi halde DOKUNMAZ (yalnız kaldırır, indirmez). **Sonuç**: SSR gövde
  tabanı board üstüne oturur (tepe 0.80→7.10, KiCad ile eşleşir); MOV z0eff=z0 kalır
  (DEĞİŞMEZ, havada disk korunur); SMD parçalar (<0.05mm) ve non-flip büyük-negatif
  standoff'lu parça (havada, gömük değil) dokunulmaz. Statik doğrulama (BRK-213):
  yalnız **18/740** parça değişir (gömük olanlar: SSR×5, TB×6 terminal blok, C×5,
  J, L) — hepsi board'a düzgün oturur; MOV ve 706 doğru parça sabit.

- **3D: 180° tilt'li komponentler (MOV, SSR, L, J) BAŞ-AŞAĞI (v2.9.18)**: v2.9.17
  düzlem-içi (Z) dönüşü düzeltti ama kullanıcı asıl sorunun **baş-aşağı çevrilme**
  olduğunu bildirdi (annotasyonlu görsel): MOV through-hole diskinin gövdesi board
  içine gömülü, **bacakları yukarı**; SSR'nin **alt yüzü görünüyor, bacakları
  deliklerin karşısında**. Tilt (`rx,ry`) three.js Euler'i ile uygulanınca **180°
  bileşen** (MOV `ry=180`; SSR/L3/L4 `rx=180`; J4 `ry=180`) modeli baş-aşağı
  çeviriyordu; 0°/90° tilt'ler (521 `rx=90` + 185 tilt-0 + 9 `ry=90` = doğru render
  edilen 706 parça) sorunsuz. Kök: extrakte mesh Z-up ve tilt-0 ankoruyla (U7_5,
  gövde yukarı) doğrulandı → mesh doğru, yalnız 180° tilt uygulaması ters çeviriyor.
  **Çözüm**: `_extract_3d` her placement'a `flip = (rx%360==180 or ry%360==180)`
  ekler; `buildModels` tilt'ten sonra flip'li parçayı **ayak-izi uzun ekseni
  (`φ = ang − zdeg`) etrafında 180° çevirir** (three.js quaternion, tilt sonrası
  world-frame; sonra recenter). Uzun eksen korunduğu için v2.9.17'nin in-plane
  hizası bozulmaz; yalnız gövde yukarı / bacak-pin aşağı döner. **Statik doğrulama**
  (BRK-213): MOV bacak + SSR pin yönü dünya-Z'de eskiden +1.00 (yukarı, ters) →
  yeni −1.00 (aşağı, doğru); flip=True yalnız 24 parçada (16 MOV + 7 rx=180 + J4),
  706 doğru parça flip=False (dokunulmaz). **Not**: L3/L4/J4 de flip setinde (aynı
  180° tilt paterni) — görsel teyit önerilir.

- **3D: tilt'li komponentler (MOV, SSR, bazı IC) düzlem-içinde 180° ters (v2.9.17)**:
  STEP modelli gövdelerin düzlem-içi (Z) dönüşü "outline-fit" ile bulunuyordu
  (`buildModels`): gerçek açı gövde konturundan (`ang`), modelin kendi yönü ise
  `psi ∈ {0°,90°}` dik-açı snap'inden (`z = ang − psi`). `psi` yalnız EKSENİ (0/90)
  verir; modelin hangi UCA baktığını (**±180° işaret**) veremezdi çünkü post-tilt
  kutu (`sz.x` vs `sz.y`) büyüklük snap'iydi. Model tilt'i (`rx,ry`) 180° içerince
  (MOV `rx=90,ry=180`; SSR `rx=180`) modelin ayak-izi uzun ekseni tilt sonrası
  `-X`'e döner ama `psi` `+X` sanar → parça düzlemde **180° ters** (kullanıcı
  bildirdi: BRK-213 MOV1_2, SSR1_2). **Kök çözüm**: yeni `_model_inplane_angle()` —
  tilt matrisinin (`T=Rx(rx)@Ry(ry)`, three.js 'XYZ' ile birebir) sütunlarından
  native X/Y/Z eksenlerinin tilt sonrası dünya-XY görüntüsü çıkar, ayak-izinde en
  baskın ekseni (native uzunluk × XY-yatkınlık) seç, **işaretli** açısı `φ` ile
  `zdeg = ang − φ` hesapla (Python'da; `psi` tamamen kalktı). JS `buildModels` artık
  `z = zdeg*DEG` kullanır. **Statik doğrulama** (BRK-213, 740 STEP): yeni yöntem
  yalnız 29 tilt'li parçayı değiştiriyor (16 MOV + 12 `rx=90` uzun-ekseni native-Z
  olan IC/U/Rdamp + J4); 185 düz + 509 iyi-davranan ayakta parça DEĞİŞMEDEN kalıyor
  (işaretin kaybolmadığı yerde `zdeg == ang−psi`). MOV/SSR spot-check 7/7 doğru.
  **Reddedilen ara-çözüm (v2.9.16, `model_3d_rotz`)**: rotz'u placement'a ekleyip
  outline-fit'ten ~180° sapınca çevirmek denendi ama YANLIŞ — rotz yüksek-tilt
  parçalarda güvenilmez (v2.7.0'daki "tutarsız" gözlemi doğruymuş): SSR'yi çevirdi
  ama MOV'u çeviremedi, kullanıcı "düzelme yok" dedi. `zdeg` (geometri) rotz'a değil
  modelin gerçek eksenine dayandığından doğru. `model_3d_rotz` artık kullanılmıyor.
  **Bilinen kısıt**: alt-katman STEP parçaları hâlâ `-z` + `scale.z=-1` ile aynalanır
  (bu board'da MOV/SSR üst katmanda); aynalı alt parçalarda işaret ayrıca kontrol
  edilmeli (ayrı iş).

- **Uygulama ikonu (icon.ico) — exe + çalışan pencere (v2.9.15)**: `--icon` tek başına
  yalnız exe DOSYA ikonunu ayarlar (Explorer); çalışan uygulamanın pencere/taskbar ikonu
  ayrı `setWindowIcon` ister. Üç yerde de görünsün diye: (1) `gui.py`'ye `ICON_FILE` sabiti
  (UI_FILE gibi `sys._MEIPASS` frozen-yol desteğiyle), (2) `MainWindow.__init__` →
  `self.setWindowIcon` (başlık çubuğu), (3) `main()` → `app.setWindowIcon` (taskbar);
  ikisi de `if ICON_FILE.exists()` korumalı. **PyInstaller**: `--icon icon.ico` (dosya
  ikonu) + `--add-data "icon.ico;."` (runtime'da setWindowIcon bulsun diye gömülür) —
  ikisi de `build_exe.bat`'te. **`build_exe.bat`**: çift-tıkla çalışan paketleme betiği
  (proje dizinine geçer, PyInstaller yoksa kurar, tüm `--collect-all` + gui.ui/icon.ico
  `--add-data`, sonuç/hata mesajı + `pause`).

- **HTML gösterim performansı — 5 iyileştirme (v2.9.14)**: (1) **GPU ipucu**: 2D PCB
  `#pcb-svg` ve şematik `#canvas`'a `will-change:transform` → zoom/pan composit'i GPU'ya
  alınır, raster jank azalır. (2) **3D**: `renderer.setPixelRatio` cap 2→1.5 (yüksek-DPI'de
  FPS), hover raycast `requestAnimationFrame` ile throttle (yüzlerce mesh'te her mousemove
  yerine frame başına 1 raycast). (3) **2D PCB tembel katman**: varsayılan KAPALI katmanlar
  açılışta DOM'a konmaz (boş `<g data-lazy>`, içerik `LAZY_SVG` JS objesinde), ilk gösterimde
  `ensureLayerLoaded` enjekte eder → başlangıç DOM/parse ↓. Çapraz-katman işlemler
  (`highlightNet`, `buildPadLabels`, `highlightComp`) gizli katmanları da taradığından
  başlarında `loadAllLazyLayers()` ile tümünü yükler (ilk tetikten sonra no-op) — işlev
  korunur. (4) **Birleşik tembel PCB iframe**: şematik HEMEN, PCB `requestIdleCallback` ile
  idle'da (Böl modunda da görünür), 3D ilk gösterimde yüklenir; cross-probe/mod değişiminde
  `ensurePcbLoaded`; yükleme sonrası `repostSel` ile son seçim yeniden iletilir (async srcdoc
  zamanlaması). (5) **gzip gömme**: birleşik kabukta iç HTML'ler (SCH/PCB/TD) ham JSON yerine
  **gzip+base64** gömülür, runtime'da `DecompressionStream` ile açılıp `srcdoc`'a yazılır
  (`gunzipB64`). base64 olduğundan `</script>` kaçışı da gerekmez. Gerçek veride SCH 489→146KB,
  PCB 2913→652KB (~3-5×); Smart_MCU birleşik çıktı ~1.8MB. Eski tarayıcı (DecompressionStream
  yok) → iframe'de uyarı mesajı. Standalone viewer'lar (inline SVG, srcdoc değil) gzip almadı
  — riskli, ayrı iş.

- **2D PCB: Top Copper tam kırmızı, Bottom Copper tam mavi (v2.9.13)**: `LAYER_STYLE`'da
  TOP `#ff0000`, BOTTOM `#0000ff` yapıldı (Altium konvansiyonu). Benzersizlik geçişi
  (v2.9.12) bunları ilk-gelen curated renk olarak KORUR; `_gen_distinct_color` üretilen
  renkler soluk (doygunluk ≤0.68) olduğundan tam kırmızı/maviyle EXACT çakışmaz ve
  görsel olarak ayrışır (BRK-213'te en yakın diğer katman kırmızıya d≈148, maviye d≈127
  — net farklı tonlar). 21/21 benzersiz korunur.

- **2D PCB: TÜM katmanlara benzersiz renk garantisi (v2.9.12)**: v2.9.11 inner/plane'i
  ayırdı ama mech katmanları hâlâ tek renk (`#7a6f4a`), "other" tek renk (`#888888`),
  paletler de board çoksa sarabiliyordu. Artık `collect_pcb_layers` katman renklerini
  iki fazda atıyor: (1) curated/palet renk seç (ham svg saklanır, recolor ERTELENİR),
  (2) **benzersizlik geçişi** — ilk gelen curated renk KORUNUR; çakışan her katman
  `_gen_distinct_color(i)` (golden-angle 0.618 HSL, geniş ton dağılımı) ile üretilen
  ayırt edilebilir renk alır; sonra HAM svg'den FINAL renge recolor edilir (recolor
  yıkıcı olduğundan her zaman ham'dan, üst üste binmeden). Doğrulandı: BRK-213'te 21/21
  katman benzersiz (Mech 2/5/10/11/13/15 önceden hep aynıydı, artık farklı). Top turuncu,
  Bottom mavi, silk beyaz gibi anlamlı renkler korunur.

- **2D PCB: iç katmanlar (Inner 1-4) hep aynı renkti (v2.9.11)**: `collect_pcb_layers`
  tüm MID (iç sinyal) katmanlarına tek sabit renk (`#8a6d3b`), tüm PLANE'lere tek renk
  (`#6b8e23`) veriyordu → çok katmanlı board'larda Inner 1/2/3/4 ayırt edilemiyordu
  (swatch + render aynı). Çözüm: **`INNER_PALETTE`** (8 ayırt edilebilir renk) +
  **`PLANE_PALETTE`** (6 renk) eklendi; katman adının sonundaki numara (`re.search(r"(\d+)$")`)
  ile indekslenir (palet uzunluğunca döner). 4 inner katman artık 4 farklı renk alıyor
  (doğrulandı). Renk recolor zaten swatch'a boyadığından (v2.9.7) render de ayrışır.

- **2D PCB: imleç nişangah (crosshair) (v2.9.10)**: PCB kanvasında fare imleci `grab`/
  `grabbing` yerine **crosshair** yapıldı (Altium benzeri hassas konumlama). `#canvas-wrap`
  varsayılan + `.grabbing` (pan sırasında) ikisi de `cursor:crosshair`. Yalnız CSS değişti.

- **2D PCB: katmanı en üste getirme (v2.9.9)**: Katman panelinde her satıra göster/gizle
  toggle'ına EK olarak **"↑" (en üste getir)** düğmesi eklendi. Katmanlar `#pcb-svg`
  içinde DOM sırasına göre yığıldığından (sonraki=üstte), seçilen katmanın `<g>`'si
  diğer katmanların üstüne (ama pad-etiketi/highlight overlay'lerinin ALTINA) taşınır
  (`bringLayerToTop`). Overlay sınırı `svg.children` içinde ilk `.pcb-layer` olmayan
  eleman bulunarak korunur. Aynı düğmeye tekrar basınca **orijinal sıraya döner**
  (`restoreLayerOrder` — katmanları `LAYERS` id sırasında yeniden yerleştirir; toggle).
  Üste getirilen katman otomatik görünür yapılır ve satırı vurgulanır (`.layer-top.on`).
  Satır tıklaması yine göster/gizle (düğme `stopPropagation` ile ayrık).

- **2D PCB: arka plan rengi toolbar'dan ayarlanabilir (v2.9.8)**: `build_pcb_html`
  toolbar'ına **"Zemin"** düğmesi eklendi — arka planı döngüyle değiştirir (Siyah →
  Koyu gri → Gri → Açık; `BG_PRESETS` + `applyBg()`). Nokta ızgarası rengi zemine göre
  kontrastlı seçilir. Varsayılan siyah (önceki davranış korunur); kullanıcı gri/açık
  seçebilir. PCB standalone + birleşik görünüm PCB iframe'inde çalışır. (3D görünümün
  zaten kendi gri zemini var — v2.8.0.)

- **2D PCB: katman renkleri swatch ile uyuşmuyordu + güç düzlemi (plane) dolu alanı
  yoktu (v2.9.7)**: (1) `build_pcb_html` katmanları altium_monkey'in **ham renkleriyle**
  çiziyordu (TOP kırmızı #FF0000, BOTTOM mavi #0000FF, silk sarı #FFFF00, solder mor …)
  ama sidebar swatch'ı `LAYER_STYLE` rengini gösteriyordu → render ile swatch uyuşmuyordu.
  (2) Bakır **pour'u** (shapebased-region, ham #000000) siyah çizildiği için görünmüyordu;
  sadece izler görünüyordu. (3) **PLANE** katmanlarında altium_monkey dolu pour'u HİÇ
  vermiyor (yalnız board outline + 4 split çizgisi) → Altium'da dolu kırmızı güç düzlemi
  bizde boştu. Çözüm: yeni **`_recolor_pcb_layer(svg, color, role)`** — her katmanın tüm
  primitive fill/stroke renklerini swatch rengine (`color`) boyar (render↔swatch birebir,
  Altium gibi çok-renkli); beyaz knockout (#FFFFFF) → şeffaf clearance (drill rolünde
  delik=color); board outline (#C0A000) → nötr gri kenar; #000000 pour da boyandığından
  **dolu bakır alan görünür**. PLANE rolünde board outline path'inden **yarı-saydam dolu
  pour SENTEZLENİR** (`data-feature="plane-fill"`, fill-opacity 0.5) → Altium benzeri dolu
  güç düzlemi (anti-pad verisi olmadığından yaklaşık, görselleştirme amaçlı). `collect_pcb_
  layers` yalnız `layers_out` kopyasını boyar; `all_layers` ham kalır → **3D yüzey dokusu
  (`_build_board_surface`) etkilenmez** (kendi ham-renk recolor'ını yapar, 309 altın+256
  delik korundu). Doğrulandı: 15 katmanda ham renk kalmadı (hepsi swatch), 2 plane'de pour
  sentezlendi. **Bilinen kısıt**: plane pour'u anti-pad/clearance içermez (altium_monkey
  vermiyor); plane'ler varsayılan KAPALI, açınca yarı-saydam alan olarak görünür.

- **3D yüzey dokusunda delikler yoktu + pad'ler sönüktü (v2.9.6)**: 3D board yüzeyinde
  through-hole/via **delikleri görünmüyordu** ve pad'ler Altium'daki parlak altın yerine
  sönük yeşilimsi haldeydi (`_build_board_surface.comp()` eksikti). Kök sebep: (1) **DRILLS
  katmanı** hiç eklenmiyordu — oysa içinde `data-primitive="pad-hole"` + `"via-hole"`
  circle'ları (delikler) var. (2) Pad'ler yalnızca copper katmanında **%50 opaklıkla**
  çiziliyordu → yeşil board üstünde sönük; gerçek pad metali burada `data-primitive="pad"`
  elemanlarında ama altın overlay yoktu. (3) Bu board'da `MULTILAYER` katmanı yalnız board
  outline path'i içeriyor (gerçek pad değil) — pad'ler TOP/BOTTOM bakırında. Çözüm: yeni
  **`prim(key, prim_vals, color, opacity)`** helper'ı bir katmandan yalnız belirli
  `data-primitive` elemanlarını çıkarıp renklendirir (board outline gibi diğer path'leri
  hariç tutar). `comp()` katman sırası (alttan üste): izler (sönük bakır %50) → **pad'ler
  (`data-primitive="pad"` → opak altın)** → SMD pasta → MULTILAYER → silk → **DELİKLER
  (`pad-hole`+`via-hole` → koyu #141414, en üstte)**. Delikler en üstte olduğundan altın
  pad diskinin ortasında koyu görünüp Altium'daki **altın halka + delik** görünümünü verir.
  `_recolor` ortak yardımcıya çıkarıldı (grp+prim paylaşır). Doğrulandı: Smart_MCU
  yüzeyinde 256 koyu delik (86 pad-hole + 170 via-hole) + 309 altın pad. Üst+alt yüz aynı
  DRILLS'i kullanır (delik iki tarafta da doğru).

- **3D yüzey dokusu büyük board'larda bulanıktı — board'a kırpma (v2.9.5)**: board,
  SVG viewBox'ından çok küçükse (`to_layer_svgs` board dışı fab/mekanik/dimension içeriği
  de çizdiği için viewBox board'dan kat kat büyük olabilir — ör. BRK-213: board 160×109mm
  ama viewBox **479×292mm**) sabit 2048px doku kanvası tüm viewBox'a yayılıyordu →
  board'a yalnızca ~680px düşüp silk/designatör yazıları **bulanık** oluyordu (Smart_MCU
  gibi board'un viewBox'ı doldurduğu projelerde sorun yok). Çözüm: `_build_board_surface`
  artık kazanan board-outline adayının **tam bbox**'ını saklar ve wrapper SVG viewBox'ını
  **board bbox + %6 margin**'e (kaynak viewBox'a clamp'li) KIRPAR → 2048px kanvas board'a
  yoğunlaşır (BRK'de 4.3→11.4 px/mm, ~2.65× keskin). Hizalama dönüş formülü kırpılmış
  viewBox ile yeniden türetilir (`cx=cvbx+cvbw/2−bcx`, `cy=bcy−cvby−cvbh/2`); board merkezi
  yine dünya origin'ine düşer (board mesh de orada). **Regresyon koruması**: kırpma yalnız
  anlamlı küçülme varsa uygulanır (`cropW < 0.92·vbw`); board viewBox'ı dolduran projelerde
  (Smart_MCU) atlanır, çıktı birebir aynı kalır. SVG içeriği değişmez (sadece görünüm
  penceresi daralır), dosya boyutu ~aynı. Statik teşhisle doğrulandı: Smart_MCU değişmedi,
  BRK board merkezi origin'e tam oturdu (sapma 0.000).

- **3D ALT görünüm: bakır dokusu komponentlerle hizasız + bakır board dışına taşıyor
  + designatör yazıları ters (v2.9.4)**: Alt yüz bakır/silk/pad dokusu `addSurface`'te
  `pl.rotation.x = Math.PI` ile çiziliyordu (Y-flip). Bu, board feature `(x,y)`'yi dünya
  uzayında `(x, 2·cy−y)`'ye kaydırıyordu; oysa alt komponentler (`buildModels`,
  `outer.scale.z=-1`) XY'lerini **koruyarak** gerçek board koordinatında duruyor →
  doku ile komponentler Y'de kayık, board merkezi viewBox merkezinde değilse bakır
  board dışına taşıyor, alt-silk yazıları ters görünüyordu. **Değişmez (kanıt):** bir
  through-hole pad fiziksel olarak tek bir `(X,Y)` noktasında — üst+alt katmanda **aynı**
  dünya XY'sinde olmalı; üst doku rotasyonsuz `(X,Y)`'ye koyduğuna göre alt doku da
  **aynı dönüşümle** koymalı. Çözüm: alt yüz dokusundan **rotasyon kaldırıldı**, materyal
  `side:THREE.DoubleSide` yapıldı (aşağıdan/Alt kameradan görünür). Böylece alt doku alt
  komponentlerle birebir hizalanır; SVG'deki aynalı alt-silk (X-ray üstten projeksiyon)
  + DoubleSide arka yüz + Alt kameranın (az=π) X-aynası birbirini götürüp designatörleri
  **düz okunur** kılar (Altium 365 online viewer alt görünümüyle eşleşir). Üst yüz
  davranışı değişmedi.
  - **Çoklu-board doğrulaması**: düzeltme iki board'da statik teşhisle doğrulandı —
    Smart_MCU (57×51mm viewBox, board onu dolduruyor) ve BRK-213 (board **160×109mm**
    ama viewBox **479×292mm**, board fab içerikli dev kanvasın ~1/3'ü — "board merkezi
    viewBox merkezinde değil" sınır durumu). Her ikisinde de `_build_board_surface`
    merkez tespiti **en güçlü sinyalle (boyut+#C0A000 renk eşleşmesi)** board outline'ını
    buldu → board merkezi dünya origin'ine düşüyor (board mesh de orada), hizalama formülü
    tutuyor. Merkez tespiti başarısını artık her zaman loglar (önceden yalnız fallback
    loglanıyordu): "· board outline merkezi: boyut[+#C0A000] eşleşme (bcx,bcy, N aday)".
  - **Bilinen kısıt (hizasızlık DEĞİL)**: viewBox board'dan çok büyükse (BRK gibi fab/
    mekanik içerik board dışına taşınca) doku 2048px kanvasa viewBox kadar sığdırıldığından
    board üzerindeki bakır/silk **çözünürlüğü düşer** (keskinlik kaybı, hizalama doğru).
    İleride viewBox'ı board bbox'ına kırpmak çözünürlüğü artırabilir.

- **3D STEP modelleri sessizce çalışmıyordu (v2.9.3)**: `_extract_step_models`
  `cascadio`+`trimesh` import'u başarısız olunca boş `{}` döndürüp **sessizce**
  extrude kutulara düşüyordu (yalnızca log'a "cascadio/trimesh yok" yazıyordu, fark
  edilmesi zor). Üretim makinesinde bu iki paket eksik kalınca (ortam yenilenmesi /
  yeni makine) kullanıcı "3D STEP eskiden çalışıyordu, artık çalışmıyor" diyordu —
  uygulama çökmediği için sebep belirsizdi. Çözüm: yeni `_check_step_deps()` helper'ı
  (`cascadio`,`trimesh` import dener, eksikleri döndürür). `generate_combined_viewer`
  **başında** çağrılır; eksikse `pip install` komutu içeren açık `RuntimeError` fırlatır
  → GUI'de "HATA: …" olarak görünür (GeneratorThread yakalar). Sert hata yalnızca 3D
  sekmesi olan **birleşik görünümde**; 2D PCB viewer'ı (`generate_pcb_viewer`)
  etkilenmez (3D'ye ihtiyacı yok, eksikse extrude fallback'i korur). **PyInstaller exe**
  paketlerken `--collect-all cascadio --collect-all trimesh` eklenmeli (cascadio native
  `.pyd`/DLL gerektirir), yoksa exe'de yine eksik kalır.

- **3D bakır/silk dokusu bazı board'larda kayıyordu (v2.9.2)**: 3D'de board
  GÖVDESİ kesin `outline.points_mils`'ten üretildiği için hep doğru; ama bakır/
  pad/silk DOKUSU `_build_board_surface`'te kırılgan bir heuristikle hizalanıyordu:
  TOP SVG'sinde **renge göre** (`#C0A000`) board outline path'i aranıp `d`
  içindeki TÜM sayılar koordinat sayılarak bbox merkezi (`bcx,bcy`) bulunuyordu.
  Doku düzlemi tüm SVG kadar büyük (board ondan çok daha küçük ve genelde
  merkezde değil — `to_layer_svgs` board dışı fab/mekanik içerik de çiziyor), bu
  yüzden hizalama tamamen `bcx,bcy`'ye bağlı. Heuristik şu board'larda patlıyordu:
  (1) outline `#C0A000` değilse/mekanik katmandaysa/parçalıysa → fallback SVG-view
  merkezine düşüp doku onlarca mm kayıyor; (2) outline'da **yay (A)** komutu varsa
  yarıçap/flag'ler koordinat sanılıp bbox bozuluyor; (3) **viewBox origin'i 0
  değilse** (regex sadece w/h alıyordu) içerik kayıyor. Çözüm: outline artık
  **renge değil GERÇEK BOYUTA göre** eşleştiriliyor — `pcb.board.outline.
  bounding_box`'tan board genişlik/yükseklik (mm) `_build_board_surface`'e
  geçiriliyor, tüm path'lerin **uç-nokta** bbox'ı yeni `_svg_path_bbox()` parser'ı
  ile çıkarılıp (yay/eğri kontrol-noktaları ve flag'ler bbox'ı KİRLETMEZ) board
  boyutuna uyan path seçiliyor (`#C0A000` eşit adaylar arasında öncelikli). viewBox
  **origin'i (vbx,vby)** hem wrapper SVG'sine hem ofset matematiğine dahil edildi
  (`cx=vbx+vbw/2−bcx`, `cy=bcy−vby−vbh/2`). Boyut eşleşmezse #C0A000 ipucu, o da
  yoksa merkezleme fallback (log'a uyarı). Repodaki board'da çıktı birebir aynı
  (regresyon yok); kayan board'lar artık doğru hizalanır.

- **PCB kardeş klasördeyse bulunamıyordu (v2.9.1)**: PCB bulma kodu
  `Path(project_path).parent.rglob("*.PcbDoc")` ile yalnızca proje dosyasının
  klasörü (ör. `PCB PROJECT/`) altını tarıyordu. Ama PcbDoc çoğu projede proje
  dosyasının KARDEŞ klasöründedir (PrjPcb `PCB PROJECT/` içinde, PcbDoc `PCB/`
  içinde, PrjPcb referansı `..\PCB\x.PcbDoc`). Proje klasörü altını tarayan rglob
  bir üst dizindeki kardeş klasörü göremediği için "PCB dosyası bulunamadı"
  diyordu (şemalar bulunuyordu çünkü onlar PrjPcb `DocumentPath=` referanslarından
  `..\` çözümüyle okunuyor). Çözüm: SchDoc çözümünün PCB karşılığı olan yeni
  **`_resolve_pcbdoc_paths()`** helper'ı — önce PrjPcb metnindeki
  `DocumentPath=...PcbDoc` satırlarını okur (`\`→`/`, `..\` yukarı çıkışı,
  case-insensitive), bulamazsa proje klasörünü VE bir üst dizini (kardeş klasörler
  dahil) tarar. `collect_pcb_placement` ve `generate_pcb_viewer` artık kör rglob
  yerine bu helper'ı çağırır. Hardcoded path ayracı yok (cross-platform).

- **Doxygen dokümantasyonu (v2.9.0)**: `viewer.py` ve `gui.py`'deki tüm fonksiyon/sınıflara
  Doxygen formatında docstring eklendi (`@file`, `@brief`, `@details`, `@param`, `@return`).
  Mevcut Türkçe açıklamalar `@brief` + detay olarak korundu; eksikler eklendi. Kod
  **değişmedi** (yalnızca docstring'ler — AST karşılaştırmasıyla doğrulandı).
  - Üretici script (tek seferlik): `add_doxygen.py` — AST güdümlü, docstring bölgelerini
    alttan üste değiştirir, kodu korur, sık param adlarına otomatik açıklama verir.
  - **Doxyfile** + **mainpage.dox** eklendi. Doküman üretimi: `doxygen Doxyfile` →
    `docs/html/index.html`. Kritik ayar: `PYTHON_DOCSTRING = NO` (docstring'lerdeki
    @komutları yorumlansın), `OPTIMIZE_OUTPUT_JAVA = YES`, `EXTRACT_ALL = YES`.
  - Doxygen 1.9.8 ile uyarısız üretildi (23 HTML sayfası).

- **GUI yeniden tasarımı: Excel / Görüntüleyiciler ayrı gruplar + modern tema (v2.9.0)**:
  Önceden tüm dışa-aktarma butonları (Excel + HTML viewer'lar) tek karışık satırdaydı.
  Artık iki ayrı `QGroupBox` yan yana: **🖥 Görüntüleyiciler (HTML)** (Şematik Viewer,
  PCB Görüntüleyici, Şematik+PCB+3D ★, "tarayıcıda aç", şematik renk alt-grubu) ve
  **📊 Excel / Veri Dışa Aktarma** (MCU/IC ayar kartı, MCU Pin Listesi, IC Haritası,
  BOM, Pick&&Place, JSON). `gui.ui` baştan kurgulandı; tüm `objectName`'ler korundu.
  - **Tema**: `gui.py`'de `APP_STYLE` (modül sabiti) QSS koyu tema; `__init__`'te
    `self.setStyleSheet(APP_STYLE)`. Yuvarlatılmış gruplar/inputlar, kategori renkli
    butonlar (`cls` dinamik property → QSS `[cls="primary|view|excel|data|ghost"]`),
    scrollbar/tooltip/statusbar stilleri. Dinamik property'ler `stdset="0"` ile yazılır
    (QSS attribute selector'ı çalışsın diye).
  - **Yerleşim**: içerik bir `QScrollArea` (scrollContent/mainLayout) içinde → küçük
    ekranlarda taşma/binme olmaz. **Log paneli scroll DIŞINDA** (outerLayout, altta sabit,
    `maximumHeight 215`) → üretim ilerlemesi hep görünür. Kenar boşlukları outerLayout'ta
    (16px) hizalı.
  - **Buton metinleri** kısaltıldı (ör. "Şematik + PCB + 3D ★"); `_BTN_LABELS` (üretim
    sonrası metni geri yükler) gui.ui ile birebir eşitlendi. `&` için literal `&&`
    (Qt mnemonic) — "Pick && Place".

- **3D seçim focus efekti (v2.8.1)**: Komponent seçilince (tıkla/cross-probe) Altium gibi
  **board + diğer her şey kararır, seçili komponent parlak yeşil öne çıkar** (önceden yeşil
  board parlak kaldığı için seçim fark edilmiyordu). Tüm karartılabilir materyaller
  `dimReg` ile `dimMats`'e kaydedilir (her komponent mesh'i + board + edge + doku düzlemleri;
  orijinal renk/emissive/opacity saklanır). `setSel(d)`: önce hepsi eski haline döner; seçim
  varsa seçili `dDesig` materyalleri yeşil emissive (0x37b257) alır, diğerleri renk×0.20 +
  saydamlar opacity×0.42 ile kararır. Boş alana tıklayınca `setSel(null)` → karartma kalkar.

- **3D board yüzeyi: bakır + pad + silkscreen dokusu + gri arka plan (v2.8.0)**: 3D'de
  yeşil board üzerine gerçek bakır izler, altın pad'ler ve silkscreen yazıları bindirilir
  (Altium 3D viewer görünümü). Arka plan siyahtan griye (#9499a0) alındı.
  - **Doku** (`_build_board_surface`): mevcut katman SVG'leri (`to_layer_svgs`: TOP,
    TOPPASTE, MULTILAYER, TOPOVERLAY ve BOTTOM eşleniği) yeniden renklendirilip tek SVG'de
    birleştirilir → bakır yarı-saydam (`opacity 0.5`, beyaz knockout/clearance → `fill=none`
    ki yeşil board görünsün), SMD+TH pad altın, silk beyaz. **gzip+base64** ile gömülür
    (top ~349KB, bot ~155KB). **Yeni bağımlılık YOK** — tarayıcı SVG'yi raster'lar.
  - **Hizalama (kritik)**: SVG view'i board outline'ından farklı. Board outline SVG'de
    `data-feature="board-outline"` / renk `#C0A000` path olarak çizilir → bbox merkezi
    bulunur, 3D düzlemine `(sx−bcx, −(sy−bcy))` ile eşlenir (Y ters). Doku düzlemi tam SVG
    view boyutunda (`view_w×view_h`), merkezi `(view_w/2−bcx, −(view_h/2−bcy))`'ye konur →
    bakır/silk STEP modelleriyle ve board mesh'iyle birebir hizalanır.
  - **Render** (`addSurface`/`decompB64`): `DecompressionStream('gzip')` ile açılır →
    SVG data-URI → `Image` → canvas (2048px) → `CanvasTexture` → board üstüne/altına ince
    `PlaneGeometry` (z=±(th/2+0.02), `transparent`, `depthWrite:false`, polygonOffset).
    Alt yüz `rotation.x=π`. **Eski tarayıcı (DecompressionStream yoksa) → düz yeşil board.**
  - Doku düzlemi `pickList`'te değil → raycast/komponent seçimini etkilemez.

- **Gerçek STEP komponent modelleri (v2.7.0)**: 3D görünümde extrude gövdeler yerine
  gömülü STEP modelleri gerçek geometri + renkle çizilir (Altium online viewer gibi).
  - **STEP çıkarımı** (`_extract_step_models`, opsiyonel `cascadio`+`trimesh`): gömülü
    modeller `pcb.get_embedded_model_entries()` ile alınır (zlib sıkıştırılmış STEP),
    açılır, `cascadio.step_to_glb` ile mesh'e çevrilir, `trimesh` ile parçalara ayrılıp
    (vertex mm — glb **metre**, ×1000 — + face + parça rengi `baseColorFactor`) JSON'a
    serileştirilir. **cascadio yoksa boş döner → otomatik extrude gövdelere düşer.**
    Bu projede 14 model ~26k üçgen. **Bağımlılık üretim makinesinde gerekir** (üretilen
    HTML self-contained, mesh'ler gömülü). `pip install cascadio trimesh`.
  - **Model↔gövde eşleşmesi**: `body.model_id == model.id` (GUID). 75/88 gövde modelli,
    kalan 13'ü extrude. `_extract_3d` artık `models` (dedup geometri) + `placements`
    (model olan gövdeler) + `bodies` (modelsiz extrude) döndürür.
  - **Yerleşim (kritik, iterasyonla çözüldü)**: Altium'un `model_3d_rotz` konvansiyonu
    tutarsız (bazı komponentte komponent rotasyonunu içeriyor, bazısında değil) →
    rotz'a güvenmek yerine **outline-fit**: modele yalnızca TILT (`model_3d_rotx/y`,
    yüksekliği Z'ye getirir) uygulanır, sonra footprint uzun ekseni gövde **outline
    dikdörtgeninin açısına** döndürülür (`ang`, Python'da hesaplanır). Model XY-merkezi
    outline merkezine, tabanı standoff Z'ye hizalanır. Alt katmanda `scale.z=-1` ile
    aynalanır. Bu yöntem rotz tahminini tamamen ortadan kaldırır, tüm parçaları doğru
    konum/yönde oturtur (header'lar dik kenarda, regülatör/QFP/kristal yerli yerinde).
  - **Render** (`build_3d_html`/`buildModels`): her placement için iç grup (parça
    mesh'leri, paylaşılan değil — `BufferGeometry` + `MeshStandardMaterial` DoubleSide)
    + dış grup (in-plane açı + konum + alt-aynalama). Seçim çoklu-mesh: `meshByDesig`
    artık dizi, `pickList` ile raycast, highlight emissive parıltı (renk korunur).
    Alttan dolgu ışığı eklendi (Alt görünüm aydınlık). Çıktı ~4MB→~5MB.
  - **NOT**: board yüzeyinde bakır/silkscreen/pad henüz yok (sonraki aşama, yeni
    bağımlılık gerektirmez — mevcut katman SVG'leri board yüzeyine doku olarak).

- **3D görünüm eklendi (v2.6.0)**: Birleşik viewer'a "3D" sekmesi — board levhası +
  komponentlerin extrude 3D gövdeleri (Altium "basit 3D" gibi; STEP mesh değil).
  - **Veri** (`_extract_3d`): `pcb.board.outline.points_mils` (dış hat), katman
    yığınından kalınlık (`copper_thickness`+`diel_height`, ~1.6mm), `pcb.component_bodies`
    (88 adet; her birinde `outline` mutlak board koordinatında [mil], `overall_height_mils`,
    `standoff_height_mils`, `body_color_3d`, `component_index`→designator/layer). Koord mm'ye
    çevrilir, board merkezi orijine alınır. Varsayılan gri gövdeler designator önekine göre
    renklendirilir (U/Q siyah IC, C kahve, R koyu, Y/X gri vb.). `collect_pcb_layers` içinde
    çıkarılıp `result["board3d"]`'e konur (çift PcbDoc yüklemesi yok).
  - **Render** (`build_3d_html`): Three.js r128 ile sahne — board `ExtrudeGeometry` (yeşil
    FR4) + kenar çizgisi, her gövde `ExtrudeGeometry(poly, depth=h)`, üst/alt katmana göre
    z konumu. Özel orbit kontrol (up=+Y; üst/alt görünümler `el=0`'da kararlı, kutuplar
    kenar-bakışta — `el` ±1.48 kelepçeli). Sol-sürükle döndür, sağ-sürükle pan, tekerlek
    zoom. Butonlar: 3B / Üst / Alt / Döndür (otomatik). Raycaster ile tıkla→seç (emissive
    yeşil highlight) + cross-probe. Hover'da designator etiketi. WebGL yoksa hata mesajı.
  - **Offline/self-contained**: `three.min.js` (r128 UMD, ~589KB) gzip+base64 olarak
    viewer.py sonunda `_THREE_MIN_GZ_B64` sabitinde gömülü; `_three_js_source()` açar,
    `build_3d_html` HTML `<script>`'ine gömer (CDN/internet gerekmez, file:// çalışır).
    viewer.py ~160K→360K, çıktı HTML ~3.5MB→4MB büyür.
  - **Kabuk entegrasyonu** (`build_combined_shell`): `td_html`+`have_3d` parametreleri,
    3. iframe `frame-3d`, "3D" view-mode butonu, **tembel yükleme** (Three.js ağır → ilk 3D
    sekmesine geçişte `srcdoc` atanır). Cross-probe artık **üç yönlü**: `{{source:'sch'|'pcb'
    |'3d'}}` → kalan iki frame'e `postTo` ile yönlendirilir (guard'lı). 3D moduna geçince son
    seçili komponent 3D'ye iletilir.

- **Firefox'ta net highlight rengi çıkmıyor + komponent seçimi PCB'yi ekran dışına
  itiyor (Chromium'da sorunsuz)**: Kök sebep `getCTM()` farkı. Chromium'da katman
  gruplarında transform olmadığından `getCTM` = elemanın kendi transform'u (trace için
  birim); Firefox ise `getCTM`'e SVG'nin **CSS zoom transform'unu da katıyor**. Net
  klonlarına `transform=matrix(getCTM)` verildiğinde Firefox'ta kök CSS transform bir kez
  daha uygulanıp **çift-transform** oluyor → klonlar/kutu ekran dışına düşüyordu (net
  renklenmiyor, komponent odağı kayboluyor). Çözüm: **konumlandırmada getCTM tamamen
  kaldırıldı.** (1) `highlightNet`: klon `cloneNode` ile olduğu gibi kopyalanır (kendi
  rotate'ını korur, katman gruplarında transform yok → kök uzayda aynı konum). (2)
  `highlightComp` ve (3) `buildPadLabels`: konum/kutu artık `getBoundingClientRect`
  ekran kutusundan kendi `tx/ty/scale`'imizle kök uzaya çevrilerek bulunur
  (`uzay = (ekran - tx)/scale`, transform-origin:0 0). Bu yöntem tüm tarayıcılarda
  (Gecko/Blink/WebKit) aynı çalışır.
- **Firefox'ta (Gecko) PCB board'u ekran dışına kayıyor / boş görünüyor** (Chromium —
  Edge/Opera/Yandex — sorunsuz): Firefox `srcdoc` iframe'i ilk anda geçici/yanlış
  boyutta raporluyor; `fitView` o boyutta `tx/ty`'yi hesaplayıp board'u ekran dışına
  itiyordu (büyük pencerede tamamen boş, küçükte şans eseri görünür). `everFitted`
  (tek sefer fit) yanlış fit'i kilitliyordu. Çözüm: **`autoFit`** bayrağı — kullanıcı
  pan/zoom/seçim yapana kadar `ResizeObserver` her yeniden boyutlanmada `fitView`
  çağırır; Firefox iframe son boyutuna oturunca board kendiliğinden ortalanır. Kullanıcı
  tekerlek/sürükleme veya komponent/net seçimi yapınca `autoFit=false` olur (görünüm
  korunur). Konsol debug log'ları (`[popup]`, `[Comps]`) da temizlendi. Not: Firefox
  konsolundaki "source map" ve "FOUC" mesajları zararsızdır, sorunla ilgisi yoktur.
- **(1) Şematikten komponent seçince PCB kayıyor + seçili olmuyor; (2) net'e çift
  tıklayınca bakır yol da kararıyor**:
  (1) "Şematik" tek-panel modunda PCB paneli gizliyken cross-probe gelince
  `highlightComp` içinde `getBBox/getCTM` çalışmıyor (gizli SVG) → marker oluşmuyordu;
  ayrıca `focusBox` aşırı yakınlaşıp board'u kaydırıyordu. Çözüm: gizliyse komponent
  `pendingComp`'a alınır, PCB görünür olunca (Böl/PCB'ye geçince) **ResizeObserver**
  ilk sığdırmayı yapıp (`everFitted`) bekleyen komponenti vurgular; `focusBox` artık
  yalnızca komponent ekranda çok küçükse (<%5) hafifçe yakınlaşır (max 12), hep ortalar.
  (2) Pad etiketi okunurluğu için zemini 0.72'ye aydınlatınca net renkleri açık-gri
  zeminde sönük kalıyordu → zemin `grayscale(1) brightness(0.58)` (tam gri, biraz koyu)
  + net klon renkleri daha çok parlatıldı (`lift 0.22→0.42`); böylece seçili iz net
  biçimde öne çıkar (pad etiketleri beyaz olduğundan yine okunur).
- **PCB net highlight karartması çok koyuydu + pad pin no/net adı eksikti**:
  (1) Net highlight'ta katman filtresi `grayscale(1) brightness(0.4)` arka planı
  okunamaz yapıyordu → `grayscale(0.8) brightness(0.72)` ile aydınlatıldı (silk/
  komponent yazıları okunur, net rengi yine öne çıkar). (2) Pad'lerde pin no + net
  adı yoktu (Altium gösteriyor). Pad SVG elemanları `data-primitive="pad"`,
  `data-pad-number`, `data-net`, `data-component` taşıyor; toolbar'daki **Pin**
  butonu (`setPadLabels`) her benzersiz pad'in (komponent+pad-no) merkezine
  dünya-koordinatında iki satır text (pin no üstte, net adı altta; beyaz + siyah
  konturlu, zoom'la ölçeklenir) çizer. Tembel kurulur (ilk açılışta), net
  highlight'ın altında kalır. **Düzeltme (görünürlük):** dünya-boyutlu etiketler
  sığdır-zoom'da ~2px olup görünmüyordu → artık **varsayılan AÇIK**, sadece
  `scale >= 14` iken (yakınlaşınca) otomatik gösterilir/lazy kurulur, uzakta gizlenir
  (Altium gibi); ayrıca gizli katmandaki ilk pad elemanı `seen`'e eklenmeden atlanır
  ki pad'in görünür elemanı etiketlensin (önceden bazı pad'ler hiç etiketlenmiyordu).
  İnce ayar: pad yazısı çok büyüktü → `fs=min(small*0.40, max*0.24)` ile küçültüldü;
  net highlight aktifken `net-hl` her `updatePadLabelVis`'te en üste alınır ki seçili
  iz pad etiketlerinin ÜSTÜNDE kalsın (etiketler izi örtmesin).
- **Şematikte highlight kutusu sadece designator text'ini sarıyordu** (komponent
  gövdesi dışarıda kalıyordu) + Altium gibi **spotlight karartma** isteği:
  Şematik SVG'si komponent primitive'lerini designator'a göre gruplamıyor (sadece
  `<text>` elimizde). Çözüm: `_collect_data`'da her komponentin
  `SchComponentInfo.full_bounds_mils()` sınırı SVG-viewBox koordinatına çevrilip
  (`svg_x=mils_x/10`, `svg_y=viewBoxH−mils_y/10`) `SCH_BOXES[sheet_id][designator]`
  olarak viewer'a gömülür. Runtime'da `highlightComponent`, designator text'inin
  `getBBox()` (SVG-viewBox) ↔ `getBoundingClientRect()` (ekran→kanvas) eşlemesinden
  SVG→kanvas dönüşümünü türetip (`svgBoxToCanvas`) TAM kutuyu kanvasa taşır
  (full_bounds yoksa text bbox'a düşer). Spotlight: `#sch-hl-overlay`'e `fill-rule:
  evenodd` ile dev dış dikdörtgen + komponent kutusu deliği olan path (kanvas-uzayı,
  zoom'la hizalı) çizilerek komponent dışı %62 karartılır.
- **Şematik komponent vurgusu kırmızı dairesel "radar" uyarısıydı** (PCB'den farklı):
  `highlightComponent` tüm sayfaya `fitToSheet` yapıp eşleşen designator text'ine
  `createPulseRing` (kırmızı genişleyen halka) çiziyordu. PCB tarafıyla birleştirildi:
  designator text'lerinin birleşik bbox'ı KANVAS uzayında hesaplanıp `focusCanvasBox`
  ile KOMPONENTE yakınlaşılır (tüm sayfaya değil) ve PCB'deki `#hl-marker` ile aynı
  camgöbeği kutu + etiket çizilir. Kutu, arcLayer net render'larında silinmesin diye
  ayrı kalıcı overlay'e (`#sch-hl-overlay`, canvas içinde) eklenir; çizgi/yazı
  `updateSchMarkerMetrics` ile `1/scale` ölçeklenip her zoom'da ekran-sabit (~1.6px)
  kalır. `.comp-highlight` text pulse'u da kırmızıdan camgöbeğine çevrildi.
- **Komponent detay popup'ı görünümü kapatıyordu** + **seçince istenmeyen otomatik
  "Böl"**: Hem şematik (`build_html`) hem PCB (`build_pcb_html`) viewer'ında komponent
  detayı sağda yüzen popup'tı (`#comp-popup`, `position:fixed/absolute`), kanvası/board'u
  örtüyordu. Çözüm: popup sol `#sidebar` içine (arama + liste/katman bölümünün ALTINA)
  dock edildi — `flex-shrink:0`, üstte `#popup-resize` tutamacından dikey
  boyutlandırma, başlıktaki ok (`popup-collapse`) ile `collapsed` sınıfına simge
  durumuna küçültme. Ayrıca birleşik kabuktaki "xprobe gelince `setViewMode('both')`"
  otomatik geçişi KALDIRILDI: komponent seçilince görünüm modu (Şematik/Böl/PCB)
  değişmez, cross-probe arka planda çalışır.
- **PCB'de seçili komponent dolu kırmızı blok / sonra çok büyük kutu**:
  Eski highlight komponentin TÜM primitive'lerine (onlarca path/rect/line) ayrı
  ayrı `outline:3px red` uyguluyordu → yakınlaşınca dolu kırmızı blob. Çözüm:
  primitive'leri boyamak yerine komponentin birleşik sınır kutusunu hesaplayıp
  TEK temiz overlay kutu (`#hl-marker`, camgöbeği) + designator etiketi çiz, sonra
  `focusBox()` ile komponente otomatik pan/zoom. İKİ önemli ince nokta:
  (1) bbox `getBBox()` ile değil, `getCTM()` ile KÖK user-space'e dönüştürülerek
  birleştirilir (öğeler farklı transform altında olabilir). (2) Zoom CSS transform
  (`svg.style.transform=scale()`) ile yapıldığından `vector-effect:non-scaling-stroke`
  ÇALIŞMAZ — stroke viewBox birimi (mm) sayılıp CSS scale ile büyür, dev cam­göbeği
  disk oluşur. Bunun yerine stroke/rx/font `1/scale` ile ölçeklenir
  (`updateMarkerMetrics`, her `applyTransform`'da çağrılır) → her zoom'da ekranda
  sabit ~1.6px ince kutu. Pay küçük tutulur (sıkı kutu).
- **Birleşik görünümde iki panel de boş** (`file://` ile açınca): İKİ bağımsız
  hata. (1) İç viewer HTML'leri kabuğun satır-içi `<script>`'ine `json.dumps` ile
  gömülüyordu; iç viewer'ların `</script>`'i (ve html2canvas CDN referansı) kabuk
  script'ini erken kapatıyor → `const SCH_HTML="..."` yarıda kesiliyor → `loadFrame`
  çalışmıyor → iframe boş. Çözüm: gömülü JSON'da `</` → `<\/`. (2) iframe'ler
  Blob URL ile yükleniyordu; `file://` sayfasının origin'i "null" olunca
  `blob:null/...` güvenilmez sayılıp Chrome tarafından engelleniyor. Çözüm:
  `iframe.srcdoc` (üst sayfanın origin'ini miras alır, `file://` altında çalışır).
  İkisi birlikte gerekli — biri tek başına yetmez. (Headless Chromium ile
  doğrulandı: embedding düzeltilse bile blob `contentDocument:null` veriyordu.)
- **PCB ilk açılışta/Sığdır'da ekran dışına kayıyor**: `#pcb-svg`'de `width`/
  `height` yoktu; tarayıcı SVG'yi containing-block genişliğinde render edip
  `fitView()`'in `VIEW_W×VIEW_H` px varsayımını bozuyordu (SVG dev görünüp kayıyor,
  kullanıcı uzaklaştırıp yakınlaştırmak zorunda kalıyordu). Çözüm: `width="{view_w}"
  height="{view_h}"` (=viewBox mm) ekle + ilk sığdırmayı layout oturduktan sonra
  yap (`requestAnimationFrame` + `getBoundingClientRect` boyut kontrolü).

- **Dikey pin adları** (STM32 gibi IC'lerde yatay render ediliyordu): altium_monkey
  **2026.6.21**'de düzeltildi — artık `transform="rotate(-90 ...)"` ile doğru
  açıda render ediliyor. Viewer bu transform'ları olduğu gibi koruyor, kod
  değişikliği gerekmedi. **Önerilen minimum altium_monkey sürümü: 2026.6.21.**
- **Multi-part komponentler** (IC2A/IC2B/IC2C): designator birleştirme +
  `resolveCompDesignator()` ile çözüldü (bkz. yukarıdaki ilgili bölümler).
