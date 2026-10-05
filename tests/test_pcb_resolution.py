"""
@file tests/test_pcb_resolution.py
@brief Projenin PcbDoc'unun bulunması: kardeş klasör düzeni çalışmalı, başka
projenin board'u ASLA alınmamalı (v2.33.1).

@details Gerçek örnek projeler geçici klasörlerde farklı düzenlerde kurulur.
Eskiden PcbDoc referansı OLMAYAN proje, üst dizindeki başka bir projenin
PcbDoc'unu alıp onunla PnP / PCB / 3D üretiyordu.
"""
import json
import shutil
import unittest
from pathlib import Path

from tests._support import OUT, sample_project

WORK = OUT / "pcb_resolution"


def _copy_project(src_prj: Path, dst_dir: Path, exts=(".PrjPcb", ".SchDoc", ".PcbDoc")) -> None:
    dst_dir.mkdir(parents=True, exist_ok=True)
    for f in src_prj.parent.iterdir():
        if f.suffix.lower() in {e.lower() for e in exts}:
            shutil.copy(f, dst_dir / f.name)


def _edit_prj(prj: Path, replace=(), append="") -> None:
    data = prj.read_bytes()
    for old, new in replace:
        assert old.encode() in data, old
        data = data.replace(old.encode(), new.encode())
    if append:
        data += append.replace("\n", "\r\n").encode()
    prj.write_bytes(data)


class TestPcbResolution(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import viewer
        cls.viewer = viewer
        cls.m2 = sample_project("m2_emmc")
        cls.simple = sample_project("simple_hierchical")
        shutil.rmtree(WORK, ignore_errors=True)
        WORK.mkdir(parents=True)

    def pick(self, prj: Path):
        logs = []
        path, doc = self.viewer._pick_pcbdoc(str(prj), logs.append)
        return path, doc, "\n".join(map(str, logs))

    def test_no_reference_ignores_sibling_project(self):
        """PcbDoc referansı olmayan proje, yan klasördeki başka projenin board'unu ALMAZ."""
        root = WORK / "yan_yana"
        _copy_project(self.m2, root / "m2_emmc")
        _copy_project(self.simple, root / "simple")
        prj = root / "simple" / self.simple.name
        path, doc, log = self.pick(prj)
        self.assertIsNone(path, log)
        self.assertIn("PCB'siz", log)
        out = root / "simple.json"
        self.viewer.generate_json(str(prj), str(out), log=lambda _m: None)
        self.assertFalse(json.loads(out.read_text(encoding="utf-8"))["summary"]["has_pnp"])

    def test_sibling_folder_layout(self):
        """Altium'un `PCB PROJECT/` + `PCB/` + `SCHEMATIC/` düzeni (v2.9.1) çalışmaya devam eder."""
        root = WORK / "kardes"
        _copy_project(self.m2, root / "PCB PROJECT", exts=(".PrjPcb",))
        _copy_project(self.m2, root / "PCB", exts=(".PcbDoc",))
        _copy_project(self.m2, root / "SCHEMATIC", exts=(".SchDoc",))
        prj = root / "PCB PROJECT" / self.m2.name
        _edit_prj(prj, replace=[
            ("DocumentPath=m2_emmc.PcbDoc", "DocumentPath=..\\PCB\\m2_emmc.PcbDoc"),
            ("DocumentPath=m2_emmc.SchDoc", "DocumentPath=..\\SCHEMATIC\\m2_emmc.SchDoc"),
        ])
        path, doc, log = self.pick(prj)
        self.assertIsNotNone(path, log)
        self.assertEqual(path.parent.name, "PCB")
        self.assertNotIn("doğrulanacak", log)     # kesin referans, tahmin değil

    def test_moved_pcbdoc_same_name_is_verified_and_accepted(self):
        """Referans eski bir yolu gösteriyor ama aynı adlı dosya projede: doğrulanıp kabul edilir."""
        root = WORK / "tasinmis"
        _copy_project(self.m2, root / "proj")
        prj = root / "proj" / self.m2.name
        _edit_prj(prj, replace=[("DocumentPath=m2_emmc.PcbDoc",
                                 "DocumentPath=..\\ESKI_YER\\m2_emmc.PcbDoc")])
        path, doc, log = self.pick(prj)
        self.assertIsNotNone(path, log)
        self.assertIn("kabul edildi", log)

    def test_broken_reference_rejects_other_projects_board(self):
        """Referans çözülemiyor, tarama başka projenin board'unu buluyor: örtüşme yok → reddedilir."""
        root = WORK / "bozuk_ref"
        _copy_project(self.m2, root / "m2_emmc")
        _copy_project(self.simple, root / "simple")
        prj = root / "simple" / self.simple.name
        _edit_prj(prj, append="\n[Document99]\nDocumentPath=yok_boyle_bir_board.PcbDoc\n")
        path, doc, log = self.pick(prj)
        self.assertIsNone(path, log)
        self.assertIn("reddedildi", log)

    def test_stale_reference_next_to_valid_one(self):
        """Var olmayan eski referans + geçerli referans: geçerli olan, tahminsiz seçilir."""
        root = WORK / "eski_ref"
        _copy_project(self.m2, root / "proj")
        prj = root / "proj" / self.m2.name
        _edit_prj(prj, append="\n[Document99]\nDocumentPath=.\\examples\\ESKI_BOARD.PcbDoc\n")
        path, doc, log = self.pick(prj)
        self.assertIsNotNone(path, log)
        self.assertEqual(path.name, "m2_emmc.PcbDoc")
        self.assertNotIn("doğrulanacak", log)


if __name__ == "__main__":
    unittest.main()
