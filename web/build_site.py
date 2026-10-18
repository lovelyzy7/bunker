#!/usr/bin/env python3
"""Assemble the in-browser builder as a static site.

  build_site.py --companion-apk APK [--output DIR]

The site holds the page, the Python build code and the Android launcher bundle
built from this repository. Master data is stripped from it; the player
supplies it. No game files are included, and there is no iOS build at all.
Serve the output folder over HTTP to test it.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
PYTHON = [
    "LICENSE",
    "web/webbuild.py",
    "android/tools/apk_sign.py",
    "android/tools/axml.py",
    "android/tools/assemble_apk.py",
    "android/tools/build_info.py",
    "android/tools/command.py",
    "android/tools/package_game.py",
    "android/tools/region.py",
    "upstream/lunar-scripts/android/patch_apk.py",
    "upstream/lunar-scripts-jp/android/patch_apk_jp.py",
    "upstream/lunar-scripts/patch_masterdata.py",
    "web/signing/bunker-key.pem",
    "web/signing/bunker-cert.der",
]
PAGES_LIMIT = 100 * 1024 * 1024  # GitHub Pages refuses larger files.
# The same launcher bundle is attached to the release, so the page can offer a
# GitHub download proxy for networks where this site is slow. A direct fetch of
# the asset is not possible (GitHub sends no CORS header), which is why the page
# goes through a proxy the reader supplies; the bytes are checked against the
# digest below. --mirror adds another source (the Pages workflow passes the
# BUNDLE_MIRROR repository variable); it must send a CORS header too.
REPO = "lovelyzy7/bunker"

# A second copy of bundles/android.zip may be given with --mirror.


def is_master(name):
    return name.endswith(".bin.e")


def android_bundle(companion_apk, target):
    with zipfile.ZipFile(companion_apk) as source, zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as out:
        for name in source.namelist():
            wanted = name == "AndroidManifest.xml" or re.fullmatch(r"classes\d*\.dex", name) \
                or name.startswith(("lib/arm64-v8a/", "assets/chaquopy/", "assets/lunar/"))
            if wanted and not is_master(name):
                out.writestr(name, source.read(name))


def folder_bundle(folder, target, prefix=""):
    folder = Path(folder)
    with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as out:
        for path in sorted(folder.rglob("*")):
            if path.is_file() and not is_master(path.name):
                out.write(path, prefix + path.relative_to(folder).as_posix())


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--companion-apk", type=Path, required=True, help="android/app build output")
    p.add_argument("--output", type=Path, default=ROOT / ".build/site")
    p.add_argument("--mirror", action="append", default=[], metavar="URL",
                   help="a second source for bundles/android.zip (must send a CORS header); repeatable")
    args = p.parse_args()
    out = args.output.resolve()
    shutil.rmtree(out, ignore_errors=True)
    (out / "bundles").mkdir(parents=True)
    for name in ("index.html", "app.js", "worker.js", "sw.js"):
        shutil.copy2(ROOT / "web" / name, out / name)
    shutil.copy2(ROOT / "web/signing/bunker-key.p12", out / "bunker-key.p12")
    for name in PYTHON:
        target = out / "py" / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / name, target)
    (out / "py/manifest.json").write_text(json.dumps(PYTHON))
    android_bundle(args.companion_apk, out / "bundles/android.zip")
    # The optional Mod Menu payload (prebuilt, per release), if present.
    payload = ROOT / "web/modmenu"
    if payload.is_dir():
        with zipfile.ZipFile(out / "bundles/modmenu.zip", "w", zipfile.ZIP_DEFLATED) as bundle:
            for path in sorted(payload.rglob("*")):
                if path.is_file():
                    # POSIX names inside the zip: Windows relative_to() inserts
                    # backslashes, and the builder looks the payload up as
                    # "en/libniermenu.so".
                    bundle.write(path, path.relative_to(payload).as_posix())
    # The version this site builds, shown in the page header.
    with zipfile.ZipFile(args.companion_apk) as companion:
        version = companion.read("assets/lunar/bunker-version.txt").decode().strip()
    # Names the picked APK on the page, from the same digests the build checks.
    sys.path.insert(0, str(ROOT / "android/tools"))
    import region  # noqa: E402  (after sys.path, which only this writer needs)
    known = {key: {"sha256": value["sha256"], "size": value["size"]} for key, value in region.REGIONS.items()}
    (out / "regions.json").write_text(json.dumps(known))
    # Where the page may fetch each bundle from, and what its bytes must hash to.
    # The release asset is a second source: GitHub's Pages and its download host
    # are reached differently, so one of them usually works when the other does not.
    def source(path, urls):
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        return {"sha256": digest, "urls": urls}

    mirrors = {
        "bundle": source(out / "bundles/android.zip", ["bundles/android.zip", *args.mirror]),
        "github": f"https://github.com/{REPO}/releases/download/v{version}/android.zip",
    }
    if (out / "bundles/modmenu.zip").exists():
        mirrors["modmenu"] = source(out / "bundles/modmenu.zip", ["bundles/modmenu.zip"])
    (out / "mirrors.json").write_text(json.dumps(mirrors))
    for path in out.rglob("*"):
        if path.is_file() and path.stat().st_size > PAGES_LIMIT:
            raise SystemExit(f"{path.name} is over GitHub Pages' 100 MB limit")
        if path.suffix == ".zip":
            with zipfile.ZipFile(path) as bundle:
                if any(is_master(n) for n in bundle.namelist()):
                    raise SystemExit(f"{path.name} contains master data")
    # A stamp over everything but the bundles: the page registers
    # sw.js?v=<version>-<stamp>, so a rebuild (even of a +dev site, where the
    # version does not change) installs a new cache instead of serving the old
    # one. Without it a changed py/webbuild.py would never reach the browser.
    stamp = hashlib.sha256()
    for path in sorted(out.rglob("*")):
        relative = path.relative_to(out).as_posix()
        if path.is_file() and not relative.startswith("bundles/") and relative != "version.json":
            stamp.update(relative.encode())
            stamp.update(path.read_bytes())
    (out / "version.json").write_text(json.dumps({"version": version, "build": stamp.hexdigest()[:12]}))
    total = sum(p.stat().st_size for p in out.rglob("*") if p.is_file())
    print(f"Site ready: {out} ({total / 1048576:.0f} MB). Test with: python3 -m http.server -d {out}")


if __name__ == "__main__":
    main()
