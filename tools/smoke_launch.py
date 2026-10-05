"""
@file tools/smoke_launch.py
@brief Paketlenmiş uygulamayı (exe / AppImage / .app) ekransız açıp sınar.

@details
    python tools/smoke_launch.py <sürüm> <proje.PrjPcb> <komut> [argüman...]

Komut `--selftest <rapor> <proje>` ile çalıştırılır (gui.run_selftest):
pencere kurulur ama gösterilmez, dil gidiş-dönüşü yapılır, projeden JSON +
birleşik görünüm üretilir. Rapor dosyasında sürüm `<sürüm>` ve `ok: true`
olmalı. Bu, v2.27.7'deki gibi "paketleme başarılı ama exe açılmıyor"
(eksik gömülü modül → bağımlılık kapısı SystemExit) durumunu yakalar.

Qt platformu `minimal`: pakette her platformda bulunan ekransız eklenti
(`offscreen` Linux paketinden spec'teki _DROP ile atılıyor). AppImage
FUSE'suz CI'da `APPIMAGE_EXTRACT_AND_RUN=1` ile çalışır.

Çıkış: 0 = geçti, 1 = rapor yok / sürüm tutmuyor / adım başarısız.

@author Mikail Cansız
@date 2026
"""
import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WAIT_SECONDS = 900


def stop_tree(proc: subprocess.Popen) -> None:
    """@brief Başlatılan sürecin bütün ağacını kapatır.

    @param proc Süreç
    """
    if os.name == "nt":
        subprocess.run(["taskkill", "/F", "/T", "/PID", str(proc.pid)], capture_output=True)
    else:
        try:
            os.killpg(proc.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
    try:
        proc.wait(timeout=30)
    except subprocess.TimeoutExpired:
        pass


def main() -> int:
    """@brief CLI giriş noktası.

    @return Çıkış kodu
    """
    if len(sys.argv) < 4:
        print(__doc__)
        return 2
    for st in (sys.stdout, sys.stderr):
        try:
            st.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass
    version, project, command = sys.argv[1], sys.argv[2], sys.argv[3:]
    # Windows CreateProcess göreli yolu (özellikle '/' ayraçlı) çözemiyor.
    if Path(command[0]).exists():
        command[0] = str(Path(command[0]).resolve())
    work = ROOT / ".tmp" / "smoke"
    work.mkdir(parents=True, exist_ok=True)
    report = work / "rapor.json"
    report.unlink(missing_ok=True)
    out_path = work / "cikti.txt"

    env = dict(os.environ, QT_QPA_PLATFORM="minimal", APPIMAGE_EXTRACT_AND_RUN="1",
               PYTHONIOENCODING="utf-8")
    env.pop("SCHVIZ_SKIP_DEP_CHECK", None)   # bağımlılık kapısı GERÇEKTEN sınansın
    cmd = command + ["--selftest", str(report), str(Path(project).resolve())]
    print("başlatılıyor:", " ".join(cmd), flush=True)
    start = time.time()
    # Çıktı boruya değil dosyaya: AppImage'in alt süreci boruyu açık tutar ve
    # okuyan taraf sonsuza dek bekleyebilir (DiskUltimate'te ölçüldü).
    with open(out_path, "wb") as out:
        kw = ({"creationflags": subprocess.CREATE_NEW_PROCESS_GROUP} if os.name == "nt"
              else {"start_new_session": True})
        proc = subprocess.Popen(cmd, env=env, stdout=out, stderr=subprocess.STDOUT, **kw)
        try:
            code = proc.wait(timeout=WAIT_SECONDS)
        except subprocess.TimeoutExpired:
            stop_tree(proc)
            code = None
    print(f"süre: {time.time() - start:.1f} s, çıkış kodu: {code}")
    text = out_path.read_text(encoding="utf-8", errors="replace")
    if text.strip():
        print("--- çıktı ---\n" + text[-4000:])

    if code is None:
        print(f"HATA: uygulama {WAIT_SECONDS} s içinde kapanmadı "
              "(bağımlılık hata diyaloğunda takılmış olabilir)")
        return 1
    if not report.is_file():
        print("HATA: rapor yazılmadı — uygulama self-test'e ulaşamadan kapandı")
        return 1
    data = json.loads(report.read_text(encoding="utf-8"))
    print("--- rapor ---\n" + json.dumps(data, ensure_ascii=False, indent=2))
    if data.get("version") != version:
        print(f"HATA: sürüm {data.get('version')!r}, beklenen {version!r}")
        return 1
    if not data.get("frozen"):
        print("HATA: uygulama paketlenmiş (frozen) çalışmıyor")
        return 1
    if code != 0 or not data.get("ok"):
        print("HATA: self-test başarısız")
        return 1
    print("TAMAM: paketlenmiş uygulama açıldı ve üretim yaptı")
    return 0


if __name__ == "__main__":
    sys.exit(main())
