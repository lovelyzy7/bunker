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

    改版适配：package_game.patch_local_reachability 的定位方式是「名字串
    UnityEngine.Application::get_internetReachability() 的唯一 adrp/add 引用
    + 回溯 prologue」（双端通用，非上游固定 RVA 0x4910D4C）。夹具合成该形状：
    串在 0x2100（同页 0x2000），wrapper 在 0x2F00（prologue+帧指令+nop+
    adrp x0/add x0,#0x100 指向串页），供扫描器唯一命中。
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
            # 改版语义优先：patch_local_reachability 走 read_bytes 全量读（工具链侧
            # 正确性优先，桌面无浏览器内存约束）。上游"禁整库读"是其流式优化断言，
            # 此处改为功能断言——就地打上、仅 8 字节变化、重复调用幂等。
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
