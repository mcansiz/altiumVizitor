---
paths:
  - "gui.py"
  - "gui.ui"
---

# PyQt5 (PyQt6 değil) Kuralları

Bu projede **PyQt5** kullanıyoruz, PyQt6 değil. Sebep: PyInstaller ile fresh
Windows'ta PyQt6 paketinde DLL load failed problemi yaşadık. PyQt5'in
ekosistemi paketleme araçları için daha olgun.

## Import

```python
from PyQt5 import QtWidgets, QtCore, QtGui, uic
# PyQt6 YOK
```

## Event Loop

```python
sys.exit(app.exec_())   # PyQt5'te underscore'lu
# sys.exit(app.exec())  # PyQt6 stili — bazı eski PyQt5'lerde patlar
```

PyQt5 5.15+ ikisini de destekler ama `exec_()` daha güvenli — geri uyumlu.

## Sinyaller

```python
log_signal = QtCore.pyqtSignal(str)         # pyqtSignal (lowercase q, S büyük)
done_signal = QtCore.pyqtSignal(bool, str)
```

## QThread Pattern (Non-blocking üretim)

```python
class GeneratorThread(QtCore.QThread):
    log_signal = QtCore.pyqtSignal(str)
    done_signal = QtCore.pyqtSignal(bool, str)

    def __init__(self, mode, project_path, output_path, **kwargs):
        super().__init__(parent=None)
        # ... attribute'ları sakla

    def run(self):
        try:
            # uzun süren iş
            self.done_signal.emit(True, result)
        except Exception as e:
            self.log_signal.emit(traceback.format_exc())
            self.done_signal.emit(False, str(e))
```

Worker fonksiyonlara `log=lambda msg: self.log_signal.emit(msg)` geçir, ana
thread'den UI güncellemesi yapılır.

## .ui Dosyaları (Qt Designer)

PyQt5'in `uic` modülü scoped enum'ları tanımaz. .ui dosyasında:

```xml
<!-- DOĞRU (flat enum) -->
<property name="orientation"><enum>Qt::Horizontal</enum></property>

<!-- YANLIŞ (PyQt6 scoped enum) — PyQt5'in uic'i yükleyemez -->
<property name="orientation"><enum>Qt::Orientation::Horizontal</enum></property>
```

PyQt6 ile yapılmış .ui dosyalarını PyQt5'e taşırken `Qt::Foo::Bar` → `Qt::Bar`
şeklinde flatten et.

## Sürüm Bilgisi Gösterimi

`gui.py` üstünde `APP_VERSION` sabiti var. Sürüm + ortam bilgisi `collect_versions()`
ile toplanır:

```python
from importlib import metadata
from PyQt5.QtCore import QT_VERSION_STR, PYQT_VERSION_STR
import platform

metadata.version("altium-monkey")   # pip ile kurulu paket sürümü
platform.python_version()           # Python sürümü
QT_VERSION_STR, PYQT_VERSION_STR    # Qt ve PyQt5 binding sürümleri
```

`metadata.version(pkg)` paket kurulu değilse `PackageNotFoundError` atar —
try/except ile sar, "—" döndür. Yeni bir bağımlılık eklersen `collect_versions()`
içindeki listeye ekle.

Sürüm dört yerde görünür: pencere başlığı, alt status bar (`self.statusBar()`),
üretim log başlığı, ve "Hakkında" diyaloğu (`QMessageBox.setDetailedText` ile
monospace liste + panoya kopyala butonu).

## PyInstaller Paketleme

```bash
py -3.12 -m PyInstaller --noconfirm --onefile --windowed --name "SchematicViz" ^
    --collect-all altium_monkey --collect-all PyQt5 ^
    --add-data "gui.ui;." gui.py
```

`--add-data "gui.ui;."` Windows'ta noktalı virgül ayraç (Linux'ta `:`).

gui.py'de `gui.ui` dosyasını şöyle yükle (frozen exe'de `sys._MEIPASS`):

```python
def resource_path(name):
    if getattr(sys, "frozen", False):
        return str(Path(sys._MEIPASS) / name)
    return str(Path(__file__).parent / name)

uic.loadUi(resource_path("gui.ui"), self)
```

Fresh Windows'ta exe açılmazsa **MS VC++ Redistributable** gerekir:
https://aka.ms/vs/17/release/vc_redist.x64.exe (kullanıcıya yönlendir).
