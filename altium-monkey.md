---
paths:
  - "viewer.py"
---

# altium_monkey API Notları

`altium_monkey` 2026.5.29 — Eli Hughes / Wavenumber'ın Altium şematik ve PCB
dosyalarını Python'da parse etmek için açık kaynak kütüphanesi.

## Doğru Import Yolları

```python
from altium_monkey.altium_prjpcb import AltiumPrjPcb
from altium_monkey.altium_schdoc import AltiumSchDoc
```

`altium_monkey` namespace'inden direkt import etme — submodülünden import
zorunlu.

## AltiumPrjPcb

```python
project = AltiumPrjPcb(path)         # constructor; .load() classmethod YOK
project.get_reachable_schdoc_paths() # tüm sayfaların Path listesi
project.get_schdoc_paths()           # alternatif
project.get_pcbdoc_paths()
project.parameters                   # PROPERTY, parantezsiz
```

## AltiumSchDoc

```python
schdoc = AltiumSchDoc(sch_path)
schdoc.to_svg()                      # SVG string döner
schdoc.to_svg(project_parameters=...)# bazı sürümlerde TypeError verir
                                     # try/except ile parametresiz fallback yap

schdoc.get_components()              # list of SchComponentInfo
schdoc.get_net_labels()              # list of SchNetLabelInfo
schdoc.get_ports()                   # list of SchPortInfo (en yaygın net kaynağı)
schdoc.get_power_ports()             # list
schdoc.get_sheet_symbols()           # list of SchSheetSymbolInfo (block'lar)
schdoc.get_cross_sheet_connectors()  # genelde boş bu projelerde
schdoc.get_harness_connectors()      # genelde boş
schdoc.get_labels()                  # generic AltiumSchLabel (yorum metni vs.)
                                     # net DEĞİL — kullanma
```

## SchComponentInfo

```python
c.designator        # "U5", "R156" vs.
c.comment           # "STM32F405RGT6" (genelde value/Comment alanı)
c.value             # alternatif değer alanı
c.description       # uzun açıklama
c.footprint         # "QFN-48"
c.library_ref       # symbol ref
c.parameters        # list of AltiumSchParameter (bkz. aşağı)
c.pins              # pin objeleri
c.unique_id
c.location          # CoordPoint
```

## AltiumSchParameter (KRİTİK)

`component.parameters` listesinin elemanları. Manufacturer, Part Number,
Supplier, Stock, Pricing, RoHS gibi tüm meta veriler burada.

```python
param.name          # parametre adı: '.Creator', 'Manufacturer', 'Stock'
param.text          # parametre DEĞERİ: 'F:TALI', 'Microchip', '3226'
param.is_hidden     # bool
```

**`.value` attribute'u YOK — değeri okurken `.text` kullan.** Daha önce iki
kez buradan yandık. Doğru pattern:

```python
# DOĞRU
for param in c.parameters:
    name = getattr(param, "name", None)
    val = getattr(param, "text", None)  # value değil text!
    if name and val:
        result[str(name)] = str(val)
```

`viewer.py`'deki `get_component_parameters(c)` helper'ı bunu zaten yapıyor —
yeni parameter okuma kodu ekleyeceksen aynı pattern'ı kullan.

## SchPortInfo (overbar notation — KRİTİK)

```python
p.name              # 'ADC1_C\S\' gibi olabilir
p.io_type
p.location
p.connection_points
p.width
p.unique_id
```

**Active-low sinyaller backslash overbar notation kullanır**:

| Python repr     | Gerçek string | SVG'de render | Anlamı |
|-----------------|---------------|---------------|--------|
| `'ADC1_C\\S\\'` | `ADC1_C\S\`   | `ADC1_CS` (üst çizgili) | `ADC1_CS̄` (active-low CS) |

SVG'de overbar **görsel çizgi** olarak çizilir, text'in kendisi backslash'siz
görünür. Bu yüzden JS tarafında `netNameSet.has(svgText)` match'i için Python
tarafında backslash'leri **atmak zorunda**.

`viewer.py`'deki `get_obj_text()` helper'ı `.replace("\\", "")` yapıyor — yeni
text okuyan kod ekleyeceksen aynı normalize'ı uygula.

## SchSheetSymbolInfo (block / hierarchical sheet)

```python
ss.file_name             # 'BRK-211-2600009_D000.SchDoc' (hedef dosya)
ss.child_filename        # aynı, fallback
ss.designator            # 'U_BRK-211-2600005_D000'
ss.sheet_name_text       # designator ile aynı, fallback
ss.entries               # sheet entry'leri (pin'ler)
ss.unique_id
ss.record
```

Block navigation için `file_name`'in `.SchDoc` uzantısını at, sheet adı olarak
match et. `_collect_data()` zaten bunu yapıyor.

## Yaygın Sorun Patternleri

- **`to_svg()` TypeError**: Bazı altium_monkey sürümlerinde signature
  `to_svg(project_parameters=...)` ister. `try/except TypeError` ile iki
  imzayı da dene (`viewer.py`'de mevcut).
- **Boş listeler**: Cover page, mekanik sayfa gibi şeylerde `get_components()`
  veya `get_sheet_symbols()` boş döner. `try/except` ile sar.
- **Generic labels ≠ net labels**: `get_labels()` text annotation döndürür
  (yorum, "APPROVAL" gibi). Net adı toplama için kullanma.

## Netlist — Gerçek Pin→Net Bağlantısı (KRİTİK)

`get_ports()`/`get_net_labels()` sadece net İSİMLERİNİ verir, hangi pin'in
hangi net'e bağlı olduğunu **vermez**. AI'nın "STM32 PB15 hangi net'e gidiyor?"
sorusunu cevaplayabilmesi için gerçek elektriksel netlist gerekir.

Çözüm: `compile_netlist()` — multi-sheet derleme, cross-sheet port/label
eşleştirmesini otomatik çözer.

```python
from altium_monkey.altium_netlist_compilation import compile_netlist

# schdocs: AltiumSchDoc objelerinin listesi (tüm proje sayfaları)
# project: AltiumPrjPcb (cross-sheet hierarchy için, opsiyonel ama önerilir)
nl = compile_netlist(schdocs, project)
raw = nl.to_json()    # yapısal dict — WireList string parse ETME
# nl.to_wirelist()    # alternatif: WireList string formatı
```

### to_json() şeması (altium_monkey.netlist.a0)

```python
{
  "schema": "altium_monkey.netlist.a0",
  "components": [{"designator", "value", "footprint", "library_ref",
                  "description", "parameters"}],
  "nets": [{
    "uid", "name", "auto_named",     # auto_named: Altium otomatik isim verdiyse
    "source_sheets": [...],          # net'in göründüğü sayfalar
    "terminals": [                   # ← ASIL DEĞER: pin bağlantıları
      {"designator": "U5", "pin": "11", "pin_name": "CS", "pin_type": "..."}
    ],
    "graphical": {...}, "aliases": [...], "endpoints": [...],
    "hierarchy_paths": [...]         # multi-sheet hierarchy (varsa)
  }]
}
```

Her net'in `terminals` listesi = o net'e bağlı tüm pinler. Bu, "pin → net" ve
"net → pinler" eşlemesinin ikisini de kurar. `viewer.py`'deki
`compile_project_netlist()` bunu sarmalıyor, hata olursa None döner (JSON yine
de net özetiyle üretilir).

### NetlistOptions

`compile_netlist(schdocs, project, options=...)` — options None ise serbest
doküman varsayılanları kullanılır. Proje ayarlarından yüklemek için
`NetlistOptions.from_prjpcb()` (sürümlere göre konumu değişebilir, import
yolunu çalıştığın sürümde doğrula).

### Pin objesi alternatifi (netlist gerekmiyorsa)

```python
schdoc.get_all_pins()                  # list[SchPinInfo], tüm pinler
schdoc.get_pins_for_component("U5")    # tek komponentin pinleri
# SchPinInfo: component_designator, designator (pin no), name (pin adı,
#             örn "PB15"), connection_point, electrical (pin tipi), location
```

`connection_point` koordinatı ile wire/junction koordinatlarını eşleştirerek
manuel bağlantı çıkarımı da yapılabilir ama `compile_netlist()` bunu zaten
doğru yapıyor — manuel koordinat eşleştirme yapma.

**Tam PCB render (görüntüleyici için)**: `pcb.to_layer_svgs(options=...)` tüm
katmanları ayrı SVG olarak döndürür (dict: {layer_name: svg}). Her SVG'de
**`data-component="<designator>"`** ve `data-net-index=` metadata'sı var —
cross-probe için altın. `data-component` doğrudan designator (örn "U2", "J5").
`PcbSvgRenderOptions(visible_layers=[PcbLayer.TOP, ...], layer_colors=...,
show_board_outline=True, mirror_x=...)`. visible_layers STRING değil PcbLayer
enum bekler (`from altium_monkey.altium_record_types import PcbLayer`).
Tüm katmanlar aynı viewBox'ı paylaşır (sabit render alanı, panel boyutu olabilir
196×293mm ama gerçek board alt-bölge — komponentler doğru yerde, pan/zoom yeterli).
Devasa katmanlar olabilir (MECHANICAL16 24MB) — boyut limiti koy.

## PcbDoc — PCB Okuma (from_file ZORUNLU)

**KRİTİK**: SchDoc constructor parse eder ama PcbDoc constructor ETMEZ.
`AltiumPcbDoc(path)` boş obje döndürür (components/nets hepsi []). PCB'yi
parse etmek için `AltiumPcbDoc.from_file(path)` kullan:

```python
from altium_monkey.altium_pcbdoc import AltiumPcbDoc
pcb = AltiumPcbDoc.from_file(path)   # constructor DEĞİL, from_file
pcb.components          # list[AltiumPcbComponent], from_file sonrası dolu
pcb.nets                # list[AltiumPcbNet]
pcb.differential_pairs  # list — high-speed çiftler
```

Komponent objesi: `designator`, `footprint`, `layer` ("TOP"/"BOTTOM"),
`rotation` (string olabilir, float'a çevir), `description`, `parameters` (dict).

Konum (cross-probe için):
```python
x_mil, y_mil = pcb.get_component_pnp_position_mils(index, origin_relative=False)
# index = components listesindeki sıra. 1 mil = 0.0254 mm.
```

**Board sınırı**: `to_board_outline_svg()` GÜVENİLMEZ — bazen panel/mekanik
katman çiziyor, komponent koordinatlarıyla hizasız (viewBox 196×293mm ama
gerçek board 55×40mm gibi). Bunun yerine:
```python
bb = pcb.board.outline.bounding_box   # (left, bottom, right, top) mil
```
Komponentleri bu bb'ye göre normalize et.

**Y EKSENİ**: Altium Y yukarı artar, SVG/HTML Y aşağı artar. Mini harita için
Y'yi ters çevir: `y_svg = (by_max - y_altium)`.

`viewer.py`'deki `collect_pcb_placement()` bunların hepsini yapar. PCB parse
maliyetli (16MB dosya) — sadece HTML viewer için (`_collect_data(with_pcb=True)`),
JSON/BOM modunda atlanır.

## Multi-Part Komponentler (ÖNEMLİ)

Büyük IC'ler (STM32, i.MX, FPGA) şemada birden çok parçaya bölünür: tek
designator "IC2" ama çizimde IC2A / IC2B / IC2C diye görünür. `get_components()`
her parçayı AYRI obje döndürür — bu yüzden ham listede "U2" 15 kez görünebilir.

Parça tespiti:
```python
rec = c.record
part_id = rec.current_part_id      # 1, 2, 3... (Altium harfe çevirir: 1=A, 2=B)
part_count = rec.part_count        # toplam parça sayısı
# DİKKAT: part_count GÜVENİLMEZ — tek dirençte bile 2 dönebiliyor.
# Gerçek multi-part göstergesi: aynı designator'ın birden fazla yerde olması.
unique_id = c.unique_id            # tüm parçalar aynı unique_id'yi paylaşır
```

`_collect_data` parçaları designator'a göre TEK komponente birleştirir
(`merged` dict), her parçanın `placements` listesini (sheet_id, sheet_name,
part_id) korur. JSON ve HTML'de komponent tek görünür ama hangi sayfalarda
parçası olduğu bilinir.

SVG'de designator "IC2A" diye yazılır (designator + part harfi). Viewer'da
tıklama için `resolveCompDesignator()` JS fonksiyonu suffix'i ("A","B") atıp
taban designator'a ("IC2") eşleştirir. Bu olmadan multi-part IC'lerin
designator'ına tıklanamaz.

## AltiumDesign — Üst Seviye API (BOM / PnP / Varyant)

altium_monkey 2026.6.x+ sürümünde `AltiumDesign` üst seviye orkestratör sınıfı
var. `AltiumPrjPcb` + her `AltiumSchDoc` + `compile_netlist` zincirini tek
çağrıya indirir, üstüne BOM/PnP/varyant ekler. Eski sürümlerde yok — import'u
try/except ile sar.

```python
from altium_monkey.altium_design import AltiumDesign

design = AltiumDesign.from_prjpcb(path)   # veya from_schdoc / from_pcbdoc

design.get_variants()        # list[str] — tasarım varyantları
design.to_bom(variant=None)  # list[dict] — malzeme listesi (aşağıda)
design.to_pnp(variant=None, units="mm")  # list[PnpEntry] — yerleşim (PCB gerekir)
design.to_netlist()          # Netlist — compile_netlist'in muadili (cached)
design.get_net(name)         # tek net sorgusu
design.to_json()             # tüm tasarım, hazır JSON dict
design.to_wirelist()         # WireList string
```

### to_bom() dönüş yapısı

```python
[{
  "designator": "R1", "value": "10k", "footprint": "...",
  "library_ref": "...", "description": "...",
  "parameters": {"Manufacturer": "...", "MPN": "...", ...},
  "dnp": False,   # bu varyantta Do Not Populate mı
}]
```

BOM şematikten gelir (PCB değil) — çünkü varyantlar ve parametreler şematik
seviyesinde tanımlı.

### to_pnp() → PnpEntry objesi

`PnpEntry` dataclass'ının `.to_json()` metodu var. Alanlar: `designator`,
`comment`, `layer` ("top"/"bottom"), `footprint`, `center_x`, `center_y`
(units cinsinden), `rotation` (derece), `description`, `parameters`.

**PCB dosyası yoksa `ValueError` atar** — try/except ile sar, "PCB yok" diye
geç. `units="mm"` veya `units="mils"`.

`viewer.py`'deki `collect_design_extras()` bunları sarmalıyor, her biri için
graceful fallback yapıyor (eski sürüm / PCB yok / hata → boş döner, uygulama
çalışmaya devam eder). `generate_bom_csv()` ve `generate_pnp_csv()` CSV
export için bunu kullanır.

## Diagnostic Pattern

Yeni bir API alanı eksik veya farklı davranıyorsa şu pattern'la keşif yap:

```python
schdoc = AltiumSchDoc(sch_path)
objs = schdoc.SOMEMETHOD()
if objs:
    o = objs[0]
    print("Tip:", type(o).__name__)
    for a in sorted(x for x in dir(o) if not x.startswith('_')):
        val = getattr(o, a, None)
        if not callable(val):
            print(f"  .{a} = {val!r}")
```
