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
import urllib.request
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
# A fixed timestamp inside the zips: the same inputs must give the same bytes,
# or the launcher the release carries would never match the site's digest.
STAMP = (1980, 1, 1, 0, 0, 0)
# Pyodide is vendored into the site: the page cannot work without it, so it must
# not depend on a CDN that may be slow or blocked where the page itself loads.
PYODIDE_VERSION = "v0.28.3"
PYODIDE_URL = f"https://cdn.jsdelivr.net/pyodide/{PYODIDE_VERSION}/full/"
PYODIDE_PACKAGES = ("pycryptodome", "msgpack", "lz4")
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


def _download(url, cache):
    name = url.rsplit("/", 1)[-1]
    cached = cache / name
    if cached.exists() and cached.stat().st_size:
        return cached.read_bytes()
    with urllib.request.urlopen(url, timeout=120) as response:
        data = response.read()
    cache.mkdir(parents=True, exist_ok=True)
    cached.write_bytes(data)
    return data


def vendor_pyodide(out, cache):
    """Copy the Python runtime next to the page, so the builder has no CDN to reach."""
    lock = _download(PYODIDE_URL + "pyodide-lock.json", cache)
    packages = json.loads(lock).get("packages", {})
    names = ["pyodide.js", "pyodide.asm.wasm", "python_stdlib.zip"]
    names += [packages[name]["file_name"] for name in PYODIDE_PACKAGES if name in packages]
    target = out / "pyodide"
    target.mkdir(parents=True, exist_ok=True)
    (target / "pyodide-lock.json").write_bytes(lock)
    for name in names:
        (target / name).write_bytes(_download(PYODIDE_URL + name, cache))
    return sum((target / name).stat().st_size for name in names) + len(lock)


def _entry(name, compress=zipfile.ZIP_DEFLATED):
    info = zipfile.ZipInfo(name, STAMP)
    info.compress_type = compress
    info.external_attr = 0o644 << 16
    return info


def android_bundle(companion_apk, target):
    with zipfile.ZipFile(companion_apk) as source, zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as out:
        for name in source.namelist():
            wanted = name == "AndroidManifest.xml" or re.fullmatch(r"classes\d*\.dex", name) \
                or name.startswith(("lib/arm64-v8a/", "assets/chaquopy/", "assets/lunar/"))
            if wanted and not is_master(name):
                out.writestr(_entry(name), source.read(name))


def folder_bundle(folder, target, prefix=""):
    folder = Path(folder)
    with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as out:
        for path in sorted(folder.rglob("*")):
            if path.is_file() and not is_master(path.name):
                out.write(path, prefix + path.relative_to(folder).as_posix())


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--companion-apk", type=Path, help="android/app build output")
    p.add_argument("--launcher-zip", type=Path,
                   help="the released android.zip: the site then serves exactly those bytes, "
                        "so a download proxy can be checked against the same digest")
    p.add_argument("--output", type=Path, default=ROOT / ".build/site")
    p.add_argument("--no-pyodide", action="store_true",
                   help="leave the vendored Python runtime out (the page then uses jsDelivr)")
    p.add_argument("--pyodide-cache", type=Path, default=ROOT / ".build/pyodide-cache")
    p.add_argument("--mirror", action="append", default=[], metavar="URL",
                   help="a second source for bundles/android.zip (must send a CORS header); repeatable")
    args = p.parse_args()
    if bool(args.companion_apk) == bool(args.launcher_zip):
        raise SystemExit("Give exactly one of --companion-apk and --launcher-zip")
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
    (out / "py/manifest.json").write_text(json.dumps(PYTHON), encoding="utf-8")
    if args.launcher_zip:
        shutil.copy2(args.launcher_zip, out / "bundles/android.zip")
    else:
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
                    bundle.writestr(_entry(path.relative_to(payload).as_posix()), path.read_bytes())
    if not args.no_pyodide:
        vendor_pyodide(out, args.pyodide_cache / PYODIDE_VERSION)
    # The version this site builds, shown in the page header.
    with zipfile.ZipFile(args.launcher_zip or args.companion_apk) as companion:
        version = companion.read("assets/lunar/bunker-version.txt").decode().strip()
    # Names the picked APK on the page, from the same digests the build checks.
    sys.path.insert(0, str(ROOT / "android/tools"))
    import region  # noqa: E402  (after sys.path, which only this writer needs)
    known = {key: {"sha256": value["sha256"], "size": value["size"]} for key, value in region.REGIONS.items()}
    (out / "regions.json").write_text(json.dumps(known), encoding="utf-8")
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
        mirrors["modmenuGithub"] = f"https://github.com/{REPO}/releases/download/v{version}/modmenu.zip"
    (out / "mirrors.json").write_text(json.dumps(mirrors), encoding="utf-8")
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
    build = stamp.hexdigest()[:12]
    # The scripts carry the build stamp in their url, so a page never runs the
    # previous release's app.js next to this release's index.html: the service
    # worker keys its cache by url, and a new stamp is a new url.
    index = out / "index.html"
    # Path.write_text defaults to the locale encoding; on Windows that is cp936,
    # which cannot even hold the ▶ in the build button.
    index.write_text(index.read_text(encoding="utf-8").replace('src="app.js"', f'src="app.js?b={build}"'),
                     encoding="utf-8")
    script = out / "app.js"
    script.write_text(script.read_text(encoding="utf-8").replace('"worker.js"', f'"worker.js?b={build}"'),
                      encoding="utf-8")
    (out / "version.json").write_text(json.dumps({"version": version, "build": build}), encoding="utf-8")
    total = sum(p.stat().st_size for p in out.rglob("*") if p.is_file())
    print(f"Site ready: {out} ({total / 1048576:.0f} MB). Test with: python3 -m http.server -d {out}")


if __name__ == "__main__":
    main()
