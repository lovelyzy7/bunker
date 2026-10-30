#!/usr/bin/env python3
"""Phase 1 switch unit tests: lunar-scripts-zh call-face, dispatch gate, adapter.

Covers the regression-risk surface of BUNKER-ADAPT-PLAN §1.7.2:
* region.py REGIONS points at the zh dual front-ends (not lunar-scripts(-jp));
* bunker REGIONS facts and zh detect_client facts agree (drift refuses);
* zh_client.dispatch fail-fast behavior (unknown / expect contradiction /
  table disagreement) and strict=False override shape;
* patch_masterdata_zh key/IV compat face and filename-invariant staging rule;
* upstream.lock.json kind=directory pin agrees with prepare.py's contract
  digest (the git-less equivalent of the submodule commit pin).

Run: python scripts/test_zh_switch.py   (from bunker/)
"""
import json
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "android/tools"))
sys.path.insert(0, str(ROOT / "scripts"))

import axml  # noqa: E402
import patch_masterdata_zh  # noqa: E402
import prepare  # noqa: E402
import region  # noqa: E402
import zh_client  # noqa: E402


def manifest(package):
    doc = axml.Document(axml.Element("manifest", [axml.Attr("package", ns=None, resid=0, raw=package)]), [])
    return axml.serialize(doc)


def apk_with(package):
    import io
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as apk:
        apk.writestr("AndroidManifest.xml", manifest(package))
    return buffer.getvalue()


class RegionsRedirectTest(unittest.TestCase):
    """§1.7.2 #1/#2: REGIONS patcher paths are the lunar-scripts-zh front-ends."""

    def test_patchers_are_the_zh_dual_front_ends(self):
        self.assertEqual(region.REGIONS["en"]["patcher"],
                         "upstream/lunar-scripts-zh/en-client/patches/patch_apk_en.py")
        self.assertEqual(region.REGIONS["jp"]["patcher"],
                         "upstream/lunar-scripts-zh/jp-client/patches/patch_apk_jp.py")

    def test_patchers_exist_on_disk(self):
        for key, info in region.REGIONS.items():
            self.assertTrue((ROOT / info["patcher"]).is_file(), f"{key}: {info['patcher']}")

    def test_no_original_lunar_scripts_paths_left_in_regions(self):
        blob = json.dumps(region.REGIONS)
        # Split so this assertion file itself carries no call-face path literal.
        self.assertNotIn("upstream/lunar-scripts" + "/", blob)
        self.assertNotIn("upstream/lunar-scripts" + "-jp/", blob)

    def test_key_and_product_facts_present(self):
        for key, info in region.REGIONS.items():
            self.assertEqual(info["product"], f"nier-{key}.apk")
            self.assertTrue(info["keystore"].startswith(f"{info['client']}/keys/"))
            self.assertTrue(info["key_alias"] and info["key_pass"])
            self.assertRegex(info["cert_sha256"], r"^[0-9a-f]{64}$")


class FactsAgreeTest(unittest.TestCase):
    """The two REGIONS tables must agree; drift refuses at dispatch time."""

    def test_zh_detect_client_facts_match_bunker_regions(self):
        dc = zh_client.detect_module()
        for key, mine in region.REGIONS.items():
            theirs = dc.REGIONS[key]
            self.assertEqual(mine["package"], theirs["package"], key)
            self.assertEqual(mine["size"], theirs["bytes"], key)
            self.assertEqual(mine["sha256"], theirs["sha256"], key)
            self.assertEqual(mine["libil2cpp_size"], theirs["libil2cpp_size"], key)
            self.assertEqual(mine["product"], theirs["product_name"], key)
            self.assertEqual(mine["cert_sha256"], theirs["cert_sha256"], key)
            self.assertEqual(mine["keystore"], theirs["keystore"], key)
            self.assertEqual(mine["key_alias"], theirs["ks_alias"], key)
            self.assertEqual(mine["key_pass"], theirs["ks_pass"], key)


class DispatchTest(unittest.TestCase):
    """zh_client.dispatch: fail-fast gates and the strict=False override shape."""

    def test_unknown_package_refused(self):
        with tempfile.TemporaryDirectory() as work:
            path = Path(work) / "other.apk"
            path.write_bytes(apk_with("com.example.other"))
            with self.assertRaises(SystemExit):
                zh_client.dispatch(path)

    def test_expect_contradiction_refused(self):
        with tempfile.TemporaryDirectory() as work:
            path = Path(work) / "jp.apk"
            path.write_bytes(apk_with(region.JP_PACKAGE))
            with self.assertRaises(SystemExit):
                zh_client.dispatch(path, expect="en", strict=False)

    def test_override_dispatch_returns_the_contract_profile(self):
        for key, info in region.REGIONS.items():
            with tempfile.TemporaryDirectory() as work:
                path = Path(work) / "game.apk"
                path.write_bytes(apk_with(info["package"]))
                profile = zh_client.dispatch(path, strict=False)
                self.assertEqual(profile["region"], key)
                self.assertEqual(profile["product_name"], f"nier-{key}.apk")
                self.assertEqual(profile["key_alias"], info["key_alias"])
                self.assertEqual(profile["patcher"], info["patcher"])
                self.assertTrue(Path(profile["patcher_path"]).is_file())
                self.assertTrue(Path(profile["keystore"]).is_file())
                self.assertFalse(profile["strict"])

    def test_patch_must_point_at_zh_otherwise_refused(self):
        # Simulate a stale REGIONS entry (pre-redirect path) → the dispatch
        # semantic assertion must refuse. Built by concatenation so this file
        # carries no call-face path literal.
        stale = "upstream/lunar-scripts" + "-jp/android/patch_apk_jp.py"
        saved = region.REGIONS["jp"]["patcher"]
        try:
            region.REGIONS["jp"]["patcher"] = stale
            with tempfile.TemporaryDirectory() as work:
                path = Path(work) / "jp.apk"
                path.write_bytes(apk_with(region.JP_PACKAGE))
                with self.assertRaises(SystemExit):
                    zh_client.dispatch(path, strict=False)
        finally:
            region.REGIONS["jp"]["patcher"] = saved

    def test_table_disagreement_refused(self):
        saved = region.REGIONS["jp"]["cert_sha256"]
        try:
            region.REGIONS["jp"]["cert_sha256"] = "0" * 64
            with tempfile.TemporaryDirectory() as work:
                path = Path(work) / "jp.apk"
                path.write_bytes(apk_with(region.JP_PACKAGE))
                with self.assertRaises(SystemExit):
                    zh_client.dispatch(path, strict=False)
        finally:
            region.REGIONS["jp"]["cert_sha256"] = saved


class AdapterContractTest(unittest.TestCase):
    """patch_masterdata_zh: the old patch_masterdata.py CLI face, adapted."""

    def test_rejects_non_builtin_key(self):
        with self.assertRaises(SystemExit):
            patch_masterdata_zh._check_key_iv(type("A", (), {
                "key": "00" * 16, "iv": None, "key_file": None, "iv_file": None})())

    def test_rejects_non_builtin_iv(self):
        with self.assertRaises(SystemExit):
            patch_masterdata_zh._check_key_iv(type("A", (), {
                "key": None, "iv": "11" * 16, "key_file": None, "iv_file": None})())

    def test_accepts_builtin_key_iv(self):
        patch_masterdata_zh._check_key_iv(type("A", (), {
            "key": patch_masterdata_zh.BUILTIN_KEY_HEX, "iv": patch_masterdata_zh.BUILTIN_IV_HEX,
            "key_file": None, "iv_file": None})())

    def test_missing_input_is_fail_fast(self):
        with self.assertRaises(SystemExit):
            patch_masterdata_zh.patch_file("no-such.bin.e", "out.bin.e")

    def test_target_build_bin_e_is_the_zh_one(self):
        self.assertIn("lunar-scripts-zh", str(patch_masterdata_zh.ZH_BUILD_BIN_E))
        self.assertTrue(patch_masterdata_zh.ZH_BUILD_BIN_E.is_file())
        self.assertTrue(patch_masterdata_zh.ZH_BIN_EDIT_DEFAULT.is_file())


class UpstreamRegistrationTest(unittest.TestCase):
    """kind=directory pin = the git-less equivalent of the submodule commit pin."""

    def test_lock_entry_shape(self):
        pins = json.loads((ROOT / "upstream.lock.json").read_text(encoding="utf-8"))
        entry = pins["lunar-scripts-zh"]
        self.assertEqual(entry["kind"], "directory")
        self.assertFalse(entry["git"])
        self.assertEqual(entry["path"], "upstream/lunar-scripts-zh")
        self.assertEqual(entry["pin"]["mode"], "contract-digest")

    def test_pin_files_match_prepare_contract(self):
        pins = json.loads((ROOT / "upstream.lock.json").read_text(encoding="utf-8"))
        self.assertEqual(tuple(pins["lunar-scripts-zh"]["pin"]["files"]),
                         tuple(sorted(prepare.ZH_CONTRACT_FILES)))

    def test_pin_digest_recomputes(self):
        pins = json.loads((ROOT / "upstream.lock.json").read_text(encoding="utf-8"))
        self.assertEqual(prepare.check_zh_module("lunar-scripts-zh", pins["lunar-scripts-zh"]),
                         pins["lunar-scripts-zh"]["pin"]["sha256"])

    def test_gitmodules_registers_the_directory_form(self):
        text = (ROOT / ".gitmodules").read_text(encoding="utf-8")
        self.assertIn('upstream-local "upstream/lunar-scripts-zh"', text)
        self.assertIn("upstream.lock.json#lunar-scripts-zh", text)


if __name__ == "__main__":
    unittest.main(verbosity=2)
