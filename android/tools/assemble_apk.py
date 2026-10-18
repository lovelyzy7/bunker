#!/usr/bin/env python3
"""Build the offline APK by editing the original APK's files directly.

  assemble_apk.py --apk ORIGINAL.apk --master 20240404193219.bin.e \\
      --companion-apk app-release.apk --output bunker.unsigned.apk

Unlike package_game.py, this needs no apktool, Android SDK or Java, so it can
also run in a browser. It patches the game library and metadata with the
pinned lunar-scripts code, edits the compiled manifest, appends the launcher
and server from the companion APK, and writes an unsigned, aligned APK.
Sign the result yourself, for example with apksigner or uber-apk-signer.

Both releases are supported. 日服 (JP) needs the smali patches only for
Facebook login and account transfer; this builder skips them, because it does
not run apktool. Offline play, Tools and save import do not use them — a fresh
install reaches the story on its own anonymous account.
"""
import argparse
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import re
import shutil
import struct
import sys
import tempfile
import zipfile
import zlib

sys.path.insert(0, str(Path(__file__).resolve().parent))
import axml  # noqa: E402
import build_info  # noqa: E402
import region  # noqa: E402
from axml import Attr, Element  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "upstream/lunar-scripts"
SCRIPTS_JP = ROOT / "upstream/lunar-scripts-jp"
GRPC, HTTP = "127.0.0.1:8003", "127.0.0.1:8080"


def addresses(port_offset=0):
    """The game's loopback addresses, moved by the build's port offset."""
    if not 0 <= port_offset <= 65535 - 8080:
        raise ValueError(f"Port offset must be 0–{65535 - 8080}")
    return f"127.0.0.1:{8003 + port_offset}", f"127.0.0.1:{8080 + port_offset}"
MASTER = "20240404193219.bin.e"
LIB, METADATA = "lib/arm64-v8a/libil2cpp.so", "assets/bin/Data/Managed/Metadata/global-metadata.dat"
# 日服 keeps its API host and port in a small Unity asset. The metadata strings
# only carry the host name, so the port has to be written here.
NETWORK_CONFIG = "assets/bin/Data/deace60a64f3d4398a2db0f3d1a41195"

# Android attribute resource IDs (stable across platform versions).
NAME, VALUE, THEME, AUTHORITIES = 0x01010003, 0x01010024, 0x01010000, 0x01010018
MIN_SDK, EXTRACT_NATIVE, CLEARTEXT, PAGE_SIZE_COMPAT = 0x0101020C, 0x010104EA, 0x010104EC, 0x010106AB
APP_CATEGORY, APP_CATEGORY_GAME = 0x01010545, 0
THEME_MATERIAL_LIGHT_NO_ACTION_BAR = 0x01030241
# Attributes the Mod Menu's service needs, as resource ids (aapt writes these;
# Android reads them by id, so a manifest without them would ignore the values).
ENABLED, EXPORTED, STOP_WITH_TASK = 0x0101000E, 0x01010010, 0x0101036A  # android.R$attr
# The prebuilt class that starts the menu and then the game (web/modmenu/shim.dex).
MENU_SHIM = "org.veritr1x.bunker.MenuShim"
MENU_SERVICE = "com.android.support.Launcher"
OVERLAY_PERMISSION = "android.permission.SYSTEM_ALERT_WINDOW"
PAGE_SIZE_COMPAT_ENABLED = 32


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run_cli(module, *args):
    old = sys.argv
    sys.argv = [module.__name__, *map(str, args)]
    try:
        module.main()
    except SystemExit as e:
        if e.code not in (None, 0):
            raise RuntimeError(f"{module.__name__} failed: {e.code}")
    finally:
        sys.argv = old


def extract(archive, name, target):
    """Copy one entry of an open APK to disk, in chunks: the 120 MB library is never one Python object."""
    target = Path(target)
    target.parent.mkdir(parents=True, exist_ok=True)
    with archive.open(name) as source, open(target, "wb") as sink:
        shutil.copyfileobj(source, sink, 1 << 20)
    return target


def patch_game_files(archive, work, port_offset=0):
    """Patch the library and metadata inside work, there; returns their paths.

    Paths rather than bytes keep the browser build's peak memory down: the game
    library is written straight from its work file into the new APK.
    """
    work = Path(work)
    lib, metadata = extract(archive, LIB, work / LIB), extract(archive, METADATA, work / METADATA)
    # The upstream patcher also edits a text manifest; that change is made
    # on the binary manifest below instead.
    (work / "AndroidManifest.xml").write_text("<application >")
    grpc, http = addresses(port_offset)
    run_cli(load("patch_apk", SCRIPTS / "android/patch_apk.py"), work, "--grpc-addr", grpc, "--http-addr", http)
    load("package_game", ROOT / "android/tools/package_game.py").patch_local_reachability(work)
    return lib, metadata


def patch_game_files_jp(archive, work, port_offset=0):
    """The 日服 (JP) library, metadata and network_config patches, without the smali."""
    jp = load("patch_apk_jp", SCRIPTS_JP / "android/patch_apk_jp.py")
    grpc, http = addresses(port_offset)
    host, port = grpc.rsplit(":", 1)
    web = f"http://{http}"
    # Same list as the command-line JP patcher, minus the Facebook/bridge
    # redirects: those live in smali and only serve social login and transfer.
    replacements = [
        ("api.app.nierreincarnation.jp", host),
        ("https://web.app.nierreincarnation.jp/assets/release/{0}/database.bin",
         f"{web}/assets/release/{{0}}/database.bin"),
        ("https://mama:na23R6uh7P@web.app.nierreincarnation.jp", web),
        ("https://resources-api.app.nierreincarnation.jp/", f"{web}/"),
        ("https://dev-web.dark.abot.sh", web),
    ]
    work = Path(work)
    lib, metadata = extract(archive, LIB, work / LIB), extract(archive, METADATA, work / METADATA)
    network_config = extract(archive, NETWORK_CONFIG, work / NETWORK_CONFIG)
    if True:
        patched = jp.patch_metadata_strings(str(work / METADATA), replacements)
        if patched != len(replacements):
            raise RuntimeError(f"Only {patched}/{len(replacements)} JP metadata strings were patched")
        jp.patch_network_config(str(work), host, int(port))
        jp.patch_libil2cpp(str(work / LIB))
        load("package_game", ROOT / "android/tools/package_game.py").patch_local_reachability(work)
        return lib, metadata, network_config


def patch_master(original):
    with tempfile.TemporaryDirectory() as work:
        source, target = Path(work) / "in.bin.e", Path(work) / "out.bin.e"
        source.write_bytes(original)
        run_cli(load("patch_masterdata", SCRIPTS / "patch_masterdata.py"), "--input", source, "--output", target)
        return target.read_bytes()


def patch_manifest(game_manifest, companion_manifest, port_offset=0, menu=False, release="en"):
    doc = axml.parse(game_manifest)
    companion = axml.parse(companion_manifest).root
    manifest = doc.root
    package = manifest.get("package", ns=None).raw
    app = manifest.find_all("application")[0]
    for sdk in manifest.find_all("uses-sdk"):
        sdk.set(Attr.integer("minSdkVersion", 28, MIN_SDK))
    # Permissions the launcher and server need, ahead of the game's own.
    have = {p.get("name").raw for p in manifest.find_all("uses-permission")}
    position = manifest.children.index(manifest.find_all("uses-sdk")[0]) + 1
    for permission in companion.find_all("uses-permission"):
        if permission.get("name").raw not in have:
            manifest.children.insert(position, permission); position += 1
    app.set(Attr.boolean("extractNativeLibs", True, EXTRACT_NATIVE))
    app.set(Attr.boolean("usesCleartextTraffic", True, CLEARTEXT))
    # The game already sets isGame; the category is what Android's Game Mode and Game Dashboard read.
    app.set(Attr.integer("appCategory", APP_CATEGORY_GAME, APP_CATEGORY))
    # The game's Unity libraries use 4 KB pages; ask Android for compatibility.
    app.set(Attr.integer("pageSizeCompat", PAGE_SIZE_COMPAT_ENABLED, PAGE_SIZE_COMPAT))
    # The 日服 patcher removes these too: Adjust and Firebase are disabled in the
    # library, and their startup receivers would only make dead network calls.
    if release == "jp":
        dead_components = ("com.adjust.sdk.AdjustReferrerReceiver",
                           "com.google.firebase.provider.FirebaseInitProvider",
                           "com.google.firebase.perf.provider.FirebasePerfProvider")
        for child in list(app.children):
            if child.name in ("receiver", "provider"):
                name = child.get("name", ns=None)
                if name and any(str(name.raw).endswith(dead) for dead in dead_components):
                    app.children.remove(child)
    # The launcher replaces the game's launcher entry and opens the game itself.
    game_activity = None
    for activity in app.find_all("activity") + app.find_all("activity-alias"):
        for intent in activity.find_all("intent-filter"):
            if any(c.get("name") and c.get("name").raw == "android.intent.category.LAUNCHER" for c in intent.find_all("category")):
                game_activity = activity.get("name").raw
                activity.children.remove(intent)
    if not game_activity:
        raise RuntimeError("Cannot find the game's launcher activity")
    launcher = next(a for a in app.find_all("activity") + app.find_all("activity-alias")
                    if a.get("name") and a.get("name").raw == game_activity)
    if game_activity.startswith("."):
        game_activity = package + game_activity
    if menu:
        # The menu runs inside the game's process, so the game's launcher entry
        # points at a prebuilt subclass that starts the menu and then the game.
        launcher.set(Attr.string("name", MENU_SHIM, NAME))
        game_activity = MENU_SHIM
    app.children.append(Element("meta-data", [Attr.string("name", "org.veritr1x.bunker.GAME_ACTIVITY", NAME),
                                              Attr.string("value", game_activity, VALUE)]))
    # The launcher and server read the ports the game was built for.
    app.children.append(Element("meta-data", [Attr.string("name", "org.veritr1x.bunker.PORT_OFFSET", NAME),
                                              Attr.integer("value", port_offset, VALUE)]))
    # Which release this build is, so an update never crosses regions.
    app.children.append(Element("meta-data", [Attr.string("name", "org.veritr1x.bunker.REGION", NAME),
                                              Attr.string("value", region.region_for_package(package) or "", VALUE)]))
    if menu:
        # The menu draws an overlay, and its service is the launcher it starts.
        if OVERLAY_PERMISSION not in have:
            element = Element("uses-permission", [Attr.string("name", OVERLAY_PERMISSION, NAME)])
            permissions = manifest.find_all("uses-permission")
            at = manifest.children.index(permissions[-1]) + 1 if permissions else 0
            manifest.children.insert(at, element)
        app.children.append(Element("service", [Attr.string("name", MENU_SERVICE, NAME),
                                                Attr.boolean("enabled", True, ENABLED),
                                                Attr.boolean("exported", False, EXPORTED),
                                                Attr.boolean("stopWithTask", True, STOP_WITH_TASK)]))
        app.children.append(Element("meta-data", [Attr.string("name", "org.veritr1x.bunker.MOD_MENU", NAME),
                                                  Attr.string("value", "true", VALUE)]))
    for source in companion.find_all("application")[0].children:
        if isinstance(source, Element) and source.name in ("activity", "service", "provider"):
            if source.name == "activity":
                source.set(Attr.reference("theme", THEME_MATERIAL_LIGHT_NO_ACTION_BAR, THEME))
            if source.name == "provider":  # Authorities are unique per device: use the game's.
                source.set(Attr.string("authorities", package + ".lunar_loopback", AUTHORITIES))
            app.children.append(source)
    return axml.serialize(doc), game_activity


class ApkWriter:
    """Writes an APK: unchanged entries are copied raw; stored data is 4-byte aligned."""

    def __init__(self, out):
        self.out, self.entries, self.names = out, [], set()

    def _write(self, name, method, crc, compressed, size, data, flags=0):
        if name in self.names:
            raise RuntimeError(f"Duplicate file in the APK: {name}")
        self.names.add(name)
        encoded = name.encode()
        offset = self.out.tell()
        extra = b""
        if method == 0:
            # Pad the extra field so stored data starts on a 4-byte boundary
            # (16 KB for native libraries), as zipalign does.
            align = 16384 if name.endswith(".so") else 4
            start = offset + 30 + len(encoded)
            extra = b"\0" * ((-start) % align)
        self.out.write(struct.pack("<IHHHHHIIIHH", 0x04034B50, 20, flags & ~0x8, method, 0, 0x21, crc,
                                   compressed, size, len(encoded), len(extra)) + encoded + extra)
        if isinstance(data, bytes):
            self.out.write(data)
        else:
            data(self.out)
        self.entries.append((name, method, crc, compressed, size, offset, flags & ~0x8))

    def add(self, name, data, compress=True):
        crc = zlib.crc32(data)
        if compress:
            deflater = zlib.compressobj(6, zlib.DEFLATED, -15)
            packed = deflater.compress(data) + deflater.flush()
            self._write(name, 8, crc, len(packed), len(data), packed)
        else:
            self._write(name, 0, crc, len(data), len(data), data)

    def add_file(self, name, path, compress=True):
        """Add a file from disk, in chunks: the 120 MB library never becomes one Python object.

        A ZIP header carries the length before the data, so a stored entry
        takes its size from the filesystem and a deflated one is packed as it
        is read. Only the patched metadata and master data are compressed.
        """
        path = Path(path)
        size = path.stat().st_size
        if compress:
            deflater, packed, crc = zlib.compressobj(6, zlib.DEFLATED, -15), io.BytesIO(), 0
            with open(path, "rb") as source:
                for chunk in iter(lambda: source.read(1 << 20), b""):
                    crc = zlib.crc32(chunk, crc)
                    packed.write(deflater.compress(chunk))
            packed.write(deflater.flush())
            data = packed.getvalue()
            self._write(name, 8, crc, len(data), size, data)
            return
        crc = 0
        with open(path, "rb") as source:
            for chunk in iter(lambda: source.read(1 << 20), b""):
                crc = zlib.crc32(chunk, crc)

        def stream(out):
            with open(path, "rb") as source:
                shutil.copyfileobj(source, out, 1 << 20)
        self._write(name, 0, crc, size, size, stream)

    def copy(self, source, info):
        """Copy an entry's compressed bytes from the source APK unchanged."""
        source.seek(info.header_offset)
        header = source.read(30)
        name_length, extra_length = struct.unpack_from("<HH", header, 26)
        start = info.header_offset + 30 + name_length + extra_length

        def stream(out):
            source.seek(start)
            left = info.compress_size
            while left:
                chunk = source.read(min(left, 1 << 20))
                out.write(chunk); left -= len(chunk)
        self._write(info.filename, info.compress_type, info.CRC, info.compress_size, info.file_size, stream, info.flag_bits)

    def close(self):
        directory = self.out.tell()
        for name, method, crc, compressed, size, offset, flags in self.entries:
            encoded = name.encode()
            self.out.write(struct.pack("<IHHHHHHIIIHHHHHII", 0x02014B50, 20, 20, flags, method, 0, 0x21, crc,
                                       compressed, size, len(encoded), 0, 0, 0, 0, 0, offset) + encoded)
        end = self.out.tell()
        count = len(self.entries)
        self.out.write(struct.pack("<IHHHHIIH", 0x06054B50, 0, 0, count, count, end - directory, directory, 0))


def assemble(apk, master, companion_apk, output, log=print, port_offset=0, menu=None):
    """Build the APK. menu=(dex files, libniermenu.so) adds the Mod Menu."""
    work = Path(tempfile.mkdtemp(prefix="bunker-"))
    try:
        return _assemble(Path(apk), Path(master), Path(companion_apk), Path(output), work, log, port_offset, menu)
    finally:
        shutil.rmtree(work, ignore_errors=True)


def _assemble(apk, master, companion_apk, output, work, log, port_offset, menu):
    with zipfile.ZipFile(apk) as game, zipfile.ZipFile(companion_apk) as companion, open(apk, "rb") as raw:
        names = set(game.namelist())
        for required in ("AndroidManifest.xml", LIB, METADATA, "resources.arsc"):
            if required not in names:
                raise RuntimeError(f"Not the ARM64 game APK: {required} is missing")
        package = axml.parse(game.read("AndroidManifest.xml")).root.get("package", ns=None).raw
        release = region.region_for_package(package)
        if release is None:
            raise RuntimeError(f"Not a game this build accepts: {package} ({', '.join(i['package'] for i in region.REGIONS.values())})")
        if release == "jp" and NETWORK_CONFIG not in names:
            raise RuntimeError(f"Not the 日服 (JP) game APK: {NETWORK_CONFIG} is missing")
        log("Patching the game library and metadata…")
        if release == "jp":
            lib, metadata, network_config = patch_game_files_jp(game, work, port_offset)
        else:
            lib, metadata = patch_game_files(game, work, port_offset)
        log("Updating the manifest…")
        manifest, game_activity = patch_manifest(game.read("AndroidManifest.xml"),
                                                 companion.read("AndroidManifest.xml"),
                                                 port_offset, menu=bool(menu), release=release)
        log("Patching master data…")
        original_master = Path(master).read_bytes()
        patched_master = patch_master(original_master)
        replaced = {"AndroidManifest.xml": manifest, LIB: lib, METADATA: metadata}
        if release == "jp":
            replaced[NETWORK_CONFIG] = network_config
        dex = [n for n in names if re.fullmatch(r"classes\d*\.dex", n)]
        next_dex = max(int(n[7:-4] or 1) for n in dex) + 1
        temporary = Path(str(output) + ".partial")
        with open(temporary, "wb") as out:
            writer = ApkWriter(out)
            log("Writing the APK…")
            entries = game.infolist()
            step = max(1, len(entries) // 10)   # ten lines, not one per hundred files
            for index, info in enumerate(entries, 1):
                name = info.filename
                # The browser shows these lines as progress: without them a phone
                # build looks frozen while one big entry is copied.
                if info.file_size >= 8 << 20:
                    log(f"  {name} ({info.file_size >> 20} MB)…")
                elif index % step == 0 and index < len(entries):
                    log(f"  {index * 100 // len(entries)}%…")
                # The publisher's signature no longer applies; you sign the result.
                if name.startswith("META-INF/") and re.search(r"\.(SF|RSA|DSA|EC)$|MANIFEST\.MF$", name) or name == "stamp-cert-sha256":
                    continue
                if name in replaced:
                    # pop(): the patched library is 120 MB that nothing below
                    # needs, and the browser build has no memory to spare.
                    value = replaced.pop(name)
                    if isinstance(value, bytes):   # the manifest, which is small
                        writer.add(name, value)
                    else:                          # the patched files, written from disk
                        writer.add_file(name, value, compress=name != LIB or info.compress_type != 0)
                else:
                    writer.copy(raw, info)
            for name in sorted(companion.namelist(), key=lambda n: (len(n), n)):
                if re.fullmatch(r"classes\d*\.dex", name):
                    writer.add("classes%d.dex" % next_dex, companion.read(name)); next_dex += 1
            ours = {"assets/lunar/" + MASTER, "assets/lunar/original-master.bin.e", "assets/lunar/LUNAR_TEAR_LICENSE.txt",
                    "assets/lunar/build.json", "assets/lunar/game-manifest.xml"}
            for name in sorted(companion.namelist()):
                if name.startswith(("lib/arm64-v8a/", "assets/chaquopy/", "assets/lunar/")) and name not in ours:
                    writer.add(name, companion.read(name))
            if menu:
                # The menu's classes and its native library, after the game's own.
                log("Writing the Mod Menu…")
                for index, blob in enumerate(menu["dex"], 1):
                    writer.add("classes%d.dex" % next_dex, blob); next_dex += 1
                    log(f"  dex {index}/{len(menu['dex'])} ({len(blob) >> 10} KB)…")
                writer.add("lib/arm64-v8a/libniermenu.so", menu["lib"])
                log(f"  libniermenu.so ({len(menu['lib']) >> 20} MB)…")
            writer.add("assets/lunar/" + MASTER, patched_master)
            writer.add("assets/lunar/original-master.bin.e", original_master)
            writer.add("assets/lunar/LUNAR_TEAR_LICENSE.txt", (ROOT / "LICENSE").read_bytes())
            # What an update in place needs (build_info.py).
            info = build_info.describe(companion, len(dex), port_offset, release, menu=bool(menu))
            writer.add("assets/lunar/build.json", json.dumps(info, indent=1).encode())
            writer.add("assets/lunar/game-manifest.xml", game.read("AndroidManifest.xml"))
            log("Finalizing the archive…")
            writer.close()
        os.replace(temporary, output)
    return {"activity": game_activity, "region": release, "name": region.REGIONS[release]["name"],
            "package": package, "version": info["version"], "modMenu": bool(menu),
            "portOffset": int(port_offset), "size": Path(output).stat().st_size}


def update(installed_apk, companion_apk, output, log=print):
    """Rebuilds an installed Bunker APK with a newer launcher; the game's entries are copied as they are.

    companion_apk is the launcher APK or the release's Android bundle. The
    installed APK's build.json says which entries are Bunker's; the master data
    and the game's original manifest stay. Returns the new build.json."""
    with zipfile.ZipFile(installed_apk) as game, zipfile.ZipFile(companion_apk) as companion, open(installed_apk, "rb") as raw:
        names = set(game.namelist())
        if "assets/lunar/build.json" not in names or "assets/lunar/game-manifest.xml" not in names:
            raise RuntimeError("This update needs the web builder: this build is older than Bunker 1.0.0")
        old = json.loads(game.read("assets/lunar/build.json"))
        # Never cross regions on an update: the installed manifest decides.
        release = region.region_for_package(axml.parse(game.read("assets/lunar/game-manifest.xml")).root.get("package", ns=None).raw)
        if release is None:
            raise RuntimeError("This update needs the web builder: the installed game is not a release Bunker knows")
        if old.get("gamePatch") != build_info.GAME_PATCH:
            raise RuntimeError("This update needs the web builder: it changes how the game itself is patched")
        log("Updating the manifest…")
        manifest, _ = patch_manifest(game.read("assets/lunar/game-manifest.xml"), companion.read("AndroidManifest.xml"),
                                     old["portOffset"], release=release)
        kept = {"assets/lunar/" + MASTER, "assets/lunar/original-master.bin.e", "assets/lunar/LUNAR_TEAR_LICENSE.txt",
                "assets/lunar/game-manifest.xml"}
        temporary = Path(str(output) + ".partial")
        try:
            with open(temporary, "wb") as out:
                writer = ApkWriter(out)
                log("Writing the APK…")
                for info in game.infolist():
                    name = info.filename
                    if name.startswith("META-INF/") and re.search(r"\.(SF|RSA|DSA|EC)$|MANIFEST\.MF$", name) or name == "stamp-cert-sha256":
                        continue
                    if name == "AndroidManifest.xml":
                        writer.add(name, manifest)
                    elif not build_info.is_bunker_entry(name, old) or name in kept:
                        writer.copy(raw, info)
                next_dex = old["gameDex"] + 1
                for name in sorted(companion.namelist(), key=lambda n: (len(n), n)):
                    if re.fullmatch(r"classes\d*\.dex", name):
                        writer.add("classes%d.dex" % next_dex, companion.read(name)); next_dex += 1
                for name in sorted(companion.namelist()):
                    if name.startswith(("lib/arm64-v8a/", "assets/chaquopy/", "assets/lunar/")) and name not in kept \
                            and name != "assets/lunar/build.json" and not name.endswith(".bin.e"):
                        writer.add(name, companion.read(name))
                info = build_info.describe(companion, old["gameDex"], old["portOffset"], release)
                writer.add("assets/lunar/build.json", json.dumps(info, indent=1).encode())
                writer.close()
            os.replace(temporary, output)
        finally:
            temporary.unlink(missing_ok=True)
    return info

def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--apk", type=Path, required=True, help="Original ARM64 game 3.7.1 APK")
    p.add_argument("--master", type=Path, required=True, help="Original 20240404193219.bin.e")
    p.add_argument("--companion-apk", type=Path, required=True, help="Built launcher APK (android/app)")
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--port-offset", type=int, default=0, help="Move the game's ports 8003/8080/3000 by this amount")
    args = p.parse_args()
    game_activity = assemble(args.apk.resolve(strict=True), args.master.resolve(strict=True), args.companion_apk.resolve(strict=True),
                             args.output.resolve(), port_offset=args.port_offset)
    print(f"Unsigned APK: {args.output}\nGame activity: {game_activity}\nSign it before installing.")


if __name__ == "__main__":
    main()
