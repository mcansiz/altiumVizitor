"""AST güdümlü Doxygen docstring ekleyici.
Kodu değiştirmez; yalnızca docstring bölgelerini ekler/değiştirir."""
import ast
import os
import sys

COMMON_PARAMS = {
    "pcb": "AltiumPcbDoc PCB nesnesi",
    "log": "Log mesajı callback'i (str alır)",
    "progress": "İlerleme callback'i (yüzde:int, etiket:str)",
    "project_path": "Altium proje dosyası (.PrjPcb) yolu",
    "project": "Altium proje nesnesi / yolu",
    "schdoc_paths": "Şema (.SchDoc) yolları listesi",
    "output_path": "Çıktı dosyası yolu",
    "output": "Çıktı dosyası yolu",
    "out_path": "Çıktı dosyası yolu",
    "view_w": "Görüntü genişliği (mm)",
    "view_h": "Görüntü yüksekliği (mm)",
    "all_layers": "Katman adı → SVG string sözlüğü",
    "layers": "Katman listesi",
    "color": "Renk (hex, ör. #RRGGBB)",
    "colors": "Renk ayarları",
    "td_html": "3B görünümün iç HTML'i",
    "have_3d": "3B görünüm mevcut mu (bool)",
    "inter_color": "Sayfalar arası bağlantı rengi (hex)",
    "intra_color": "Sayfa içi bağlantı rengi (hex)",
    "main_ic": "Ana işlemci (MCU) designator'ı",
    "main_ics": "Ana işlemci designator listesi",
    "min_pin": "Minimum pin sayısı eşiği",
    "min_pins": "Minimum pin sayısı eşiği",
    "mode": "Üretim modu (html/json/bom/pnp/icmap/mcupin/pcbview/combined)",
    "msg": "Mesaj metni",
    "percent": "Yüzde değeri (0-100)",
    "label": "Durum etiketi metni",
    "which": "Hedef seçici",
    "data": "Veri sözlüğü",
    "html": "HTML metni",
    "svg": "SVG metni",
    "name": "Ad",
    "designator": "Komponent designator'ı",
    "timestamp": "Zaman damgası metni",
    "svg_str": "SVG metni",
    "project_name": "Proje adı",
    "inter_sheet_color": "Sayfalar arası bağlantı rengi (hex)",
    "intra_sheet_color": "Sayfa içi bağlantı rengi (hex)",
    "variant": "Varyant adı",
    "net": "Net adı",
    "net_type": "Net tipi",
    "net_list": "Net listesi",
    "main_designators": "Ana işlemci designator listesi",
    "mcu_designator": "MCU designator'ı",
    "with_pcb": "PCB dahil mi (bool)",
    "have_pcb": "PCB mevcut mu (bool)",
    "sch_html": "Şematik iç HTML'i",
    "pcb_html": "PCB iç HTML'i",
    "d3d": "3B veri sözlüğü (board3d)",
    "max_layer_mb": "Katman başına maksimum boyut (MB)",
    "include_power": "Güç netlerini dahil et (bool)",
    "components": "Komponent listesi",
    "comp_info": "Komponent bilgi sözlüğü",
    "pin_name": "Pin adı",
    "pin_names": "Pin adları listesi",
    "units": "Birim",
    "opacity": "Saydamlık (0-1)",
    "white_none": "Beyaz knockout'ları şeffaf yap (bool)",
    "copper_key": "Bakır katman anahtarı",
    "paste_key": "Lehim pastası (pad) katman anahtarı",
    "silk_key": "Silkscreen katman anahtarı",
    "self_desig": "Komponentin kendi designator'ı",
    "success": "İşlem başarılı mı (bool)",
    "message": "Mesaj metni",
    "schdoc": "Şema (.SchDoc) nesnesi",
    "schdocs": "Şema nesneleri listesi",
    "target_names": "Hedef ad listesi",
    "default": "Varsayılan değer",
}

CONTAINER = (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)


def returns_value(node):
    """Bu fonksiyonun (iç içe fonksiyonlara inmeden) değer döndürüp döndürmediği."""
    found = [False]

    def visit(n, top=False):
        for child in ast.iter_child_nodes(n):
            if isinstance(child, ast.Return) and child.value is not None:
                found[0] = True
            elif isinstance(child, CONTAINER):
                continue  # iç fonksiyona inme
            else:
                visit(child)
    visit(node)
    return found[0]


def func_params(node):
    a = node.args
    names = []
    for grp in (getattr(a, "posonlyargs", []), a.args, a.kwonlyargs):
        for arg in grp:
            if arg.arg not in ("self", "cls"):
                names.append(arg.arg)
    if a.vararg:
        names.append("*" + a.vararg.arg)
    if a.kwarg:
        names.append("**" + a.kwarg.arg)
    return names


def build_doc(indent, brief, details, params, has_ret):
    pad = " " * indent
    out = [pad + '"""@brief ' + brief]
    if details:
        out.append(pad.rstrip() if False else pad)
        for dl in details:
            out.append((pad + dl).rstrip())
    if params or has_ret:
        out.append(pad)
    for p in params:
        base = p.lstrip("*")
        desc = COMMON_PARAMS.get(base, "")
        out.append((pad + "@param " + p + (" " + desc if desc else "")).rstrip())
    if has_ret:
        out.append(pad + "@return Üretilen sonuç.")
    out.append(pad + '"""')
    return out


def process(path):
    src = open(path, encoding="utf-8").read()
    lines = src.split("\n")
    tree = ast.parse(src)

    targets = []  # (start_line, end_line_or_None, new_lines)

    # --- modül docstring → @file başlığı ---
    mod_doc = ast.get_docstring(tree, clean=False)
    file_hdr = FILE_HEADERS[os.path.basename(path)]
    if mod_doc is not None and isinstance(tree.body[0], ast.Expr):
        ds = tree.body[0]
        targets.append((ds.lineno, ds.end_lineno, file_hdr))
    else:
        targets.append((1, None, file_hdr + [""]))  # başa ekle

    # --- fonksiyon / sınıflar ---
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            continue
        body0 = node.body[0]
        indent = body0.col_offset
        existing = ast.get_docstring(node, clean=True)
        if existing:
            dl = existing.split("\n")
            brief = next((x.strip() for x in dl if x.strip()), node.name)
            rest_idx = dl.index(next(x for x in dl if x.strip())) + 1
            details = [x for x in dl[rest_idx:]]
            # baştaki/sondaki boşları kırp
            while details and not details[0].strip():
                details.pop(0)
            while details and not details[-1].strip():
                details.pop()
        else:
            brief = node.name + ("()" if not isinstance(node, ast.ClassDef) else " sınıfı")
            details = []
        if isinstance(node, ast.ClassDef):
            params, has_ret = [], False
        else:
            params, has_ret = func_params(node), returns_value(node)
        new_doc = build_doc(indent, brief, details, params, has_ret)

        ds_node = body0 if (isinstance(body0, ast.Expr)
                            and isinstance(getattr(body0, "value", None), ast.Constant)
                            and isinstance(body0.value.value, str)) else None
        if ds_node is not None:
            targets.append((ds_node.lineno, ds_node.end_lineno, new_doc))
        else:
            # tek satırlık gövde (def f(): return x) → atla
            if body0.lineno == node.lineno:
                continue
            targets.append((body0.lineno, None, new_doc))  # body0'dan önce ekle

    # uygula: en alttan en üste (satır numaraları kaymasın)
    targets.sort(key=lambda t: t[0], reverse=True)
    for start, end, new in targets:
        if end is None:  # ekle (start satırından önce)
            lines[start - 1:start - 1] = new
        else:  # değiştir
            lines[start - 1:end] = new

    out = "\n".join(lines)
    ast.parse(out)  # geçerlilik kontrolü
    open(path, "w", encoding="utf-8").write(out)
    print(f"  ✓ {path}: {len(targets)} blok dokümante edildi")


FILE_HEADERS = {
    "viewer.py": [
        '"""',
        "@file viewer.py",
        "@brief Altium projelerini interaktif HTML görüntüleyiciye ve veri dosyalarına dönüştürür.",
        "",
        "@details",
        "Altium şematik (.SchDoc) ve PCB (.PcbDoc) dosyalarını okuyup tek-dosya, çevrimdışı",
        "çalışan HTML görüntüleyiciler üretir: interaktif şematik, Altium benzeri PCB katman",
        "görüntüleyici ve gerçek STEP modelleri + bakır/silkscreen dokusu içeren 3B board.",
        "Ayrıca BOM / Pick&Place (CSV), IC bağlantı haritası / MCU pin listesi (Excel) ve",
        "AI/LLM analizi için kompakt JSON dışa aktarımı sağlar. Üretilen HTML tamamen",
        "bağımsızdır (Three.js gömülü, harici bağımlılık yok).",
        "",
        "@author altium-monkey",
        "@date 2026",
        "@version 2.9.27",
        '"""',
    ],
    "gui.py": [
        '"""',
        "@file gui.py",
        "@brief viewer.py için PyQt5 masaüstü grafik arayüzü.",
        "",
        "@details",
        "Altium projesi seçimi, şemaların otomatik listelenmesi ve tüm çıktıların",
        "(HTML görüntüleyiciler, Excel/CSV veri, JSON) tek pencereden üretilmesini sağlar.",
        "Üretim arka plan iş parçacığında (GeneratorThread) yürütülür; ilerleme çubuğu ve",
        "log canlı güncellenir. Arayüz gui.ui (Qt Designer) dosyasından yüklenir ve",
        "APP_STYLE (QSS koyu tema) ile biçimlendirilir.",
        "",
        "@author altium-monkey",
        "@date 2026",
        "@version 2.9.27",
        '"""',
    ],
}

if __name__ == "__main__":
    for p in sys.argv[1:]:
        process(p)
