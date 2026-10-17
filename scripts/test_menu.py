#!/usr/bin/env python3
"""Finding the Mod Menu checkout and staging an APK for re-signing."""
import os
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "android/tools"))

import menu  # noqa: E402


class RootTest(unittest.TestCase):
    def setUp(self):
        self.t = tempfile.TemporaryDirectory()
        self.addCleanup(self.t.cleanup)
        self.checkout = Path(self.t.name) / "bunker-modmenu"
        (self.checkout / "jp-client/tools").mkdir(parents=True)
        (self.checkout / "en-client/tools").mkdir(parents=True)
        (self.checkout / "README.md").write_text("menu")
        for client in ("jp-client", "en-client"):
            (self.checkout / client / "tools/build_all.py").write_text("raise SystemExit")

    def test_finds_a_checkout_from_the_argument(self):
        self.assertEqual(menu.root(self.checkout), self.checkout.resolve())

    def test_finds_it_from_the_environment(self):
        with mock.patch.dict(os.environ, {"BUNKER_MODMENU": str(self.checkout)}):
            self.assertEqual(menu.root(), self.checkout.resolve())

    def test_explains_how_to_get_the_sources(self):
        with mock.patch.dict(os.environ, {"BUNKER_MODMENU": ""}), \
                mock.patch.object(menu, "DEFAULT_ROOT", Path(self.t.name) / "absent"):
            with self.assertRaises(SystemExit) as caught:
                menu.root()
        self.assertIn("bunker-modmenu", str(caught.exception))

    def test_each_release_has_its_own_workspace(self):
        self.assertEqual(menu.injector("jp", self.checkout).parent.parent.name, "jp-client")
        self.assertEqual(menu.injector("en", self.checkout).parent.parent.name, "en-client")
        with self.assertRaises(SystemExit):
            menu.injector("xx", self.checkout)

    def test_refuses_an_incomplete_checkout(self):
        (self.checkout / "jp-client/tools/build_all.py").unlink()
        with self.assertRaises(SystemExit):
            menu.injector("jp", self.checkout)


class StripTest(unittest.TestCase):
    def test_drops_only_old_signatures(self):
        with tempfile.TemporaryDirectory() as work:
            work = Path(work)
            source = work / "signed.apk"
            with zipfile.ZipFile(source, "w") as z:
                z.writestr("AndroidManifest.xml", "m")
                z.writestr("classes.dex", "d")
                z.writestr("META-INF/MANIFEST.MF", "x")
                z.writestr("META-INF/CERT.SF", "x")
                z.writestr("META-INF/CERT.RSA", "x")
                z.writestr("META-INF/androidx.core_core.version", "1")
            target = work / "stripped.apk"
            menu._strip_signatures(source, target)
            with zipfile.ZipFile(target) as z:
                names = set(z.namelist())
            self.assertIn("AndroidManifest.xml", names)
            self.assertIn("classes.dex", names)
            self.assertIn("META-INF/androidx.core_core.version", names)  # not a signature
            self.assertNotIn("META-INF/CERT.SF", names)
            self.assertNotIn("META-INF/CERT.RSA", names)
            self.assertNotIn("META-INF/MANIFEST.MF", names)


class BuildToolsTest(unittest.TestCase):
    def test_picks_the_newest_build_tools_that_can_sign(self):
        with tempfile.TemporaryDirectory() as work:
            sdk = Path(work)
            (sdk / "build-tools/34.0.0").mkdir(parents=True)
            (sdk / "build-tools/34.0.0/apksigner").write_text("")
            (sdk / "build-tools/36.1.0").mkdir()
            (sdk / "build-tools/36.1.0/apksigner").write_text("")
            (sdk / "build-tools/37.0.0").mkdir()  # no apksigner: unusable
            self.assertEqual(menu._build_tools(sdk).name, "36.1.0")

    def test_reports_a_missing_sdk(self):
        with tempfile.TemporaryDirectory() as work:
            with self.assertRaises(SystemExit) as caught:
                menu._build_tools(Path(work))
        self.assertIn("build-tools", str(caught.exception))


if __name__ == "__main__":
    unittest.main()
