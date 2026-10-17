#!/usr/bin/env python3
"""Region detection and the release-agnostic library locator."""
import io
import struct
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "android/tools"))

import axml  # noqa: E402
import package_game  # noqa: E402
import region  # noqa: E402

PROLOGUE = bytes.fromhex("f30f1ef8fd7b01a9fd430091738401b0")  # str x19; stp x29,x30; mov x29,sp


def manifest(package):
    """A minimal compiled manifest carrying one package name."""
    # A real manifest's package attribute carries no namespace.
    doc = axml.Document(axml.Element("manifest", [axml.Attr("package", ns=None, resid=0, raw=package)]), [])
    return axml.serialize(doc)


def apk_with(package):
    """A zip that looks like an APK to the detector."""
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as apk:
        apk.writestr("AndroidManifest.xml", manifest(package))
    return buffer.getvalue()


class RegionTest(unittest.TestCase):
    def test_detects_the_game_releases(self):
        self.assertEqual(region.region_for_package(region.EN_PACKAGE), "en")
        self.assertEqual(region.region_for_package(region.JP_PACKAGE), "jp")

    def test_reads_the_package_from_an_apk(self):
        for key, info in region.REGIONS.items():
            with tempfile.TemporaryDirectory() as work:
                path = Path(work) / "game.apk"
                path.write_bytes(apk_with(info["package"]))
                self.assertEqual(region.region_of_apk(path), (key, info["package"]))

    def test_refuses_another_app(self):
        with tempfile.TemporaryDirectory() as work:
            path = Path(work) / "other.apk"
            path.write_bytes(apk_with("com.example.other"))
            with self.assertRaises(SystemExit):
                region.region_of_apk(path)

    def test_region_override_must_agree(self):
        self.assertEqual(region.resolve("auto", "jp"), "jp")
        self.assertEqual(region.resolve(None, "en"), "en")
        self.assertEqual(region.resolve("jp", "jp"), "jp")
        with self.assertRaises(SystemExit):
            region.resolve("en", "jp")

    def test_every_region_names_its_patcher(self):
        for key, info in region.REGIONS.items():
            self.assertTrue((ROOT / info["patcher"]).is_file(), f"{key}: {info['patcher']}")


def synthetic_library(name_at=0x8000, wrapper_at=0x1000):
    """An ELF64 ARM64 blob whose one wrapper computes the address of name_at."""
    name = package_game.REACHABILITY_NAME
    data = bytearray(max(wrapper_at + 0x40, name_at + len(name)))
    data[0:6] = b"\x7fELF\x02\x01"
    struct.pack_into("<H", data, 18, 183)
    data[name_at:name_at + len(name)] = name
    adrp_at = wrapper_at + 12
    page = name_at & ~0xFFF
    imm = (page - (adrp_at & ~0xFFF)) >> 12  # the page adrp must add, in 4 KB units
    adrp = 0x90000000 | ((imm & 0x3) << 29) | (((imm >> 2) & 0x7FFFF) << 5) | 19
    add = 0x91000000 | ((name_at & 0xFFF) << 10) | (19 << 5) | 19
    data[wrapper_at:wrapper_at + 8] = PROLOGUE[:8]
    struct.pack_into("<I", data, wrapper_at + 8, 0x910043FD)  # add x29, sp, #0x10
    struct.pack_into("<I", data, adrp_at, adrp)
    struct.pack_into("<I", data, adrp_at + 4, add)
    return bytes(data)


class ReachabilityTest(unittest.TestCase):
    def test_finds_the_wrapper_from_the_name_string(self):
        data = synthetic_library()
        self.assertEqual(package_game.reachability_wrapper(data), 0x1000)

    def test_patch_writes_the_lan_value(self):
        data = synthetic_library()
        with tempfile.TemporaryDirectory() as work:
            game = Path(work)
            (game / "lib/arm64-v8a").mkdir(parents=True)
            (game / "lib/arm64-v8a/libil2cpp.so").write_bytes(data)
            package_game.patch_local_reachability(game)
            patched = (game / "lib/arm64-v8a/libil2cpp.so").read_bytes()
        self.assertEqual(patched[0x1000:0x1008], bytes.fromhex("40008052c0035fd6"))

    def test_refuses_a_library_without_the_name(self):
        data = bytearray(synthetic_library())
        data[0x8000:] = b"\0" * (len(data) - 0x8000)
        with self.assertRaises(RuntimeError):
            package_game.reachability_wrapper(bytes(data))

    def test_real_game_library_at_both_releases(self):
        """The patcher's own RVA table must agree with what the locator finds."""
        for tag, expected in (("en", 0x4910D4C), ("jp", 0x4883AB0)):
            path = ROOT / ".build/apks" / f"{tag}-libil2cpp.so"
            if not path.is_file():
                continue  # The game's libraries are not part of the repository.
            data = path.read_bytes()
            self.assertEqual(package_game.reachability_wrapper(data), expected, tag)
            # The prologue the patcher checks must be there. Only the first
            # three instructions can match: the adrp that follows points at a
            # page, which differs between releases.
            self.assertEqual(data[expected:expected + 12], PROLOGUE[:12])


if __name__ == "__main__":
    unittest.main()
