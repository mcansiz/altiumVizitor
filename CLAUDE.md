# Schematic Viz Generator

Altium şematik projelerini interaktif HTML viewer'a dönüştüren PyQt5 uygulaması.
Wavenumber'ın ticari "viz sch 1.0" ürününün açık-kaynak alternatifi.
[altium_monkey](https://github.com/wavenumber-eng/altium_monkey) kütüphanesi
(Eli Hughes / Wavenumber) üzerine kurulu.

**Mevcut sürüm**: `APP_VERSION` sabiti **`viewer.py`'de** tutulur (şu an 2.9.30);
`gui.py` oradan import eder (v2.9.29'da taşındı — HTML çıktıları da sürümü
gösterebilsin diye, tek kaynak). Yeni özellik/düzeltme ekleyince bu sabiti
güncelle (semver: major.minor.patch). Sürüm pencere başlığında, alt durum
çubuğunda, üretim log'unun başında, "Hakkında" diyaloğunda ve birleşik HTML'in
sağ üst rozetinde (`{proje} · v{APP_VERSION}`) görünür.

## Üç Dosya

- **`viewer.py`** — Tüm üretim mantığı. Ortak `_collect_data()` helper'ı sayfaları,
  netleri, komponentleri, sheet symbol'leri (block'ları), netlist'i (pin→net)
  ve BOM/PnP/varyant verilerini toplar. Altı public üretim fonksiyonu:
  - `generate_viewer(...)` → tek dosya interaktif HTML (~30 MB, gömülü SVG'lerle)
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
  - `generate_pcb_viewer(...)` → tam ekran PCB görüntüleyici HTML (Altium benzeri).
    `collect_pcb_layers()` ile tüm katmanlar SVG render edilir (TOP/BOTTOM bakır,
    iç katmanlar MID1-8, silkscreen, pasta, lehim, mekanik, drill). Sidebar'dan
    katman aç/kapa, pan/zoom, komponente tıkla → cross-probe popup (şematik
    değer/açıklama + PCB konum/footprint). **Bakır yol/net highlight**: render
    SVG'sindeki bakır elemanlarda `data-net` (net adı) bulunur; bir iz/pad'e ÇİFT
    tıklayınca o net'in tüm elemanları (tüm katmanlarda) KENDİ KATMAN RENKLERİNDE
    (Top kırmızı, Bottom mavi, plane'ler yeşil — Altium gibi; her klonun rengi
    computed style'dan alınıp hafif parlatılır) klonlanıp en üste çizilir; board'un
    kalanı `grayscale(1) brightness(0.4)` CSS filtresiyle grileşip kararır
    (klonlar `getCTM()` ile kök uzaya taşınır). Hover'da net adı, Esc ile temizleme.
    `data-component` metadata'sı designator verir. Büyük katmanlar (>8MB) atlanır. ~30-40MB çıktı.
    `#pcb-svg`'ye açık `width`/`height` (=viewBox mm) verilir; yoksa SVG containing
    block genişliğini doğal boyut sanar, `fitView()` matematiği bozulur, board ilk
    açılışta ekran dışına kayar (bkz. Çözülen Sorunlar). İlk sığdırma iframe layout'u
    oturduktan sonra çalışır (`requestAnimationFrame` + boyut kontrolü).
  - `generate_combined_viewer(...)` → şematik + PCB tek HTML'de yan yana,
    çift yönlü cross-probe. İki viewer iframe içinde izole (her iframe'in HTML'i
    kabuğa JSON string olarak gömülür, runtime'da `iframe.srcdoc` ile yüklenir),
    `postMessage` ile haberleşir: birinde komponente tıkla → diğeri o komponenti
    gösterir. Ortada sürüklenebilir ayraç. Topbar'da görünüm modu düğmeleri
    **Şematik / Böl / PCB / 3D** (klavye: 1/2/3/4, odak kabuktayken).
    **Açılış modu SADECE Şematik** (v2.9.22+): PCB ve 3D iframe'leri tembel
    yüklenir — ilk o moda geçişte gzip'ten çözülür, o sırada "PCB/3D
    hazırlanıyor…" spinner'ı görünür (`.pane-loading`). Şematikte komponent
    seçilse bile PCB arka planda YÜKLENMEZ (`curMode` kontrolü); son seçim
    `lastSel`'de saklanır, moda geçince `repostSel` ile iletilir → açılışta
    ekstra yük yok, cross-probe kaybolmaz. Pane etiketleri (ŞEMATİK/PCB
    yazıları) v2.9.27'de tamamen kaldırıldı. Komponent seçilince mod
    DEĞİŞMEZ (cross-probe arka planda çalışır). ~45-50MB çıktı.
    `build_combined_shell()` kabuk sayfayı, köprü için her iki builder'a eklenen
    `crossProbeOut()` + message listener'ı kullanır.
    **İKİ KRİTİK GÖMME KURALI** (bkz. Çözülen Sorunlar): (1) iç HTML JSON'unda
    `</` → `<\/` yapılır, yoksa iç viewer'ların `</script>`'i kabuğun satır-içi
    script'ini erken kapatır → paneller boş. (2) `srcdoc` kullanılır, Blob URL
    DEĞİL — `file://` altında origin "null" olur, `blob:null/...` engellenir.
- **`gui.py`** — PyQt5 ana pencere. `GeneratorThread` ile non-blocking üretim,
  `mode='html'|'json'|'bom'|'pnp'|'icmap'|'mcupin'|'pcbview'|'combined'` ile
  sekiz ayrı buton. `GeneratorThread.progress_signal(int percent, str label)`
  üretim ilerlemesini taşır → `logGroup`'taki `progressBar`'a yansır. `percent < 0`
  = belirsiz/marquee (süresi kestirilemeyen adım, örn. PCB `to_layer_svgs()`).
  Üretici fonksiyonlar `progress=` callback'i alır (combined/pcbview/html).
- **`gui.ui`** — Qt Designer XML form. `uic.loadUi('gui.ui')` ile yüklenir.

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

## Geliştirme Komutları

```bash
# Bağımlılıklar (Python 3.12)
py -3.12 -m pip install PyQt5 altium-monkey openpyxl
# 3D STEP modelleri için ZORUNLU (yoksa birleşik görünüm üretimi hata verir):
py -3.12 -m pip install cascadio trimesh numpy

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
- **Sol panel katlanabilir** (v2.9.23+): sağ üst köşedeki küçük ◂/▸ ok butonu
  veya `B` kısayolu; kapalıyken 26px şerit kalır. Komponent popup'ı (panele
  dock'lu) açılırsa veya `/` ile arama açılırsa panel otomatik açılır. Durum
  `localStorage`'da (`schviz-ui` anahtarı) hatırlanır; file:// altında storage
  kısıtlıysa try/catch ile sessizce atlanır.
- Sol panel sekmeleri: **Nets** (power=orange, ground=green, signal=gray) ve **Comps**
- **Net tipi filtre çipleri** (v2.9.25+): Nets sekmesinde Tümü/Güç/GND/Sinyal;
  aramayla birlikte çalışır, Comps sekmesinde gizlenir.
- **Arama katlanabilir** (v2.9.22+): "▸ Ara" başlığı altında, varsayılan KAPALI;
  `/` açar+odaklar, `Esc` kapatır (kapatınca filtre temizlenir). **Enter** görünen
  listedeki ilk sonucu seçer; sonuç yoksa "eşleşen yok" mesajı.
- **Şematik metinleri PDF gibi seçilebilir/kopyalanabilir** (v2.9.22+):
  `.sheet-body svg text {user-select:text}`; fare metin üzerindeyken pan
  BAŞLAMAZ (native seçim çalışır), boş alanda pan normal. Sürükleyip seçim
  yapıldıysa click handler'ları aksiyonu tetiklemez
  (`window.getSelection()` kontrolü). Tıklanabilir sınıflar pointer imlecini
  korur (özgüllük: `.sheet-body svg text.clickable-net {cursor:pointer}`).
- SVG text'leri tıklanabilir: net adı → bağlantı yayları; block (sheet symbol)
  → hedef sayfaya navigate; komponent designator → detay popup
- **Şematikte designator tıklamasında görünüm KAYMAZ** (v2.9.24+):
  `highlightComponent(desig, sheetId, focus=false)` — sadece kutu çizilir.
  Arama/Comps listesi ve cross-probe `focus=true` (varsayılan) ile ortalar.
- **Boş alana tıklama komponent seçimini iptal eder** (v2.9.24+): pan hareketi
  (`panMoved`, >3px eşiği), metin seçimi ve tıklanabilir öğeler hariç.
- **Hover bilgi balonu** (v2.9.25+): `#svg-tip` — komponentte değer+açıklama,
  net'te bağlantı sayısı+tipi, block'ta hedef; altında eylem ipucu.
- **Toolbar** (v2.9.25+): **Sayfa… açılır menüsü** (sayfaya git), **+/−** zoom,
  **Tümü** (tüm sayfaları sığdır, `fitAll`), anlık renk picker'lar (sayfa-arası
  ve sayfa-içi; seçim `localStorage`'a kaydedilir), PNG export, Reset, Clear
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
  `B` sol paneli gizle/göster, `0` reset view, `F` fit last, `Esc` clear
- PyInstaller paketi için gui.ui dosyası `sys._MEIPASS` üzerinden bulunur
  (gui.py'de fonksiyonla)

### PCB Viewer'a taşınan UX özellikleri (v2.9.26+)

Şematik tarafındaki desenler `build_pcb_html`'e de uygulandı:
- Katlanabilir sol panel: `#sb-toggle` ok butonu (h2'nin sağında), `B` kısayolu,
  `localStorage` alanı `pcbSidebar` (şematikten bağımsız). `showComp()` popup
  açarken paneli otomatik açar.
- Katlanabilir arama (`#search-box.collapsed`, varsayılan kapalı, `/` açar,
  `Esc` kapatır).
- Toolbar +/− zoom butonları (`zoomBy`, autoFit=false yapar).
- **Boş alana tek tıklama net highlight'ını temizler**: SVG içinde
  data-component/data-net taşımayan hedef VEYA SVG dışındaki `#canvas-wrap`
  zemini; `moved` bayrağı pan'i ayırt eder. Esc de çalışmaya devam eder.

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
