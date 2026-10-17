#!/usr/bin/env python3
"""Rebuild web/modmenu/: the Mod Menu payload the in-browser builder injects.

  make_menu_payload.py --modmenu ~/src/bunker-modmenu

Two things come out of it, per release (jp, en):

  * `menu<N>.dex` and `libniermenu.so` — taken from that checkout's built menu
    APK (`<client>/modmenu/app/build/outputs/apk/debug/app-debug.apk`).
  * `shim.dex` — `tools/menu/MenuShim.java`, compiled and dexed here. It is the
    subclass that starts the menu and then the game, so the builder only has to
    point the game's launcher activity at it instead of patching the game's
    smali (which needs a dex compiler the browser does not have).

The output is committed: the site build in CI has no Android SDK.
"""
import argparse
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "android/tools"))
import command  # noqa: E402
PAYLOAD = ROOT / "web/modmenu"
CLIENTS = {"jp": "jp-client", "en": "en-client"}
SHIM_SOURCES = [ROOT / "tools/menu/MenuShim.java"]
STUBS = [ROOT / "tools/menu/stubs/com/google/firebase/MessagingUnityPlayerActivity.java",
         ROOT / "tools/menu/stubs/com/android/support/Main.java"]


def sdk_tool(sdk, name):
    """javac/jar/d8 and android.jar for the SDK in use."""
    java_home = Path(os.environ.get("JAVA_HOME", ""))
    build_tools = sorted((sdk / "build-tools").glob("3*")) if (sdk / "build-tools").is_dir() else []
    d8 = next((bt / "d8" for bt in reversed(build_tools) if (bt / "d8").exists() or (bt / "d8.bat").exists()), None)
    platforms = sorted((sdk / "platforms").glob("android-*"))
    platform = next((p for p in reversed(platforms) if (p / "android.jar").is_file()), None)
    if not (java_home / "bin").is_dir() or d8 is None or platform is None:
        raise SystemExit("Set JAVA_HOME to a JDK and ANDROID_HOME to an SDK with build-tools and a platform.")
    return java_home / "bin/javac", java_home / "bin/jar", d8, platform / "android.jar"


def run(*args, **kwargs):
    # d8 ships as a batch file on Windows, so it goes through command.command().
    subprocess.run(command.command(*args), check=True, **kwargs)


def build_shim(work, sdk):
    """Compile MenuShim against the game's activity and the menu entry point, then dex it."""
    javac, jar, d8, android_jar = sdk_tool(sdk, "shim")
    classes, stubs = work / "classes", work / "stubs"
    classes.mkdir(parents=True, exist_ok=True)
    run(javac, "-encoding", "UTF-8", "-source", "11", "-target", "11", "-nowarn",
        "-cp", android_jar, "-d", classes, *STUBS)
    run(jar, "cf", stubs.with_suffix(".jar"), "-C", classes, ".")
    run(javac, "-encoding", "UTF-8", "-source", "11", "-target", "11", "-nowarn",
        "-cp", f"{android_jar}{os.pathsep}{stubs.with_suffix('.jar')}", "-d", classes, *SHIM_SOURCES)
    out = work / "dex"
    out.mkdir()
    run(d8, "--lib", android_jar, "--classpath", stubs.with_suffix(".jar"), "--min-api", "28",
        "--output", out, classes / "org/veritr1x/bunker/MenuShim.class")
    return out / "classes.dex"


def copy_menu(modmenu, release, work):
    """The menu's dex files and its native library, from its built APK."""
    apk = modmenu / CLIENTS[release] / "modmenu/app/build/outputs/apk/debug/app-debug.apk"
    if not apk.is_file():
        raise SystemExit(f"{apk} is missing; build that client's menu first (tools/build_all.py or build.bat).")
    target = work / release
    target.mkdir(parents=True)
    written = []
    with zipfile.ZipFile(apk) as bundle:
        for index, name in enumerate(sorted(n for n in bundle.namelist() if re.fullmatch(r"classes\d*\.dex", n)), 1):
            path = target / f"menu{index}.dex"
            path.write_bytes(bundle.read(name))
            written.append(path)
        (target / "libniermenu.so").write_bytes(bundle.read("lib/arm64-v8a/libniermenu.so"))
    return written


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--modmenu", type=Path, required=True, help="bunker-modmenu checkout with built menus")
    parser.add_argument("--sdk", type=Path, default=Path(os.environ.get("ANDROID_HOME", Path.home() / "Android/Sdk")))
    parser.add_argument("--output", type=Path, default=PAYLOAD)
    args = parser.parse_args()
    modmenu, sdk, output = args.modmenu.resolve(), args.sdk.resolve(), args.output.resolve()

    with tempfile.TemporaryDirectory() as temp:
        work = Path(temp)
        shim = build_shim(work, sdk)
        staged = work / "payload"
        staged.mkdir()
        shutil.copy2(shim, staged / "shim.dex")
        for release in CLIENTS:
            copy_menu(modmenu, release, staged)
        if output.exists():
            shutil.rmtree(output)
        shutil.copytree(staged, output)
    total = sum(p.stat().st_size for p in output.rglob("*") if p.is_file())
    print(f"Payload ready: {output} ({total / 1048576:.1f} MB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
