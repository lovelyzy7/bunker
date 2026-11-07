#!/usr/bin/env python3
"""The site's build code and page: what the fork's builder promises.

- The page names both master files and says the Japanese APK takes the
  Japanese master data (20240405123139.bin.e).
- Master data is identified by its contents, not its name (a browser names a
  second download "20240405123139.bin (1).e"); a file too large to be master
  data is refused unread.
- The worker preloads the builder sources as one sources.zip and fetches only
  the detected client's font payload (worker.js's contract).
"""
import ast
import unittest
from pathlib import Path
import tempfile

import msgpack

import build_site


def added_paths(source):
    """Folders a file puts on sys.path as Path(__file__).resolve().parents[N] / "name"."""  # noqa: E501
    folders = []
    for node in ast.walk(ast.parse(source.read_text(encoding="utf-8"))):
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Div) and isinstance(node.right, ast.Constant) \
                and isinstance(node.left, ast.Subscript) and isinstance(node.left.value, ast.Attribute) \
                and node.left.value.attr == "parents" and isinstance(node.left.slice, ast.Constant):
            folders.append(source.resolve().parents[node.left.slice.value] / node.right.value)
    return [f for f in folders if f.is_dir()]


def synthetic_master(mission_rows, total=1_100_000):
    """A master-data file: AES-CBC of the game's key, a msgpack table-of-contents
    and a blob. Small tables are plain rows (no LZ4), as the reader allows."""
    import lz4.block  # noqa: F401  (the reader's dependency must import here too)
    from Crypto.Cipher import AES
    from Crypto.Util.Padding import pad
    blob, toc = b"", {}
    tables = {"m_costume": [[1]], "m_weapon": [[2]], "m_event_quest_chapter": [[3]],
              "m_shop": [[4]], "m_mom_banner": [[5]], "m_mission": mission_rows}
    for name, rows in tables.items():
        part = msgpack.packb(rows)
        toc[name] = (len(blob), len(part))
        blob += part
    decoded = msgpack.packb(toc) + blob
    if len(decoded) < total:
        decoded = decoded + b"\0" * (total - len(decoded))
    return AES.new(bytes.fromhex("36436230313332314545356536624265"), AES.MODE_CBC,
                   bytes.fromhex("45666341656634434165356536446141")).encrypt(pad(decoded, AES.block_size))


def mission(type_, option, detail):
    """One m_mission row: the columns region.master_edition reads (7, 10, 15)."""
    row = [0] * 16
    row[7], row[10], row[15] = type_, option, detail
    return row


class MasterHelpTest(unittest.TestCase):
    def test_the_page_names_both_master_files(self):
        page = (build_site.ROOT / "web/index.html").read_text(encoding="utf-8")
        self.assertIn("20240404193219.bin.e", page)
        self.assertIn("20240405123139.bin.e", page)
        self.assertIn('id="master-help"', page)

    def test_the_japanese_apk_takes_the_japanese_master_data(self):
        app = (build_site.ROOT / "web/app.js").read_text(encoding="utf-8")
        self.assertIn("20240405123139.bin.e", app)
        self.assertIn("master-help", app)


class MasterEditionTest(unittest.TestCase):
    """region.master_edition: the contents decide, not the name."""

    def setUp(self):
        import sys
        sys.path.insert(0, str(build_site.ROOT / "android/tools"))
        import region
        self.region = region

    def edition(self, rows, name):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / name
            path.write_bytes(synthetic_master(rows))
            return self.region.master_edition(path)

    def test_the_japanese_master_is_recognized_by_its_mission_conditions(self):
        rows = [mission(10, 198, 0), mission(6, 201, 0), mission(10, 197, 0)]
        # A browser names a second download with " (1)"; the name says nothing.
        self.assertEqual(self.edition(rows, "20240405123139.bin (1).e"), "jp")
        self.assertEqual(self.edition(rows, "master.bin.e"), "jp")

    def test_a_master_without_them_is_the_global_one(self):
        rows = [mission(10, 197, 0), mission(6, 200, 0)]
        self.assertEqual(self.edition(rows, "20240404193219.bin.e"), "en")
        self.assertEqual(self.edition(rows, "whatever.bin"), "en")

    def test_something_else_is_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "notes.txt"
            path.write_bytes(b"not master data")
            self.assertIsNone(self.region.master_edition(path))

    def test_a_resource_dump_is_refused_unread(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "resource_dump.bin.e"
            with open(path, "wb") as out:
                out.truncate(self.region.MAX_MASTER_SIZE + 1)
            self.assertIsNone(self.region.master_edition(path))


class WorkerFetchTest(unittest.TestCase):
    def test_the_worker_preloads_the_sources_as_one_zip_and_fonts_per_client(self):
        # The fork's contract (worker.js): the builder sources arrive as one
        # sources.zip and only the detected client's font payload is fetched.
        worker = (build_site.ROOT / "web/worker.js").read_text(encoding="utf-8")
        self.assertIn('"sources"', worker)
        self.assertIn("py/sources.zip", worker)
        self.assertIn('prebuiltArtifact("fonts_" + release', worker)
        self.assertIn("bundles/fonts-", worker)


class PublishedTest(unittest.TestCase):
    def test_every_local_import_is_published(self):
        published = {path for path in build_site.PYTHON if path.endswith(".py")}
        missing = []
        for path in sorted(published):
            folders = [(build_site.ROOT / path).parent] + added_paths(build_site.ROOT / path)
            for node in ast.walk(ast.parse((build_site.ROOT / path).read_text(encoding="utf-8"))):
                if isinstance(node, ast.Import):
                    names = [alias.name for alias in node.names]
                elif isinstance(node, ast.ImportFrom) and node.module and not node.level:
                    names = [node.module]
                else:
                    continue
                for name in names:
                    module = next((f / (name.split(".")[0] + ".py") for f in folders if (f / (name.split(".")[0] + ".py")).exists()), None)
                    if module:
                        relative = module.relative_to(build_site.ROOT).as_posix()
                        if relative not in published:
                            missing.append(f"{path} imports {relative}")
        self.assertEqual(missing, [])


if __name__ == "__main__":
    unittest.main()
