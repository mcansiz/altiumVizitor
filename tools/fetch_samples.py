"""
@file tools/fetch_samples.py
@brief Testlerin kullandığı herkese açık örnek Altium projelerini indirir.

@details
Şirket projeleri (altium_prj/, AltiumBasic/) depoya girmez; CI'daki uçtan uca
üretim testleri bunun yerine altium_monkey deposunun kendi örnek projelerini
kullanır. Dosyalar SABİT bir commit'ten indirilir (içerik değişmez) ve
SHA-256 ile denetlenir.

Kullanım:  py -3.12 tools/fetch_samples.py [hedef_klasör]
           (varsayılan: .tmp/samples — testler de oraya bakar)

Örnekler:
  m2_emmc            tek sayfa şematik + PcbDoc (PCB, 3D, BOM/PnP yolu)
  simple_hierchical  üç sayfalı hiyerarşi, PCB'siz (hiyerarşi ağacı yolu)

Lisans: altium_monkey AGPL-3.0 (bu proje de AGPL-3.0); dosyalar yalnız test
için indirilir, depoya ve pakete girmez.

@author Mikail Cansız
@date 2026
"""
import hashlib
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
COMMIT = "aa9e39c3be9aeba8f11eb7cb9773e42dfafd37b9"   # wavenumber-eng/altium_monkey, 2026-09-22
BASE = f"https://raw.githubusercontent.com/wavenumber-eng/altium_monkey/{COMMIT}/examples/assets/projects/"

## @brief (göreli yol, sha256)
FILES = [
    ("m2_emmc/m2_emmc.PrjPcb", "a7d30556ad6b1f7d7f8fb4fecf377eab59bcb7b38519cb7b8851f0932d5e2bbb"),
    ("m2_emmc/m2_emmc.SchDoc", "37221e504a0dd242bb5e9a43bbe305929f4f1260319c626274c7916792a6569f"),
    ("m2_emmc/m2_emmc.PcbDoc", "9cccda95e1068a9dabb04d60d0bd50e6b6823415233383927e7a99669ba6d4e6"),
    ("simple_hierchical/simple.PrjPCB", "debc4e3f780189802ce306abdc8b2dd93a2c11dd3a3b035bf2629b9e017440e4"),
    ("simple_hierchical/parent.SchDoc", "3a36e0c41ec14c67789519d86548d693d935b19ca7e0054a3b3f307227353653"),
    ("simple_hierchical/child.SchDoc", "2ab9f28ca29f7d26ed5b2209efd39c2297b0c1ad48f896ac44d7a68c2e07c9ed"),
    ("simple_hierchical/childA.SchDoc", "c603a133b9210fb2460e187c2c4920eb4f29d59d90c7ecbccd6e64f094352fb3"),
]

## @brief Testlerin kullandığı proje dosyaları (hedef klasöre göreli).
PROJECTS = {
    "m2_emmc": "m2_emmc/m2_emmc.PrjPcb",
    "simple_hierchical": "simple_hierchical/simple.PrjPCB",
}


def _local(rel: str) -> str:
    """@brief Depodaki göreli yolu yerel düzene çevirir: `<örnek>/proj/<dosya>`.

    @details Her örnek kendi `proj/` klasörüne konur. Örnekler kardeş klasörde
    dursaydı PcbDoc'u olmayan projede `_resolve_pcbdoc_paths`'ın üst dizin
    taraması BAŞKA örneğin PcbDoc'unu bulup onu kullanırdı (ölçüldü:
    simple_hierchical, m2_emmc'nin board'unu aldı).

    @param rel Depodaki göreli yol (ör. "m2_emmc/m2_emmc.PrjPcb")
    @return Yerel göreli yol (ör. "m2_emmc/proj/m2_emmc.PrjPcb")
    """
    name, _, rest = rel.partition("/")
    return f"{name}/proj/{rest}"


def _sha256(path: Path) -> str:
    """@brief Dosyanın SHA-256 özetini döndürür.

    @param path Dosya yolu
    @return Onaltılık özet
    """
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def fetch(dest: Path) -> dict:
    """@brief Örnekleri indirir (zaten varsa ve özet tutuyorsa atlar).

    @param dest Hedef klasör
    @return {ad: proje dosyası yolu}
    """
    for rel, digest in FILES:
        path = dest / _local(rel)
        if path.is_file() and _sha256(path) == digest:
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        print(f"indiriliyor: {rel}", flush=True)
        with urllib.request.urlopen(BASE + urllib.request.quote(rel), timeout=120) as r:
            path.write_bytes(r.read())
        got = _sha256(path)
        if got != digest:
            raise SystemExit(f"HATA: {rel} SHA-256 tutmuyor ({got})")
    return {name: dest / _local(rel) for name, rel in PROJECTS.items()}


def main() -> int:
    """@brief CLI giriş noktası.

    @return Çıkış kodu
    """
    dest = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / ".tmp" / "samples"
    for name, path in fetch(dest).items():
        print(f"{name}: {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
