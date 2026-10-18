"""Browser build driver: the same Android build as scripts/build.py, in Pyodide.

The page mirrors the repository under /repo, mounts the player's own files
read-only under /input and the prebuilt bundles under /bundles. Nothing is
uploaded anywhere; everything runs in the browser.
"""
from pathlib import Path
import shutil
import sys
import zipfile

# The browser mounts the repository at /repo; on a command line this file's own
# parent says where it is, which is what CI and local test runs need.
REPO = Path("/repo") if Path("/repo/android/tools").is_dir() else Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "android/tools"))

import apk_sign  # noqa: E402
import assemble_apk  # noqa: E402
import region  # noqa: E402

MASTER = region.MASTER


def verify(apk, master, release):
    """Refuse files that are not the release this build's offsets were read from.

    Only the SHA-256 is compared: the size follows from it, and a split APK
    from an app bundle has the same library and metadata but a different
    overall size, which is why the page offers an override.
    """
    expected = region.REGIONS[release]
    if region.sha256_of(apk) != expected["sha256"]:
        raise ValueError(f"The game APK is not the original 3.7.1 {expected['name']} release (SHA-256 does not match)")
    if region.sha256_of(master) != region.MASTER_SHA256:
        raise ValueError(f"The master data is not the original {MASTER} (SHA-256 does not match)")


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
        # as_posix(): on Windows relative_to() yields "en\\libniermenu.so", which
        # never matched the "en/…" keys below — the menu was silently dropped
        # from every Windows build.
        names = {p.relative_to(bundle).as_posix() for p in bundle.rglob("*") if p.is_file()}
        close = lambda: None
    elif bundle.is_file():
        payload = zipfile.ZipFile(bundle)
        names = set(payload.namelist())
        # Not `read = payload.read` for later use: that bound method outlives the
        # with block, and calling it after close() raises "Attempt to use ZIP
        # archive that was already closed". The site ships this as a zip, so the
        # Mod Menu never built in the browser.
        read = payload.read
        close = payload.close
    else:
        return None
    try:
        if "shim.dex" not in names or f"{release}/libniermenu.so" not in names:
            return None
        menu_dex = sorted(n for n in names if n.startswith(release + "/menu") and n.endswith(".dex"))
        if not menu_dex:
            return None
        return {"dex": [read("shim.dex")] + [read(n) for n in menu_dex],
                "lib": read(f"{release}/libniermenu.so")}
    finally:
        close()


def build_android(apk, master, companion, output, log=print, port_offset=0, modmenu=None, verify_inputs=True):
    addresses(port_offset)  # Validate before the slow steps.
    release, package = region.region_of_apk(Path(apk))
    log(f"{region.REGIONS[release]['name']}: {package}")
    if verify_inputs:
        log("Checking the game APK and master data…")
        verify(apk, master, release)
    menu = menu_payload(modmenu, release)
    if modmenu and menu is None:
        log("The Mod Menu payload is missing; building without it.")
    elif menu:
        log(f"Adding the Mod Menu ({release})…")
    built = assemble_apk.assemble(Path(apk), Path(master), Path(companion), Path(output),
                                  log=log, port_offset=int(port_offset), menu=menu)
    log("Signing with the public Bunker key…")
    # The digest comes out of the signing pass, so the finished APK is not read
    # a second time just to hash it.
    certificate, sha256 = apk_sign.sign_and_digest(Path(output))
    log("Signed APK ready to install.")
    built = built if isinstance(built, dict) else {}
    built["sha256"] = sha256
    built["certificate"] = certificate
    return built




def _utf8_console():
    """Print 日服, ✓ and … on Windows too: a cp936 console raises or mangles them."""
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass


def main():
    """Command-line entry point: the same build the page runs in the browser."""
    import argparse
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--apk", type=Path, required=True, help="Original ARM64 game 3.7.1 APK (日服 or 全球服)")
    parser.add_argument("--master", type=Path, required=True, help="Original 20240404193219.bin.e")
    parser.add_argument("--companion-apk", type=Path, required=True, help="Built launcher APK (android/app)")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--port-offset", type=int, default=0)
    parser.add_argument("--mod-menu", nargs="?", const=str(REPO / "web/modmenu"), default=None,
                        help="Add the Mod Menu; optionally name the payload folder or zip")
    parser.add_argument("--skip-checks", action="store_true", help="Build even if the input SHA-256 differs")
    args = parser.parse_args()
    _utf8_console()
    build_android(args.apk, args.master, args.companion_apk, args.output, port_offset=args.port_offset,
                  modmenu=args.mod_menu, verify_inputs=not args.skip_checks)


if __name__ == "__main__":
    main()
