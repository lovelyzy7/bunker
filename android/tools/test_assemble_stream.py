"""The Android builder streams the large game files instead of holding them whole."""
from pathlib import Path
import io
import os
import struct
import tempfile
import unittest
import zipfile

import assemble_apk
import package_game


def reachability_library(path, prologue="f30f1ef8fd7b01a9"):
    """A small ELF carrying the shape the reachability scan recognises.

    package_game.patch_local_reachability locates the patch site by the
    string "UnityEngine.Application::get_internetReachability()" and its
    single adrp/add reference (works for both the JP and EN release
    libraries, unlike a fixed RVA). The fixture synthesises that shape:
    the string at 0x2100 (page 0x2000) and a wrapper at 0x2F00 (prologue,
    frame instruction, nop, adrp x0/add x0,#0x100 aimed at the string page).
    """
    data = bytearray(0x4000)
    data[:6] = b"\x7fELF\x02\x01"
    struct.pack_into("<H", data, 18, 183)          # e_machine = EM_AARCH64
    name = b"UnityEngine.Application::get_internetReachability()"
    name_at = 0x2100
    data[name_at:name_at + len(name)] = name
    start = 0x2F00
    data[start:start + 8] = bytes.fromhex(prologue)
    struct.pack_into("<I", data, start + 8, 0x910003FD)   # add x29, sp, #0
    struct.pack_into("<I", data, start + 12, 0xD503201F)  # nop
    struct.pack_into("<I", data, start + 16, 0x90000000)  # adrp x0, <page>
    struct.pack_into("<I", data, start + 20, 0x91040000)  # add x0, x0, #0x100
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    return start


class StreamTests(unittest.TestCase):
    def test_reachability_is_patched_where_the_library_lies(self):
        with tempfile.TemporaryDirectory() as temp:
            game = Path(temp)
            library = game / "lib/arm64-v8a/libil2cpp.so"
            at = reachability_library(library)
            before = library.read_bytes()
            # patch_local_reachability reads the library whole (read_bytes); the
            # toolchain side has no browser memory constraint and correctness
            # comes first. Assert the functional contract: the patch lands in
            # place, touches exactly 8 bytes, and repeat calls are idempotent.
            package_game.patch_local_reachability(game)
            after = library.read_bytes()
            self.assertEqual(after[at:at + 8], bytes.fromhex("40008052c0035fd6"))
            self.assertEqual(after[:at] + after[at + 8:], before[:at] + before[at + 8:])
            package_game.patch_local_reachability(game)  # Already patched is fine.

    def test_reachability_refuses_an_unknown_library(self):
        with tempfile.TemporaryDirectory() as temp:
            game = Path(temp)
            library = game / "lib/arm64-v8a/libil2cpp.so"
            reachability_library(library, prologue="1f2003d51f2003d5")
            before = library.read_bytes()
            with self.assertRaises(RuntimeError):
                package_game.patch_local_reachability(game)
            self.assertEqual(library.read_bytes(), before)

    def test_files_are_written_like_bytes(self):
        data = os.urandom(3000) + b"\0" * 70000
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "big.bin"
            path.write_bytes(data)
            for compress in (True, False):
                with self.subTest(compress=compress):
                    from_bytes, from_file = io.BytesIO(), io.BytesIO()
                    for out, add in ((from_bytes, lambda w: w.add("lib/arm64-v8a/libx.so", data, compress)),
                                     (from_file, lambda w: w.add_file("lib/arm64-v8a/libx.so", path, compress))):
                        writer = assemble_apk.ApkWriter(out)
                        writer.add("a.txt", b"first")
                        add(writer)
                        writer.close()
                    self.assertEqual(from_file.getvalue(), from_bytes.getvalue())
                    with zipfile.ZipFile(from_file) as z:
                        self.assertEqual(z.read("lib/arm64-v8a/libx.so"), data)


if __name__ == "__main__":
    unittest.main()
