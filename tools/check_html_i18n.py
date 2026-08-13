"""
@file tools/check_html_i18n.py
@brief HTML görüntüleyici çevirilerinin kapsama ve güvenlik denetimi.

@details
viewer.py şablonlarındaki her ⟪metin⟫ işareti için:
  1. i18n katalogunda karşılığı var mı (yoksa o metin İngilizce çıktıda
     Türkçe kalır — sessiz eksik),
  2. çeviri metni ' " < > içeriyor mu (bu metinler tek/çift tırnaklı JS
     dizgelerine ve HTML attribute'larına gömülür; tırnak şablonu bozar),
  3. katalogda ARTIK kullanılmayan HTML anahtarı kalmış mı (ölü kayıt).

Kullanım:  py -3.12 tools/check_html_i18n.py   (sorun varsa çıkış kodu 1)

@author Mikail Cansız
@date 2026
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import i18n  # noqa: E402

MARK = re.compile(r"⟪([^⟪⟫]*)⟫")
# Kendi belge/yorum satırlarımızdaki örnek işaretler (şablonda değil)
DOC_LINES_MAX = 80
UNSAFE = re.compile(r"[\"'<>]")

src = (ROOT / "viewer.py").read_text(encoding="utf-8")
lines = src.splitlines()
keys = set()
for ln, line in enumerate(lines, 1):
    if ln <= DOC_LINES_MAX:
        continue  # _tr_html'in kendi docstring'i
    keys.update(MARK.findall(line))
keys.discard("")

def variants(k):
    """@brief Anahtarın kaynak ve ÇALIŞMA-ANI biçimleri.

    @details Şablon bir f-string ise kaynaktaki `\\\\'` çalışma anında `\\'`
    olur — katalog anahtarı çalışma-anı biçimidir, denetim ikisini de dener.

    @param k Kaynaktan okunan işaret metni
    @return Denenecek anahtar biçimleri
    """
    return {k, k.replace("\\\\", "\\")}


def lookup(k):
    """@brief Anahtarın katalogdaki karşılığını bul (biçim varyantlarıyla).

    @param k İşaret metni
    @return Çeviri metni ya da None
    """
    for v in variants(k):
        if v in i18n._EN:
            return i18n._EN[v]
    return None


missing = sorted(k for k in keys if lookup(k) is None)
unsafe = sorted((k, lookup(k)) for k in keys
                if lookup(k) and UNSAFE.search(lookup(k)))
used = {v for k in keys for v in variants(k)}
dead = sorted(k for k in i18n._EN_HTML if k not in used)

print(f"şablonda {len(keys)} benzersiz arayüz metni işaretli")
print(f"katalogda karşılığı olan: {len(keys) - len(missing)}")

ok = True
if missing:
    ok = False
    print(f"\n✗ ÇEVİRİSİ EKSİK ({len(missing)}):")
    for k in missing:
        print("   ", repr(k))
if unsafe:
    ok = False
    print(f"\n✗ GÜVENSİZ ÇEVİRİ — ' \" < > içeriyor ({len(unsafe)}):")
    for k, v in unsafe:
        print("   ", repr(k), "→", repr(v))
if dead:
    print(f"\n! katalogda kullanılmayan anahtar ({len(dead)}):")
    for k in dead:
        print("   ", repr(k))

print("\n✓ tamam" if ok else "\n✗ sorun var")
sys.exit(0 if ok else 1)
