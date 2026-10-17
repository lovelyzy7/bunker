"""Optional: inject the Bunker Mod Menu into a finished game APK.

The menu lives in its own repository (bunker-modmenu), one workspace per game
release. This module finds it, runs its injector, and re-signs the result with
the build's own key: the launcher only updates itself from APKs signed with the
key it was built with.

Nothing here is required for a normal build; scripts/build.py calls it only
with --mod-menu.
"""
import os
import shutil
import subprocess
import tempfile
import zipfile
from pathlib import Path

import command

HERE = Path(__file__).resolve().parent
DEFAULT_ROOT = HERE.parents[1] / "vendor/bunker-modmenu"
# Which workspace builds the menu for each release.
WORKSPACE = {"en": "en-client", "jp": "jp-client"}


def root(explicit=None):
    """The bunker-modmenu checkout: --mod-menu-root, then $BUNKER_MODMENU, then vendor/."""
    for candidate in (explicit, os.environ.get("BUNKER_MODMENU"), DEFAULT_ROOT):
        if candidate and (Path(candidate) / "README.md").is_file():
            return Path(candidate).resolve()
    raise SystemExit(
        "The Mod Menu sources are missing. Clone them next to this repository as vendor/bunker-modmenu "
        "(git clone https://github.com/lovelyzy7/bunker-modmenu vendor/bunker-modmenu), set "
        "BUNKER_MODMENU to a checkout, or pass --mod-menu-root."
    )


def injector(release, menu_root=None):
    """The client workspace's build_all.py for a release."""
    if release not in WORKSPACE:
        raise SystemExit(f"No Mod Menu workspace for {release!r}")
    script = root(menu_root) / WORKSPACE[release] / "tools" / "build_all.py"
    if not script.is_file():
        raise SystemExit(f"{script} is missing; the Mod Menu checkout looks incomplete.")
    return script


def inject(release, apk, output, python, keystore, menu_root=None, log=print):
    """Build the release's menu into apk and sign the result with keystore."""
    script = injector(release, menu_root)
    apk, output = Path(apk).resolve(), Path(output).resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    # The menu's own tooling works from its repository, so every path is absolute.
    work = output.parent / (output.stem + ".modmenu")
    work.mkdir(parents=True, exist_ok=True)
    staged = work / "menu.apk"
    log(f"Injecting the {release} Mod Menu…")
    subprocess.run([str(python), str(script),
                    "--target", "patched", "--apk", str(apk), "--out", str(staged),
                    "--work", str(work / "apktool"), "--no-input", "--yes"],
                   cwd=script.parent.parent, check=True)
    log("Re-signing with the build's own key…")
    resign(staged, output, Path(keystore).resolve())
    shutil.rmtree(work, ignore_errors=True)
    return Path(output)


def resign(apk, output, keystore, sdk=None):
    """Align and sign apk with keystore, replacing the menu's signature."""
    sdk = Path(sdk or os.environ.get("ANDROID_HOME", Path.home() / "Android/Sdk"))
    tools = _build_tools(sdk)
    aligned = Path(tempfile.mkdtemp()) / "aligned.apk"
    try:
        _strip_signatures(apk, aligned)
        signed = Path(str(output) + ".signed")
        subprocess.run(command.command(tools / "apksigner", "sign", "--ks", keystore,
                                       "--ks-key-alias", "lunar-local",
                                       "--ks-pass", "pass:android", "--key-pass", "pass:android",
                                       "--out", signed, aligned), check=True)
        subprocess.run(command.command(tools / "apksigner", "verify", signed), check=True)
        os.replace(signed, output)
    finally:
        shutil.rmtree(aligned.parent, ignore_errors=True)


def _strip_signatures(apk, output):
    """Copy apk without its old signatures, so apksigner writes a clean one."""
    with zipfile.ZipFile(apk) as source, zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as target:
        for item in source.infolist():
            name = item.filename
            if name.startswith("META-INF/") and name.upper().endswith((".SF", ".RSA", ".DSA", ".EC", "MANIFEST.MF")):
                continue
            target.writestr(item, source.read(name))


def _build_tools(sdk):
    """The SDK build-tools folder with apksigner, newest first (it ships as .bat on Windows)."""
    root_dir = Path(sdk) / "build-tools"
    candidates = [p for p in root_dir.glob("3*")
                  if Path(command.resolve(p / "apksigner")).exists()] if root_dir.is_dir() else []
    if not candidates:
        raise SystemExit(f"No Android build-tools with apksigner under {root_dir}")
    return sorted(candidates, key=lambda p: [int(x) if x.isdigit() else 0 for x in p.name.split(".")])[-1]
