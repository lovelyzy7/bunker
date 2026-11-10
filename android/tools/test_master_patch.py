"""The builders' master data carries the Pod Programs data.

The fork's builders run the zh pipeline (patch_masterdata_zh = build_bin_e
with bin-edit.default.json's edit surface); the prepared patcher
(NavHobbyDev's) is the runtime library whose TABLE_ROW_ADDITIONS carry
Bunker's rows. The two are different tools by design — the builder also
carries the zh text — so this checks each where the fork uses it, and that
the builder's output holds the Pod Programs rows (the gift text).

Needs the player's own inputs/20240404193219.bin.e; skipped without it.
"""
from pathlib import Path
import sys
import tempfile
import unittest

import assemble_apk

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "android/app/src/main/python"))
ORIGINAL = ROOT / "inputs/20240404193219.bin.e"
POD_PROGRAMS = ROOT / "android/app/src/main/python/patcher/patch_masterdata.py"


class MasterPatchTests(unittest.TestCase):
    def test_builds_start_with_the_pod_programs_data(self):
        if not ORIGINAL.is_file() or not POD_PROGRAMS.is_file():
            self.skipTest("needs inputs/20240404193219.bin.e and prepared sources (scripts/prepare.py)")
        from patcher import patch_masterdata as pm
        rows = pm.TABLE_ROW_ADDITIONS.get("m_gift_text")
        self.assertTrue(rows, "the prepared patcher carries the gift text rows (patches/bunker-gift-text.patch)")
        original = ORIGINAL.read_bytes()
        built = assemble_apk.patch_master(original)
        self.assertNotEqual(built, original)
        self.assertEqual(built, assemble_apk.patch_master(original))  # deterministic

        # The built master holds one of the Pod Programs rows (the gift text).
        import android_calendar
        import tempfile as td
        with td.TemporaryDirectory() as work:
            out = Path(work) / "built.bin.e"
            out.write_bytes(built)
            toc, blob = android_calendar.read_master(out)
            self.assertIn("m_gift_text", toc)
            found = []
            def collect(b):
                import msgpack
                from patcher import patch_masterdata as pm2
                count, pos = pm2.read_array_len(b, 0)
                for _ in range(count):
                    _, row_pos = pm2.read_array_len(b, pos)
                    found.append(pm2.read_int(b, row_pos))
                    pos2 = pm2.skip_msgpack_value(b, pos)
                    pos = pos2
                return 0
            pm.apply_to_table(toc, blob, {}, "m_gift_text", collect)
            self.assertIn(90000, found)


if __name__ == "__main__":
    unittest.main()
