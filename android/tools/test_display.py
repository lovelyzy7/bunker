#!/usr/bin/env python3
"""Pod Programs → Display, and the instructions display_patch.c rewrites.

The settings tests need fastapi (the Android Python requirements) and the
prepared Tools sources (scripts/prepare.py). The binary tests run when
BUNKER_GAME_LIB points at a 3.7.1 ARM64 libil2cpp.so (either client: the
client is detected from its file size, per-client).

【rev D·L4】RVA 表按客户端选对（验证门）：
  TableConsistency — display_patch.c kClients/kEnRvas/kJpRvas 与
    tools/rva-display-{en,jp}.json、lunar-scripts-zh/shared/detect_client.py
    REGIONS、region.py REGIONS 同一套 JP/EN 事实表（漂移即红）。
  GameBinary     — BUNKER_GAME_LIB 所指客户端的 11 站点在其自身表下全部命
    中原始指令；对面客户端的表必须拒（选对=本表过、错表拒）。
  本门由 build.py 产物验证门与 verify_*_client.py 清单按本文件断言调用。
"""
from pathlib import Path
import importlib.util
import json, os, re, struct, subprocess, sys, tempfile, unittest

root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(root / "android/app/src/main/python"))

C_SOURCE = root / "android/app/src/main/cpp/display_patch.c"
TABLES = root / "android/tools"
ZH_DETECT = root / "upstream/lunar-scripts-zh/shared/detect_client.py"


class Settings(unittest.TestCase):
    def setUp(self):
        import android_display
        self.display = android_display
        self.dir = tempfile.TemporaryDirectory()
        self.conf = Path(self.dir.name) / "display.conf"

    def tearDown(self):
        self.dir.cleanup()

    def test_missing_file_keeps_the_game_defaults(self):
        self.assertEqual(self.display.read_settings(self.conf), {"fps": "30", "resolution": "default"})

    def test_saved_choices_are_read_back(self):
        self.display.write_settings("60", "native", self.conf)
        self.assertEqual(self.conf.read_text(), "fps=60\nresolution=native\n")
        self.assertEqual(self.display.read_settings(self.conf), {"fps": "60", "resolution": "native"})
        self.display.write_settings("max", "1440", self.conf)
        self.assertEqual(self.display.read_settings(self.conf), {"fps": "max", "resolution": "1440"})

    def test_unknown_values_are_refused_and_ignored(self):
        with self.assertRaises(ValueError):
            self.display.write_settings("240", "native", self.conf)
        self.conf.write_text("fps=240\nresolution=8k\nnoise\n")
        self.assertEqual(self.display.read_settings(self.conf), {"fps": "30", "resolution": "default"})


# ---------------------------------------------------------------------------
# Per-client tables: display_patch.c ↔ tools/rva-display-{en,jp}.json
# ---------------------------------------------------------------------------
def c_facts():
    """{region: {...}} from display_patch.c: kClients + #defines + struct inits."""
    source = C_SOURCE.read_text(encoding="utf-8")
    facts = {}
    for region, define, struct_name in (("en", "EN_LIB_SIZE", "kEnRvas"),
                                        ("jp", "JP_LIB_SIZE", "kJpRvas")):
        size = int(re.search(rf"#define {define} (\d+)LL", source).group(1))
        pkg = re.search(rf'\{{"{region}", "([^"]+)", {define}', source).group(1)
        block = re.search(rf"static const ClientRvas {struct_name} = \{{(.*?)\}};", source, re.S).group(1)
        rvas = {name: int(val, 16) for name, val in
                re.findall(r"\.(\w+)\s*=\s*(0x[0-9A-Fa-f]+)", block)}
        facts[region] = {"lib_size": size, "package": pkg, "rvas": rvas}
    return facts


def json_tables():
    """{region: {id: rva}} from tools/rva-display-{en,jp}.json."""
    out = {}
    for region in ("en", "jp"):
        table = json.loads((TABLES / f"rva-display-{region}.json").read_text(encoding="utf-8"))
        rvas = {}
        for collection in ("patches", "hooks", "related", "support_functions"):
            for entry in table.get(collection, []):
                if entry.get("rva") and int(entry["rva"], 16):
                    rvas[entry["id"]] = int(entry["rva"], 16)
        out[region] = {"meta": table["_meta"], "rvas": rvas}
    return out


class TableConsistency(unittest.TestCase):
    """RVA 表按客户端选对：同一套 JP/EN 事实表，漂移即红（无需真机/真表）。"""

    def test_c_table_matches_the_shipped_json_per_client(self):
        facts, tables = c_facts(), json_tables()
        for region in ("en", "jp"):
            self.assertEqual(facts[region]["lib_size"], tables[region]["meta"]["libil2cpp_size"], region)
            self.assertEqual(facts[region]["package"], tables[region]["meta"]["package"], region)
            for name, value in facts[region]["rvas"].items():
                if name == "hook_showrewardedvideo" and value == 0:
                    continue  # JP 未解出：warning-only skip
                self.assertIn(name, tables[region]["rvas"], f"{region}.{name} missing in JSON")
                self.assertEqual(tables[region]["rvas"][name], value, f"{region}.{name}")

    def test_fact_table_matches_detect_client_and_region_py(self):
        facts = c_facts()
        spec = importlib.util.spec_from_file_location("zh_detect_client", ZH_DETECT)
        zh = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(zh)
        sys.path.insert(0, str(TABLES))
        import region
        for region_key in ("en", "jp"):
            self.assertEqual(zh.REGIONS[region_key]["package"], facts[region_key]["package"])
            self.assertEqual(zh.REGIONS[region_key]["libil2cpp_size"], facts[region_key]["lib_size"])
            self.assertEqual(zh.region_for_lib_size(facts[region_key]["lib_size"]), region_key)
            self.assertEqual(region.REGIONS[region_key]["package"], facts[region_key]["package"])
            self.assertEqual(region.REGIONS[region_key]["libil2cpp_size"], facts[region_key]["lib_size"])


class FlyingMom(unittest.TestCase):
    """flying_mom.c's step clock and internal-call decoding, built for this computer."""

    @classmethod
    def setUpClass(cls):
        cls.dir = tempfile.TemporaryDirectory()
        harness = Path(cls.dir.name) / "harness.c"
        harness.write_text(r"""
#include <stdio.h>
#include <stdlib.h>
#include "flying_mom.h"
// clock FRAMES DELTA TOUCHES...: one line per frame, "step time" or "-".
int main(int argc, char **argv) {
    if (argv[1][0] == 's') {
        uint32_t code[16]; int n = 0;
        for (int i = 3; i < argc; i++) code[n++] = (uint32_t)strtoul(argv[i], 0, 16);
        printf("%lx\n", (unsigned long)flying_mom_icall_slot(code, strtoul(argv[2], 0, 16)));
        return 0;
    }
    FlyingMomClock clock = {0};
    int frames = atoi(argv[2]);
    for (int f = 0; f < frames; f++) {
        float delta = (float)atof(argv[3]);
        int touch = 0;
        for (int i = 4; i < argc; i++) if (atoi(argv[i]) == f) touch = 1;
        if (flying_mom_clock_tick(&clock, delta, delta, touch)) printf("step %.6f\n", clock.step_time);
        else printf("-\n");
    }
    return 0;
}
""")
        cls.binary = Path(cls.dir.name) / "harness"
        cpp = root / "android/app/src/main/cpp"
        subprocess.run(["cc", "-Wall", "-Wextra", "-Werror", "-I", str(cpp), "-o", str(cls.binary), str(harness),
                        str(cpp / "flying_mom.c")], check=True)

    @classmethod
    def tearDownClass(cls):
        cls.dir.cleanup()

    def frames(self, count, delta, touches=()):
        out = subprocess.run([str(self.binary), "clock", str(count), str(delta), *map(str, touches)],
                             check=True, capture_output=True, text=True).stdout.split("\n")[:count]
        return [None if line == "-" else float(line.split()[1]) for line in out]

    def test_at_30_fps_or_slower_every_frame_is_a_step(self):
        for delta in (1 / 30, 1 / 20):
            steps = self.frames(10, delta)
            self.assertTrue(all(s is not None for s in steps))
            self.assertAlmostEqual(steps[5], delta, places=5)

    def test_at_60_fps_every_other_frame_is_a_step_of_two_frames(self):
        steps = self.frames(12, 1 / 60)
        self.assertEqual([s is not None for s in steps], [True, False] * 6)
        self.assertAlmostEqual(steps[2], 2 / 60, places=5)

    def test_at_120_fps_every_fourth_frame_is_a_step(self):
        steps = self.frames(16, 1 / 120)
        self.assertEqual([s is not None for s in steps], [True, False, False, False] * 4)
        self.assertAlmostEqual(steps[4], 4 / 120, places=5)

    def test_a_display_a_little_over_60_hz_still_steps_every_other_frame(self):
        # 60.000004 Hz (the emulator's display): each frame is a hair under 1/60 s.
        steps = self.frames(600, 1 / 60.000004)
        self.assertEqual(sum(s is not None for s in steps), 300)
        self.assertEqual([s is not None for s in steps[-6:]], [True, False] * 3)

    def test_a_touch_on_an_in_between_frame_runs_a_step_then_keeps_30_a_second(self):
        steps = self.frames(60, 1 / 60, touches=[3, 21, 40])
        self.assertIsNotNone(steps[3])      # the tap's own frame, so its "began" isn't missed
        self.assertAlmostEqual(steps[3], 1 / 60, places=5)
        self.assertEqual(sum(s is not None for s in steps), 30)

    def test_the_time_of_every_step_adds_up_to_the_time_played(self):
        steps = self.frames(240, 1 / 120, touches=[5, 6, 50, 51, 52, 130])
        # All but the frames after the last step, which the next step covers.
        self.assertLessEqual(abs(sum(s for s in steps if s is not None) - 240 / 120), 1 / 30 + 1e-6)

    def slot(self, address, words):
        out = subprocess.run([str(self.binary), "slot", hex(address), *(hex(w) for w in words)],
                             check=True, capture_output=True, text=True).stdout
        return int(out, 16)

    def test_the_cached_pointer_of_time_get_delta_time_is_found(self):
        # 3.7.1 ARM64 Time.get_deltaTime at 0x4d7ecf4: "adrp x19, 0x79a0000; ldr x0, [x19, #0xc78]".
        words = [0xf81e0ff3, 0xa9017bfd, 0x910043fd, 0xd0016113, 0xf9463e60, 0xb50000a0]
        self.assertEqual(self.slot(0x4d7ecf4, words), 0x79a0c78)

    def test_code_that_is_not_an_internal_call_wrapper_gives_nothing(self):
        # Flying Mama's OnUpdateFreeFall: the adrp is followed by ldrb, not a pointer load.
        words = [0xfc1c0fea, 0x6d0123e9, 0xa9024ff4, 0xa9037bfd, 0x9100c3fd, 0xf0028354, 0x396d7288, 0xaa0003f3]
        self.assertEqual(self.slot(0x291d5c4, words), 0)


@unittest.skipUnless(os.environ.get("BUNKER_GAME_LIB"), "set BUNKER_GAME_LIB to a 3.7.1 libil2cpp.so")
class GameBinary(unittest.TestCase):
    """RVA 表按客户端选对（真表实证）：本客户端表全过、对面表必拒。"""

    @classmethod
    def setUpClass(cls):
        cls.path = Path(os.environ["BUNKER_GAME_LIB"])
        cls.data = cls.path.read_bytes()
        size = cls.path.stat().st_size
        facts = c_facts()
        cls.client = next((r for r in facts if facts[r]["lib_size"] == size), None)
        if cls.client is None:
            raise unittest.SkipTest(f"libil2cpp.so size {size} is not a known client")
        cls.other = "jp" if cls.client == "en" else "en"
        cls.tables = json_tables()

    def test_every_site_holds_the_expected_instruction(self):
        table = json.loads((TABLES / f"rva-display-{self.client}.json").read_text(encoding="utf-8"))
        sites = [(int(e["rva"], 16), [int(w, 16) for w in e["original_bytes"]])
                 for collection in ("patches", "hooks") for e in table[collection]]
        self.assertEqual(len(sites), 11)  # 7 patch + 4 hook（分客户端表）
        for rva, original in sites:
            # The library's first segment maps at address 0 with file offset 0.
            self.assertEqual(list(struct.unpack_from(f"<{len(original)}I", self.data, rva)), original, hex(rva))

    def test_the_other_clients_table_is_refused(self):
        """选对 = 本表过；错表（对面客户端 RVA）必拒，绝不混表。"""
        other = self.tables[self.other]["rvas"]
        mismatches = 0
        for name, rva in other.items():
            if name not in self.tables[self.client]["rvas"]:
                continue
            want = self.tables[self.client]["rvas"][name]
            if want == rva:
                continue  # 同址站点（理论上不存在）不参与
            # 对面 RVA 处放的必不是本表 original（打补丁前哨检查即拒）
            here = struct.unpack_from("<I", self.data, rva)[0]
            mine = struct.unpack_from("<I", self.data, want)[0]
            if here != mine:
                mismatches += 1
        self.assertGreater(mismatches, 0, "the wrong client's table matched the binary")

    def test_event_zone_methods_are_where_the_patch_calls_them(self):
        sup = {e["id"]: int(e["rva"], 16)
               for e in json.loads((TABLES / f"rva-display-{self.client}.json").read_text(encoding="utf-8"))
               ["support_functions"]}
        prologue = [0xf81d0ff5, 0xa9014ff4, 0xa9027bfd, 0x910083fd]
        # EventTriggerOnStayCollision.OnStateBegin and OnStay.
        for rva in (sup["stay_begin"], sup["stay_on_stay"]):
            self.assertEqual(list(struct.unpack_from("<4I", self.data, rva)), prologue, hex(rva))
        # StateConductor.OnStateUpdate, the empty virtual the patch replaces: "ret".
        self.assertEqual(struct.unpack_from("<I", self.data, sup["empty_onstateupdate"])[0], 0xd65f03c0)


if __name__ == "__main__":
    unittest.main()
