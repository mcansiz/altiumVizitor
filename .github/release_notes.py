"""Taslak release gövdesini üretir (release.yml çağırır; çıktı stdout'a).

    python3 .github/release_notes.py <sürüm> <etiket> <önceki_etiket> <repo> <run_url> <macos_sonucu>

Değişiklik notları isteğe bağlıdır: `.github/release-notes/v<sürüm>.tr.md` ve
`.en.md` varsa ilgili bölüme konur; yoksa yer tutucu yazılır ve taslak
yayınlanmadan önce GitHub'da elle doldurulur. İndirme tablosu, kurulum notları,
SHA256SUMS ve "Full Changelog" bağlantısı her zaman otomatik gelir.
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
VCREDIST = "https://aka.ms/vs/17/release/vc_redist.x64.exe"


def notes(ver: str, lang: str) -> str:
    path = HERE / "release-notes" / f"v{ver}.{lang}.md"
    if path.is_file():
        return path.read_text(encoding="utf-8").strip()
    return ("<!-- Değişiklik notlarını buraya yazın (taslak). -->" if lang == "tr"
            else "<!-- Write the release notes here (draft). -->")


def main() -> int:
    ver, tag, prev, repo, run_url, macos = sys.argv[1:7]
    win = f"SchematicViz-v{ver}-win-x64.exe"
    lin = f"SchematicViz-v{ver}-linux-x86_64.AppImage"
    mac = f"SchematicViz-v{ver}-macos-arm64.zip"
    has_mac = macos == "success"

    tr_rows = [
        f"| **Windows 10/11 (64-bit)** | `{win}` | Tek dosya, kurulum gerektirmez. Temiz bir "
        f"Windows'ta açılmazsa [MS VC++ Redistributable]({VCREDIST}) kurun. İmzasız: "
        "SmartScreen'de **Ek bilgi → Yine de çalıştır**. |",
        f"| **Linux (64-bit)** | `{lin}` | `chmod +x` ile çalıştırılabilir yapın. glibc 2.35+ "
        "(Ubuntu 22.04+ / Debian 12+). FUSE yoksa `--appimage-extract-and-run`. |",
    ]
    en_rows = [
        f"| **Windows 10/11 (64-bit)** | `{win}` | Single file, no installation. If it does not "
        f"start on a fresh Windows machine, install the [MS VC++ Redistributable]({VCREDIST}). "
        "Not code-signed: SmartScreen → **More info → Run anyway**. |",
        f"| **Linux (64-bit)** | `{lin}` | `chmod +x` and run. Needs glibc 2.35+ "
        "(Ubuntu 22.04+ / Debian 12+). Without FUSE: `--appimage-extract-and-run`. |",
    ]
    if has_mac:
        tr_rows.append(
            f"| **macOS 11+ (Apple Silicon), deneysel** | `{mac}` | Yalnız otomatik testlerden "
            "geçti. İmzasız: ilk açılışta engellenirse **Sistem Ayarları → Gizlilik ve Güvenlik → "
            "Yine de Aç** ya da `xattr -dr com.apple.quarantine SchematicViz.app`. |")
        en_rows.append(
            f"| **macOS 11+ (Apple Silicon), experimental** | `{mac}` | Passed automated tests "
            "only. Unsigned: if blocked on first launch use **System Settings → Privacy & "
            "Security → Open Anyway** or `xattr -dr com.apple.quarantine SchematicViz.app`. |")

    changelog = (f"**Full Changelog**: https://github.com/{repo}/compare/{prev}...{tag}"
                 if prev else "")
    body = f"""## 🇹🇷 Türkçe

{notes(ver, "tr")}

### İndirme ve kurulum

| Platform | Dosya | Not |
|---|---|---|
{chr(10).join(tr_rows)}

---

## 🇬🇧 English

{notes(ver, "en")}

### Download and install

| Platform | File | Notes |
|---|---|---|
{chr(10).join(en_rows)}

---

Checksums / sağlama: `SHA256SUMS`. Built and tested automatically by GitHub Actions
from tag `{tag}` on Windows, Linux and macOS ([run]({run_url})).

{changelog}
"""
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stdout.write(body)
    return 0


if __name__ == "__main__":
    sys.exit(main())
