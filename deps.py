"""
@file deps.py
@brief Projenin bağımlılık kataloğu ve başlangıç denetimi (eksik paketle çalıştırmayı engeller).

@details
Uygulamanın kullandığı TÜM üçüncü-parti kütüphaneler tek kaynak olarak burada
listelenir: doğrudan import edilenler (PyQt5, altium-monkey, openpyxl, cascadio,
trimesh, numpy) ve bunların çalışma zamanında gerçekten gereken alt bağımlılıkları
(freetype-py, lxml, lz4, pillow, uharfbuzz, wn-geometer, et-xmlfile, PyQt5-sip,
PyQt5-Qt5). pip'in kurduğu ama BİZİM kullanmadığımız paketler (msgspec,
jsonschema-rs) bilerek listede DEĞİL — gerekçe DEPENDENCIES tablosunun sonunda.

`gui.py` ve `viewer.py` import edilir edilmez bu modülü çağırır:
- gui.py  → `enforce(gui=True)`  : eksik varsa konsola + hata diyaloğuna yazar, çıkar.
- viewer.py → `require()`        : eksik varsa `DependencyError` fırlatır.

Yani bağımlılıklardan biri eksikse (veya doğrudan bağımlılıklardan biri
requirements.txt'te bildirilen minimumun altındaysa) uygulama HİÇ AÇILMAZ; bunun
yerine hangi paketin eksik olduğunu ve çalıştırılacak tam `pip install` komutunu
söyleyen açık bir mesaj verir. Böylece sorun, üretim sırasında gizli bir
`ImportError` / sessiz geri-düşme (fallback) olarak değil, ilk saniyede görülür.

Komut satırı kullanımı:
```
py -3.12 deps.py                 # tüm kütüphaneleri durumlarıyla listeler (eksikse çıkış kodu 1)
py -3.12 deps.py --requirements  # requirements.txt satırlarını üretir (drift kontrolü)
```

Denetimi bilinçli olarak atlamak gerekirse (vendored/özel kurulum):
`SCHVIZ_SKIP_DEP_CHECK=1` ortam değişkeni.

@author Mikail Cansız
@date 2026
"""
# Schematic Viz Generator — bağımlılık kataloğu ve başlangıç denetimi.
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
import os
import re
import sys
from importlib import metadata, util
from typing import NamedTuple, Optional


class Dep(NamedTuple):
    """@brief Tek bir bağımlılığın tanımı.

    @param dist PyPI/pip dağıtım adı (ör. "altium-monkey")
    @param module Import adı (ör. "altium_monkey"); yalnız ikili dosya taşıyan
                  paketlerde None (o zaman sadece pip metadata'sına bakılır)
    @param min_version requirements.txt'te bildirilen minimum sürüm (yoksa None)
    @param purpose Projede ne için kullanıldığı (hata mesajında/listede gösterilir)
    @param direct Kodumuzun DOĞRUDAN import ettiği paket mi (False = alt bağımlılık)
    """
    dist: str
    module: Optional[str]
    min_version: Optional[str]
    purpose: str
    direct: bool


## @brief Projenin tüm bağımlılıkları (tek kaynak; requirements.txt bununla eşleşir).
#
#  Sürüm minimumları YALNIZCA doğrudan bağımlılıklar için zorlanır; alt
#  bağımlılıklarda (altium-monkey/openpyxl/PyQt5 kendi pin'lerini pip ile
#  zorluyor) yalnızca "kurulu mu" kontrolü yapılır — böylece pip'in çözdüğü
#  geçerli bir kurulum sürüm ayrıntısı yüzünden yanlışlıkla reddedilmez.
DEPENDENCIES = (
    # --- Doğrudan import edilenler (gui.py / viewer.py) ---
    Dep("PyQt5", "PyQt5", "5.15.11",
        "Masaüstü arayüz (gui.py + gui.ui)", True),
    Dep("altium-monkey", "altium_monkey", "2026.8.21",
        "Altium SchDoc/PcbDoc okuma, SVG render, netlist derleme", True),
    Dep("openpyxl", "openpyxl", "3.1",
        "Excel çıktıları (IC bağlantı haritası, MCU pin listesi)", True),
    Dep("cascadio", "cascadio", "0.0.17",
        "3D: gömülü STEP modellerini GLB'ye dönüştürme", True),
    Dep("trimesh", "trimesh", "4.12",
        "3D: STEP mesh ayrıştırma (vertex/face/renk)", True),
    Dep("numpy", "numpy", "2.0",
        "3D: vertex/face dizi işlemleri", True),

    # --- Alt bağımlılıklar (doğrudan import etmiyoruz ama olmazsa çöker) ---
    Dep("PyQt5-Qt5", None, None,
        "PyQt5: Qt5 çalışma zamanı ikilileri", False),
    Dep("PyQt5-sip", "PyQt5.sip", None,
        "PyQt5: C++ ↔ Python köprüsü", False),
    Dep("freetype-py", "freetype", None,
        "altium_monkey: yazı tipi (glif) render", False),
    Dep("lxml", "lxml", None,
        "altium_monkey: XML/SVG ayrıştırma", False),
    Dep("lz4", "lz4", None,
        "altium_monkey: kayıt sıkıştırma", False),
    Dep("pillow", "PIL", None,
        "altium_monkey: görüntü işleme", False),
    Dep("uharfbuzz", "uharfbuzz", None,
        "altium_monkey: metin şekillendirme", False),
    Dep("wn-geometer", "geometer", None,
        "altium_monkey: geometri (Linux'ta glibc >= 2.35 gerektirir)", False),
    Dep("et-xmlfile", "et_xmlfile", None,
        "openpyxl: XML akış yazımı", False),
    # --- BİLEREK LİSTEDE DEĞİL: msgspec + jsonschema-rs (v2.27.7) ---
    # altium-monkey 2026.8.21 bunları `Requires-Dist` olarak bildiriyor
    # (yeni `pcb_manufacturing` / IPC-2581 alt paketi için), yani pip HER ZAMAN
    # kuruyor. Ama bu tablo "olmazsa uygulama çöker" listesidir ve bu ikisi o
    # ölçüte UYMUYOR: kod yolumuz `pcb_manufacturing`'i hiç import etmiyor
    # (ölçüldü — ikisi de `sys.meta_path`'ten bloklanınca kullandığımız 10
    # modülün hepsi sorunsuz açılıyor).
    # Listeye eklemek FROZEN EXE'Yİ AÇILMAZ YAPIYOR: `pcb_manufacturing`
    # kütüphanenin BİLDİRMEDİĞİ `shapely`'yi de istediğinden PyInstaller onu
    # import edemiyor ("Failed to collect submodules … No module named
    # 'shapely'"), alt modülleri toplayamıyor ve msgspec/jsonschema_rs exe'ye
    # HİÇ girmiyor → denetim "KURULU DEĞİL" deyip SystemExit(1) veriyor
    # (bir kez yaşandı ve exe açılmadı). Kullanmadığımız bir paketi yalnız
    # denetimi susturmak için exe'ye gömmek de doğru değil.
    # Kayıt olarak requirements.txt'in alt bağımlılık notunda duruyorlar.
)

## @brief Denetimi atlamak için ayarlanabilecek ortam değişkeni.
SKIP_ENV = "SCHVIZ_SKIP_DEP_CHECK"

## @brief Sorun türü etiketleri (kullanıcıya gösterilen kısa durum).
_KIND_LABEL = {
    "missing": "KURULU DEĞİL",
    "broken": "KURULUM BOZUK",
    "outdated": "ESKİ SÜRÜM",
}


class Problem(NamedTuple):
    """@brief Denetimde bulunan tek bir bağımlılık sorunu.

    @param dep İlgili bağımlılık tanımı
    @param kind "missing" (yok) | "broken" (metadata var, modül yüklenemiyor) |
                "outdated" (minimumun altında)
    @param found Kurulu sürüm (bilinmiyorsa None)
    """
    dep: Dep
    kind: str
    found: Optional[str]


class DependencyError(RuntimeError):
    """@brief Eksik/uyumsuz bağımlılık hatası (mesajı kullanıcıya gösterilmeye hazırdır)."""


# Denetim sonucu önbelleği — gui.py ve viewer.py aynı süreçte iki kez çağırır.
_CACHE = None


def _write(text: str, stream=None) -> None:
    """@brief Konsola güvenle yaz (Windows'ta cp1252/cp437 konsolları çökertmeden).

    Mesajda Türkçe karakterler ve ✓/✗/→ gibi işaretler var; Türkçe Windows'ta
    konsol kod sayfası bunları kodlayamayınca `print` UnicodeEncodeError fırlatır
    ve eksik-bağımlılık mesajı hiç görünmez (asıl hatanın üstünü örter). Bu yüzden
    yazma her zaman kodlanamayan karakterleri '?' ile değiştirerek yedeklenir.

    @param text Yazılacak metin
    @param stream Hedef akış (varsayılan: sys.stderr)
    """
    stream = stream or sys.stderr
    try:
        stream.write(text + "\n")
        stream.flush()
        return
    except UnicodeEncodeError:
        pass
    except Exception:
        return
    enc = getattr(stream, "encoding", None) or "ascii"
    data = (text + "\n").encode(enc, errors="replace")
    buf = getattr(stream, "buffer", None)
    try:
        if buf is not None:
            buf.write(data)
            buf.flush()
        else:
            stream.write(data.decode(enc, errors="replace"))
            stream.flush()
    except Exception:
        pass


def _installed_version(dist: str) -> Optional[str]:
    """@brief Kurulu dağıtımın sürümünü döndür (kurulu değilse None).

    @param dist pip dağıtım adı
    @return Sürüm dizgesi veya None
    """
    try:
        return metadata.version(dist)
    except Exception:
        return None


def _module_present(module: Optional[str]) -> Optional[bool]:
    """@brief Modülün import edilebilir olup olmadığını (modülü ÇALIŞTIRMADAN) bak.

    `find_spec` kullanılır: paket bulunur ama içeriği yürütülmez → başlangıç
    hızlı kalır (numpy/trimesh import etmek saniyeler alabilir).

    @param module Import adı; None ise denetim yapılmaz
    @return True/False, module None ise None (bilinmiyor)
    """
    if module is None:
        return None
    try:
        return util.find_spec(module) is not None
    except Exception:
        # Üst paket yoksa ModuleNotFoundError, bozuk kurulumda başka hatalar gelir.
        return False


def parse_version(ver: Optional[str]):
    """@brief Sürüm dizgesinin baştaki sayısal kısmını demete çevir.

    "2026.6.21" → (2026, 6, 21); "4.12.2.post1" → (4, 12, 2); "3.1" → (3, 1).
    Not: `int(x) for x in ver.split(".")` gibi saf bölme, PyPI'daki `.postN` /
    `bN` / `rcN` ekli sürümlerde patlar (altium-monkey 2026.8.11.post1 gerçek
    örnek) — bu yüzden regex ile yalnız baştaki sayısal kısım alınır.
    Ayrıştırılamazsa None döner (o zaman sürüm karşılaştırması ATLANIR — hatalı
    ayrıştırma yüzünden geçerli bir kurulumu reddetmemek için).

    @param ver Sürüm dizgesi
    @return int demeti veya None
    """
    if not ver:
        return None
    m = re.match(r"\s*v?(\d+(?:\.\d+)*)", str(ver))
    if not m:
        return None
    return tuple(int(x) for x in m.group(1).split("."))


def _older(found: Optional[str], minimum: Optional[str]) -> bool:
    """@brief Kurulu sürüm bildirilen minimumun altında mı?

    Demetler eşit uzunluğa sıfırla tamamlanır ((2,0) ile (2,0,0) eşit sayılsın).

    @param found Kurulu sürüm
    @param minimum Gereken minimum sürüm
    @return Eskiyse True; karşılaştırılamıyorsa False (şüphede kabul et)
    """
    a, b = parse_version(found), parse_version(minimum)
    if a is None or b is None:
        return False
    n = max(len(a), len(b))
    a += (0,) * (n - len(a))
    b += (0,) * (n - len(b))
    return a < b


def check(force: bool = False):
    """@brief Tüm bağımlılıkları denetle ve sorunları döndür.

    @param force True ise önbelleği yok sayıp yeniden denetler
    @return Problem listesi (boşsa her şey tamam)
    """
    global _CACHE
    if _CACHE is not None and not force:
        return _CACHE
    # Paketlenmiş exe'de (PyInstaller) pip metadata'sı bulunmayabilir; orada
    # tek güvenilir ölçüt modülün pakete gömülmüş olmasıdır. Bu yüzden frozen
    # modda yalnız import edilebilirlik denetlenir (sürüm/metadata denetimi
    # yanlış "eksik" raporlayıp exe'yi hiç açılmaz hale getirmesin).
    frozen = bool(getattr(sys, "frozen", False))
    problems = []
    for dep in DEPENDENCIES:
        ver = _installed_version(dep.dist)
        present = _module_present(dep.module)
        if present is False:
            # Modül bulunamadı: metadata da yoksa hiç kurulmamış, varsa kurulum bozuk.
            problems.append(Problem(dep, "missing" if ver is None else "broken", ver))
        elif present is None:
            # Import edilebilir modülü olmayan paket (yalnız ikili/veri taşır) →
            # sadece pip kaydından doğrulanabilir.
            if ver is None and not frozen:
                problems.append(Problem(dep, "missing", None))
        elif dep.direct and dep.min_version and ver and _older(ver, dep.min_version):
            problems.append(Problem(dep, "outdated", ver))
    _CACHE = problems
    return problems


def _pip_command(problems) -> str:
    """@brief Sorunlu paketleri kuracak `pip install` komutunu üret.

    @param problems Problem listesi
    @return Kopyalanabilir tek satırlık komut
    """
    specs = []
    for p in problems:
        dep = p.dep
        specs.append(f'"{dep.dist}>={dep.min_version}"' if dep.min_version else dep.dist)
    if getattr(sys, "frozen", False):
        # Paketlenmiş exe'de sys.executable uygulamanın kendisidir; pip yoktur.
        runner = "py -3.12 -m pip" if os.name == "nt" else "python3 -m pip"
    else:
        runner = f'"{sys.executable}" -m pip'
    return f"{runner} install {' '.join(specs)}"


def format_report(problems) -> str:
    """@brief Sorunları kullanıcıya gösterilecek açık bir metne dönüştür.

    @param problems Problem listesi
    @return Çok satırlı hata metni (pip komutu dahil)
    """
    lines = ["Schematic Viz başlatılamadı: gerekli kütüphanelerden bazıları eksik "
             "veya uyumsuz.", ""]
    for p in problems:
        dep = p.dep
        durum = _KIND_LABEL.get(p.kind, p.kind)
        if p.kind == "outdated":
            durum = f"{durum} (kurulu {p.found}, gereken >= {dep.min_version})"
        elif p.kind == "broken":
            durum = f"{durum} (pip kaydı {p.found} var ama '{dep.module}' import edilemiyor)"
        tur = "" if dep.direct else "  [alt bağımlılık]"
        lines.append(f"  ✗ {dep.dist:<14s} {durum}{tur}")
        lines.append(f"      → {dep.purpose}")
    lines += ["", "Çözüm:", f"  {_pip_command(problems)}", "",
              "veya tüm bağımlılıkları birden kurmak için:",
              "  py -3.12 -m pip install -r requirements.txt" if os.name == "nt"
              else "  python3 -m pip install -r requirements.txt"]
    if getattr(sys, "frozen", False):
        lines += ["", "(Bu bir paketlenmiş exe: kütüphane pakete dahil edilmemiş. "
                  "build_exe.bat ile yeniden paketleyin.)"]
    lines += ["", f"Denetimi atlamak için (önerilmez): {SKIP_ENV}=1"]
    return "\n".join(lines)


def require(force: bool = False) -> None:
    """@brief Eksik/uyumsuz bağımlılık varsa DependencyError fırlat.

    Kütüphane olarak kullanım için (viewer.py import edildiğinde çağrılır).

    @param force True ise önbelleği yok sayıp yeniden denetler
    @throws DependencyError Eksik veya uyumsuz paket bulunduğunda
    """
    if os.environ.get(SKIP_ENV):
        return
    problems = check(force=force)
    if problems:
        raise DependencyError(format_report(problems))


def enforce(gui: bool = False) -> None:
    """@brief Bağımlılıkları denetle; sorun varsa mesajı göster ve uygulamayı KAPAT.

    Uygulama giriş noktası için (gui.py). Konsola her zaman yazar; `gui=True` ise
    ayrıca PyQt5 kuruluysa bir hata diyaloğu gösterir (PyQt5'in kendisi eksikse
    diyalog atlanır, konsol mesajı kalır).

    @param gui True ise grafik hata diyaloğu da denenir
    """
    try:
        require()
    except DependencyError as exc:
        msg = str(exc)
        _write(msg)
        if gui:
            try:
                from PyQt5 import QtWidgets
                app = QtWidgets.QApplication.instance() or QtWidgets.QApplication(sys.argv)
                box = QtWidgets.QMessageBox()
                box.setIcon(QtWidgets.QMessageBox.Critical)
                box.setWindowTitle("Eksik bağımlılık")
                box.setText("Schematic Viz başlatılamadı — gerekli kütüphaneler eksik.")
                box.setDetailedText(msg)
                box.exec_()
            except Exception:
                pass  # PyQt5 yoksa/açılamıyorsa konsol mesajı yeterli
        raise SystemExit(1)


def status_table():
    """@brief Tüm bağımlılıkları durumlarıyla birlikte listele (GUI "Hakkında" + CLI).

    @return [(dist, kurulu_sürüm|"—", durum, açıklama, doğrudan_mı), ...]
    """
    by_dist = {p.dep.dist: p for p in check()}
    rows = []
    for dep in DEPENDENCIES:
        prob = by_dist.get(dep.dist)
        ver = _installed_version(dep.dist)
        if prob is None:
            durum = "tamam"
        elif prob.kind == "outdated":
            durum = f"eski (>= {dep.min_version} gerekli)"
        else:
            durum = _KIND_LABEL.get(prob.kind, prob.kind).lower()
        rows.append((dep.dist, ver or "—", durum, dep.purpose, dep.direct))
    return rows


def requirements_lines():
    """@brief requirements.txt'in doğrudan bağımlılık satırlarını üret (drift kontrolü).

    @return Satır listesi (ör. 'PyQt5>=5.15.11')
    """
    return [f"{d.dist}>={d.min_version}" if d.min_version else d.dist
            for d in DEPENDENCIES if d.direct]


def _main() -> int:
    """@brief CLI: bağımlılık tablosunu yazdır (veya --requirements çıktısı).

    @return Süreç çıkış kodu (0 = her şey tamam, 1 = eksik/uyumsuz var)
    """
    # Türkçe metin + ✓/✗ işaretleri için mümkünse konsolu UTF-8'e al.
    for st in (sys.stdout, sys.stderr):
        try:
            st.reconfigure(encoding="utf-8")
        except Exception:
            pass
    if "--requirements" in sys.argv:
        _write("\n".join(requirements_lines()), sys.stdout)
        return 0
    rows = status_table()
    out = [f"Schematic Viz — bağımlılıklar ({sys.version.split()[0]} @ {sys.executable})", ""]
    hdr = f"  {'PAKET':<16s} {'SÜRÜM':<16s} {'DURUM':<26s} AÇIKLAMA"
    out += [hdr, "-" * max(len(hdr), 96)]
    for grup, dogrudan in (("Doğrudan kullanılan", True), ("Alt bağımlılıklar", False)):
        out.append(f"\n[{grup}]")
        for dist, ver, durum, purpose, direct in rows:
            if direct is dogrudan:
                isaret = "✓" if durum == "tamam" else "✗"
                out.append(f"{isaret} {dist:<16s} {ver:<16s} {durum:<26s} {purpose}")
    _write("\n".join(out), sys.stdout)
    problems = check()
    if problems:
        _write("\n" + format_report(problems), sys.stdout)
        return 1
    _write("\n✓ Tüm bağımlılıklar kurulu — uygulama çalıştırılabilir.", sys.stdout)
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
