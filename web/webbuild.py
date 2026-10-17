"""Browser build driver: the same Android build as scripts/build.py, in Pyodide.

The page mirrors the repository under /repo, mounts the player's own files
read-only under /input and the prebuilt bundles under /bundles. Nothing is
uploaded anywhere; everything runs in the browser.
"""
from pathlib import Path
import shutil
import sys
import zipfile

REPO = Path("/repo")
sys.path.insert(0, str(REPO / "android/tools"))

import apk_sign  # noqa: E402
import assemble_apk  # noqa: E402
import region  # noqa: E402

MASTER = "20240404193219.bin.e"


def addresses(port_offset=0):
    """The game's loopback addresses (game, assets, accounts), moved by the port offset."""
    port_offset = int(port_offset)
    if not 0 <= port_offset <= 65535 - 8080:
        raise ValueError(f"Port offset must be 0–{65535 - 8080}")
    return tuple(f"127.0.0.1:{port + port_offset}" for port in (8003, 8080, 3000))


def menu_payload(resources, release):
    """The Mod Menu's dex files and library for a release, or None.

    resources is the payload the site ships as bundles/modmenu.zip; a folder
    works too, which is how the payload is edited before it is zipped.
    """
    if not resources:
        return None
    import zipfile
    bundle = Path(resources)
    if bundle.is_dir():
        read = lambda name: (bundle / name).read_bytes()
        names = {str(p.relative_to(bundle)) for p in bundle.rglob("*") if p.is_file()}
    elif bundle.is_file():
        with zipfile.ZipFile(bundle) as payload:
            names = set(payload.namelist())
            read = payload.read
    else:
        return None
    if "shim.dex" not in names or f"{release}/libniermenu.so" not in names:
        return None
    menu_dex = sorted(n for n in names if n.startswith(release + "/menu") and n.endswith(".dex"))
    if not menu_dex:
        return None
    return {"dex": [read("shim.dex")] + [read(n) for n in menu_dex],
            "lib": read(f"{release}/libniermenu.so")}


def build_android(apk, master, companion, output, log=print, port_offset=0, modmenu=None):
    addresses(port_offset)  # Validate before the slow steps.
    release, package = region.region_of_apk(Path(apk))
    log(f"{region.REGIONS[release]['name']}: {package}")
    if release != "en":
        raise ValueError(
            "日服 (JP) needs the desktop build: its client patch rewrites smali, which this builder cannot do. "
            "Run scripts/build.py with the JP APK on macOS, Linux or Windows (WSL)."
        )
    menu = menu_payload(modmenu, release)
    if modmenu and menu is None:
        log("The Mod Menu payload is missing; building without it.")
    elif menu:
        log(f"Adding the Mod Menu ({release})…")
    assemble_apk.assemble(Path(apk), Path(master), Path(companion), Path(output),
                          log=log, port_offset=int(port_offset), menu=menu)
    log("Signing with the public Bunker key…")
    apk_sign.sign(Path(output))
    log("Signed APK ready to install.")


