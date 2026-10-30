#!/usr/bin/env python3
"""Makes a release's files: Bunker's own bundles, update.json and the notes.

  release_assets.py --version 1.0.0 --companion-apk APK --out DIR

The bundle is the one the web builder uses (web/build_site.py): the Android
launcher. It never holds game files or master data. update.json lists its size
and SHA-256 for the launcher's self-update, and the game patch version
(build_info.py).
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "web"))
sys.path.insert(0, str(ROOT / "android/tools"))
import build_info  # noqa: E402
import build_site  # noqa: E402


def _sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def make(version, companion_apk, out_dir):
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(companion_apk) as companion:
        built = companion.read(build_info.VERSION_ENTRY).decode().strip()
    if built != version:
        raise ValueError(f"The launcher is version {built}, not {version}")
    files = {"android": f"bunker-android-{version}.zip"}
    build_site.android_bundle(companion_apk, out / files["android"])
    assets = {}
    for key, name in files.items():
        path = out / name
        with zipfile.ZipFile(path) as bundle:
            if any(build_site.is_master(n) for n in bundle.namelist()):
                raise ValueError(f"{name} contains master data")
        assets[key] = {"name": name, "size": path.stat().st_size, "sha256": _sha256(path)}
    update = {"version": version, "gamePatch": build_info.GAME_PATCH, "assets": assets}
    (out / "update.json").write_text(json.dumps(update, indent=1) + "\n", encoding="utf-8")
    return update


def changelog_section(text, version):
    """The CHANGELOG text under "## <version> (date)", up to the previous release."""
    m = re.search(rf"^## {re.escape(version)} \(.*?\)\n(.*?)(?=^## \d+\.\d+\.\d+ \(|\Z)", text, re.S | re.M)
    if not m:
        raise ValueError(f"CHANGELOG.md has no section for {version}")
    return unwrap(m.group(1).strip())


def downloads(version):
    """The end of the release notes: what each file is for."""
    return (f"### Downloads\n"
            f"- `Bunker-{version}.exe` plays the Android build on Windows, in Google's Android Emulator. "
            f"Put it in one folder with your `bunker.apk` and `resource_dump_android.7z`. "
            f"See [Windows](https://github.com/veritr1x/bunker/blob/main/docs/WINDOWS.md).\n"
            f"- The `bunker-*.zip` files and `update.json` are for the Bunker's own updates. "
            f"You don't need to download them.")


def unwrap(text):
    """Joins the file's wrapped lines: GitHub release notes keep every line break."""
    out, fenced = [], False
    for line in text.split("\n"):
        if line.startswith("```"):
            fenced = not fenced
            out.append(line)
            continue
        continued = out and out[-1] and not fenced and line.strip() and not out[-1].startswith(("#", "```")) \
            and not re.match(r"\s*([-*+]|\d+\.)\s|#", line)
        if continued:
            out[-1] += " " + line.strip()
        else:
            out.append(line)
    return "\n".join(out)


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--version", required=True)
    p.add_argument("--companion-apk", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    args = p.parse_args()
    make(args.version, args.companion_apk, args.out)
    notes = args.out / "notes.md"
    notes.write_text(changelog_section((ROOT / "CHANGELOG.md").read_text(encoding="utf-8"), args.version) + "\n\n" + downloads(args.version) + "\n",
                     encoding="utf-8")
    print(notes)


if __name__ == "__main__":
    main()
