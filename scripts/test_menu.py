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



class ManifestTest(unittest.TestCase):
    """The menu's manifest edits, on a real binary manifest."""

    def _manifest(self, menu):
        sys.path.insert(0, str(ROOT / "android/tools"))
        import assemble_apk
        game = ROOT / ".build/jp-e2e/game-en.apk"
        if not game.is_file():
            self.skipTest("the game APK is not available")
        with zipfile.ZipFile(game) as apk, zipfile.ZipFile(ROOT / "android/app/build/outputs/apk/debug/app-debug.apk") as companion:
            manifest, activity = assemble_apk.patch_manifest(apk.read("AndroidManifest.xml"),
                                                             companion.read("AndroidManifest.xml"),
                                                             0, menu=menu)
        import axml
        return axml.parse(manifest).root, activity

    def test_without_the_menu_nothing_changes(self):
        root, activity = self._manifest(False)
        app = [c for c in root.children if getattr(c, "name", None) == "application"][0]
        names = [s.get("name").raw for s in app.children if getattr(s, "name", None) == "service"]
        self.assertNotIn("com.android.support.Launcher", names)
        self.assertEqual(activity, "com.google.firebase.MessagingUnityPlayerActivity")

    def test_with_the_menu_the_launcher_becomes_the_shim(self):
        root, activity = self._manifest(True)
        app = [c for c in root.children if getattr(c, "name", None) == "application"][0]
        self.assertEqual(activity, "org.veritr1x.bunker.MenuShim")
        services = {s.get("name").raw: s for s in app.children if getattr(s, "name", None) == "service"}
        self.assertIn("com.android.support.Launcher", services)
        self.assertEqual(services["com.android.support.Launcher"].get("stopWithTask").data, 0xFFFFFFFF)
        permissions = [p.get("name").raw for p in root.children if getattr(p, "name", None) == "uses-permission"]
        self.assertIn("android.permission.SYSTEM_ALERT_WINDOW", permissions)
        meta = {m.get("name").raw: m for m in app.children if getattr(m, "name", None) == "meta-data"}
        self.assertEqual(meta["org.veritr1x.bunker.GAME_ACTIVITY"].get("value").raw, "org.veritr1x.bunker.MenuShim")
        self.assertEqual(meta["org.veritr1x.bunker.MOD_MENU"].get("value").raw, "true")


class PayloadTest(unittest.TestCase):
    def test_payload_has_both_releases_and_the_shim(self):
        sys.path.insert(0, str(ROOT / "web"))
        import webbuild
        for release in ("jp", "en"):
            menu = webbuild.menu_payload(ROOT / "web/modmenu", release)
            self.assertIsNotNone(menu)
            self.assertGreaterEqual(len(menu["dex"]), 2, release)  # shim + the menu's own
            self.assertTrue(menu["lib"].startswith(b"\x7fELF"), release)

    def test_a_missing_payload_is_reported_not_fatal(self):
        sys.path.insert(0, str(ROOT / "web"))
        import webbuild
        self.assertIsNone(webbuild.menu_payload(None, "en"))
        self.assertIsNone(webbuild.menu_payload(ROOT / "nope.zip", "en"))

if __name__ == "__main__":
    unittest.main()
