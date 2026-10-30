#!/usr/bin/env python3
"""Rebuilding an installed Bunker APK with a newer launcher (assemble_apk.update)."""
import json
from pathlib import Path
import tempfile
import unittest
import zipfile

import assemble_apk
import build_info
import axml
from axml import Attr, Document, Element
import privacy
from test_privacy import elf

ROOT = Path(__file__).resolve().parents[2]
GAME_APK = ROOT / "inputs/game-3.7.1.apk"
COMPANION_APK = ROOT / "android/app/build/outputs/apk/debug/app-debug.apk"
MASTER = "assets/lunar/20240404193219.bin.e"
SETTINGS = b"prefix" + b"\x01\0\0\0\x2b\0\0\0https://api.uca.cloud.unity3d.com/v1/events" + b"suffix"


def manifests():
    if GAME_APK.is_file() and COMPANION_APK.is_file():
        with zipfile.ZipFile(GAME_APK) as g, zipfile.ZipFile(COMPANION_APK) as c:
            return g.read("AndroidManifest.xml"), c.read("AndroidManifest.xml")
    # CI exercises update/signing with synthetic manifests and ELF instructions.
    def named(tag, name, children=()):
        return Element(tag, [Attr.string("name", name, assemble_apk.NAME)], children)
    pkg_attr = Attr.string("package", "com.square_enix.android_googleplay.nierspww", 0)
    pkg_attr.ns = None
    game = Element("manifest", [pkg_attr], children=[
        Element("uses-sdk"),
        *(named("uses-permission", name) for name in sorted(privacy.AD_PERMISSIONS)),
        named("uses-permission", "android.permission.INTERNET"),
        Element("application", children=[
            named("activity", ".GameActivity", [Element("intent-filter", children=[
                named("category", "android.intent.category.LAUNCHER")])]),
            named("receiver", "com.adjust.sdk.AdjustReferrerReceiver"),
            named("provider", "com.google.firebase.provider.FirebaseInitProvider"),
            *(named("provider", name) for name in assemble_apk.SDK_PROVIDERS),
        ]),
    ])
    companion = Element("manifest", children=[Element("application", children=[
        named("activity", "org.veritr1x.bunker.MainActivity")])])
    return tuple(axml.serialize(Document(root, [("android", axml.ANDROID_NS, 0)])) for root in (game, companion))


class UpdateTests(unittest.TestCase):
    def setUp(self):
        self.t = tempfile.TemporaryDirectory()
        self.addCleanup(self.t.cleanup)
        self.work = Path(self.t.name)
        self.game_manifest, self.companion_manifest = manifests()
        self.game_library = bytes(elf()[0]) + b"unrelated local-server patch"

    def installed(self, *, library=None, compression=zipfile.ZIP_STORED, settings=SETTINGS, **info_changes):
        info = {"version": "1.0.0", "gamePatch": build_info.GAME_PATCH, "portOffset": 0, "gameDex": 1,
                "bunkerLibs": ["lib/arm64-v8a/liblunar.so", "lib/arm64-v8a/libold.so"]}
        info.update(info_changes)
        path = self.work / "installed.apk"
        with zipfile.ZipFile(path, "w") as z:
            z.writestr("AndroidManifest.xml", b"patched manifest, replaced by the update")
            z.writestr("classes.dex", b"game dex")
            z.writestr(assemble_apk.LIB, self.game_library if library is None else library, compress_type=compression)
            z.writestr(assemble_apk.SETTINGS, settings)
            z.writestr("assets/bin/Data/a", b"game data")
            z.writestr("classes2.dex", b"old launcher dex")
            z.writestr("lib/arm64-v8a/liblunar.so", b"old server")
            z.writestr("lib/arm64-v8a/libold.so", b"dropped library")
            z.writestr("assets/chaquopy/old.zip", b"old python")
            z.writestr(MASTER, b"patched master")
            z.writestr("assets/lunar/original-master.bin.e", b"original master")
            z.writestr("assets/lunar/LUNAR_TEAR_LICENSE.txt", b"license")
            z.writestr("assets/lunar/game-manifest.xml", self.game_manifest)
            z.writestr("assets/lunar/build.json", json.dumps(info))
            z.writestr("META-INF/CERT.RSA", b"old signature")
        return path

    def companion(self):
        path = self.work / "bundle.zip"
        with zipfile.ZipFile(path, "w") as z:
            z.writestr("AndroidManifest.xml", self.companion_manifest)
            z.writestr("classes.dex", b"new launcher dex")
            z.writestr("lib/arm64-v8a/liblunar.so", b"new server")
            z.writestr("lib/arm64-v8a/libnew.so", b"new library")
            z.writestr("assets/chaquopy/new.zip", b"new python")
            z.writestr("assets/lunar/bunker-version.txt", b"1.1.0\n")
        return path

    def test_update_replaces_bunker_files_keeps_game(self):
        out = self.work / "out.apk"
        info = assemble_apk.update(self.installed(), self.companion(), out, log=lambda m: None)
        with zipfile.ZipFile(out) as z:
            names = set(z.namelist())
            for name, data in [("classes.dex", b"game dex"), (assemble_apk.LIB, privacy.patch_library(self.game_library)),
                               ("assets/bin/Data/a", b"game data"), (MASTER, b"patched master"),
                               ("assets/lunar/original-master.bin.e", b"original master"),
                               ("assets/lunar/game-manifest.xml", self.game_manifest),
                               ("classes2.dex", b"new launcher dex"), ("lib/arm64-v8a/liblunar.so", b"new server"),
                               ("lib/arm64-v8a/libnew.so", b"new library"), ("assets/chaquopy/new.zip", b"new python")]:
                self.assertEqual(z.read(name), data, name)
            for gone in ["lib/arm64-v8a/libold.so", "assets/chaquopy/old.zip", "META-INF/CERT.RSA"]:
                self.assertNotIn(gone, names)
            manifest = z.read("AndroidManifest.xml")
            self.assertNotEqual(manifest, b"patched manifest, replaced by the update")
            self.assertIn("org.veritr1x.bunker".encode("utf-16-le"), manifest)
            self.assertEqual(z.read(assemble_apk.SETTINGS), assemble_apk.patch_unity_connect(SETTINGS))
            root = axml.parse(manifest).root
            self.assertFalse(privacy.AD_PERMISSIONS.intersection(x.get("name").raw for x in root.find_all("uses-permission")))
            app = root.find_all("application")[0]
            self.assertFalse(privacy.TRACKING_RECEIVERS.intersection(x.get("name").raw for x in app.find_all("receiver")))
            flags = {x.get("name").raw: x.get("value") for x in app.find_all("meta-data")}
            for name, enabled in assemble_apk.SDK_SWITCHES:
                self.assertEqual(bool(flags[name].data), enabled, name)
            written = json.loads(z.read("assets/lunar/build.json"))
        self.assertEqual(written, info)
        self.assertEqual(info["version"], "1.1.0")
        self.assertEqual(info["gameDex"], 1)
        self.assertEqual(info["gamePatch"], 1)
        self.assertEqual(info["bunkerLibs"], ["lib/arm64-v8a/liblunar.so", "lib/arm64-v8a/libnew.so"])

    def test_update_keeps_port_offset(self):
        out = self.work / "out.apk"
        info = assemble_apk.update(self.installed(portOffset=7), self.companion(), out, log=lambda m: None)
        self.assertEqual(info["portOffset"], 7)

    def test_old_build_needs_web_builder(self):
        path = self.work / "old.apk"
        with zipfile.ZipFile(path, "w") as z:
            z.writestr("AndroidManifest.xml", b"x")
            z.writestr("classes.dex", b"game dex")
        with self.assertRaisesRegex(RuntimeError, "web builder"):
            assemble_apk.update(path, self.companion(), self.work / "out.apk", log=lambda m: None)
        self.assertFalse((self.work / "out.apk").exists())

    def test_game_patch_change_needs_web_builder(self):
        with self.assertRaisesRegex(RuntimeError, "web builder"):
            assemble_apk.update(self.installed(gamePatch=build_info.GAME_PATCH + 1), self.companion(),
                                self.work / "out.apk", log=lambda m: None)

    def test_update_applies_telemetry_to_revision_one_and_can_repeat(self):
        for compression in (zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED):
            with self.subTest(compression=compression):
                installed = self.installed(gamePatch=1, compression=compression)
                original = installed.read_bytes()
                out, again = self.work / "out.apk", self.work / "again.apk"
                assemble_apk.update(installed, self.companion(), out, log=lambda m: None)
                self.assertEqual(installed.read_bytes(), original)
                assemble_apk.update(out, self.companion(), again, log=lambda m: None)
                with zipfile.ZipFile(out) as first, zipfile.ZipFile(again) as second:
                    for name in (assemble_apk.LIB, assemble_apk.SETTINGS, "AndroidManifest.xml"):
                        self.assertEqual(first.read(name), second.read(name), name)
                    self.assertEqual(second.read(assemble_apk.LIB), privacy.patch_library(self.game_library))
                    self.assertEqual(second.getinfo(assemble_apk.LIB).compress_type, compression)
                    self.assertEqual(json.loads(second.read("assets/lunar/build.json"))["gamePatch"], 1)

    def test_unknown_library_does_not_replace_output_or_leave_partial(self):
        library, offsets = elf()
        library[offsets[-1] + 12] ^= 1
        installed = self.installed(library=library)
        original = installed.read_bytes()
        out = self.work / "out.apk"
        out.write_bytes(b"previous output")
        with self.assertRaisesRegex(ValueError, "Unsupported game binary"):
            assemble_apk.update(installed, self.companion(), out, log=lambda m: None)
        self.assertEqual(installed.read_bytes(), original)
        self.assertEqual(out.read_bytes(), b"previous output")
        self.assertFalse(out.with_suffix(".apk.partial").exists())

    def test_update_keeps_the_installed_notices(self):
        out = self.work / "out.apk"
        info = assemble_apk.update(self.installed(notices="abc"), self.companion(), out, log=lambda m: None)
        with zipfile.ZipFile(out) as z:
            self.assertEqual(z.read("assets/lunar/LUNAR_TEAR_LICENSE.txt"), b"license")

    def test_update_turns_unity_connect_off(self):
        settings = b"head\x01\0\0\0\x2b\0\0\0https://api.uca.cloud.unity3d.com/v1/events\0tail"
        path = self.installed(settings=settings)
        out = self.work / "out.apk"
        assemble_apk.update(path, self.companion(), out, log=lambda m: None)
        with zipfile.ZipFile(out) as z:
            self.assertEqual(z.read(assemble_apk.SETTINGS), assemble_apk.patch_unity_connect(settings))


class DeviceBuildTests(unittest.TestCase):
    """bunker_update.build_android, as the launcher runs it (with the tools importable as bunker_tools)."""

    def setUp(self):
        import sys
        import types
        self.t = tempfile.TemporaryDirectory()
        self.addCleanup(self.t.cleanup)
        self.work = Path(self.t.name)
        package = types.ModuleType("bunker_tools")
        package.__path__ = [str(Path(__file__).resolve().parent)]
        sys.modules["bunker_tools"] = package
        sys.path.insert(0, str(ROOT / "android/app/src/main/python"))
        import bunker_update
        self.bunker_update = bunker_update
        self.case = UpdateTests("test_update_keeps_port_offset")
        self.case.setUp()
        self.addCleanup(self.case.doCleanups)

    def test_damaged_download_is_refused(self):
        bundle = self.case.companion()
        with self.assertRaisesRegex(RuntimeError, "damaged"):
            self.bunker_update.build_android(self.case.installed(), bundle, "0" * 64, self.work / "update",
                                             ROOT / "web/signing/bunker-key.pem", ROOT / "web/signing/bunker-cert.der", print)
        self.assertFalse(any((self.work / "update").glob("*.apk")))

    def test_builds_and_signs(self):
        import hashlib
        bundle = self.case.companion()
        digest = hashlib.sha256(bundle.read_bytes()).hexdigest()
        apk = Path(self.bunker_update.build_android(self.case.installed(), bundle, digest, self.work / "update",
                                                    ROOT / "web/signing/bunker-key.pem", ROOT / "web/signing/bunker-cert.der",
                                                    lambda m: None))
        self.assertTrue(apk.is_file())
        self.assertIn(b"APK Sig Block 42", apk.read_bytes())


if __name__ == "__main__":
    unittest.main()
