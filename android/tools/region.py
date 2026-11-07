"""Which release of the game an APK is, and what each one needs.

The game shipped twice, as 日服 (JP) and 全球服 (EN / "west"). Both are 3.7.1
and both are served by the same Lunar Tear instance, but they are different
binaries: different package names, different IL2CPP library layout, and
different client patch scripts. Bunker therefore builds one region per APK and
records which one, so an update never crosses regions.

Android only: the project has no iOS build, so an IPA is refused.

Detection reads the compiled manifest with axml.py, so it runs before anything
is unpacked, needs no SDK, and works in the browser builder too.
"""
import zipfile
from pathlib import Path

import axml

EN_PACKAGE = "com.square_enix.android_googleplay.nierspww"
JP_PACKAGE = "com.square_enix.android_googleplay.nierspjp"

# The package names the game uses, in the order the build tries them.
# Call-face switch (BUNKER-ADAPT-PLAN §1.7.2 #1/#2): the patchers are the
# lunar-scripts-zh dual front-ends (jp-client / en-client). The original
# lunar-scripts(-jp) checkouts stay pinned for provenance with zero call sites.
# Key selection (§8.2) and product naming (§9.1) live here so every build entry
# point derives them from the same detection. zh_client.dispatch() cross-checks
# these facts against lunar-scripts-zh/shared/detect_client.py and refuses on
# any disagreement.
REGIONS = {
    "en": {
        "name": "全球服 (EN)",
        "package": EN_PACKAGE,
        # lib/arm64-v8a/libil2cpp.so 3.7.1 文件大小。display_patch.c detect_client
        # 与 lunar-scripts-zh/shared/detect_client.py 同一套 JP/EN 事实表：
        # 包名 / 清单 org.veritr1x.bunker.REGION meta / 本三元组 与 so 大小交叉
        # 核对选 RVA 表，不一致 fail-fast 拒补丁。
        "libil2cpp_size": 127359872,
        # The upstream patcher: lunar-scripts-zh en-client (was lunar-scripts).
        "patcher": "upstream/lunar-scripts-zh/en-client/patches/patch_apk_en.py",
        # The 3.7.1 release this build's offsets were read from. A different
        # build is refused unless the caller allows it: its metadata offsets
        # move, and the patched metadata would corrupt the game.
        "size": 263571029,
        "sha256": "9ded0797ee607b6892b531ba3a02f4c4510774f5fe098ccada78ccff881c9209",
        # Product naming contract (§9.1): auto-named from the detection.
        "product": "nier-en.apk",
        "client": "en-client",
        # Signing key auto-selection (§8.2), relative to lunar-scripts-zh/.
        "keystore": "en-client/keys/nier-en.keystore",
        "key_alias": "androiddebugkey",
        "key_pass": "android",
        "cert_sha256": "7d792c3cfefd73223764206edebd9526618638ff152165df5fbecd356aa4a173",
    },
    "jp": {
        "name": "日服 (JP)",
        "package": JP_PACKAGE,
        # lib/arm64-v8a/libil2cpp.so 3.7.1 文件大小（同上，双表同源）。
        "libil2cpp_size": 126216336,
        # The upstream patcher: lunar-scripts-zh jp-client (was lunar-scripts-jp).
        "patcher": "upstream/lunar-scripts-zh/jp-client/patches/patch_apk_jp.py",
        "size": 254131762,
        "sha256": "25b6326c610290dd1f581fc3b41e60efb1126172aae45804d5345caa0b653609",
        "product": "nier-jp.apk",
        "client": "jp-client",
        "keystore": "jp-client/keys/nier-jp.keystore",
        "key_alias": "nier",
        "key_pass": "lunar-jp",
        "cert_sha256": "eec23be0cb205c401791be3d4b82e8851560f5c2aed3ec644166093d3d98a2fe",
    },
}

# The master data both releases use, named after its release date. The build
# patches it, so it must be the untouched file.
MASTER = "20240404193219.bin.e"
MASTER_SIZE = 7801104
MASTER_SHA256 = "60555788242de9a0580b0d86f6d109d67bd9cabd16d7bcda9b9a99745f270778"

# Each release's master data, named after its release date. The Japanese APK
# takes the Japanese master data, 20240405123139.bin.e. The name says nothing
# (a browser names a second download "20240405123139.bin (1).e"): the contents
# decide (master_edition). The build embeds either one as MASTER, unchanged
# (assemble_apk; the L6 gate's filename invariant).
MASTERS = {
    "en": {"name": MASTER, "size": MASTER_SIZE, "sha256": MASTER_SHA256},
    "jp": {"name": "20240405123139.bin.e"},
}

# Far above the master data's 7.5 MB: a resource dump picked by mistake is
# refused without reading it. Below 1 MB it is not master data either.
MAX_MASTER_SIZE = 64 << 20
MIN_MASTER_SIZE = 1_000_000

# The master data's AES-CBC key and IV (the game's, the same for both
# releases; also patch_masterdata_zh's built-in BUILTIN_KEY/IV).
MASTER_KEY = bytes.fromhex("36436230313332314545356536624265")
MASTER_IV = bytes.fromhex("45666341656634434165356536446141")

# Mission conditions only the checked 20240405123139 Japanese master has
# (scripts/gen_mission_rules.py regional_rules: the shifted costume/weapon
# skills, the Flying Mama score and a Japanese-only stamina quest). The Global
# master's neighbouring counters are 197/199 and 200/202, never 198/201.
JP_ONLY_MISSIONS = {(10, 198, 0), (6, 201, 0), (29, 7, 0), (1, 101030801, 0)}

# m_mission's columns (lunar-scripts-zh/shared/schemas.json), read by position.
MISSION_TYPE, MISSION_OPTION, MISSION_DETAIL = 7, 10, 15

CHUNK = 1 << 20


def file_digest(path, digest=None):
    """A file's SHA-256, read in chunks: a 250 MB APK never sits in memory whole."""
    import hashlib
    digest = digest or hashlib.sha256()
    with open(path, "rb") as source:
        while chunk := source.read(CHUNK):
            digest.update(chunk)
    return digest


def sha256_of(path):
    return file_digest(path).hexdigest()


def master_edition(path):
    """Which release's master data a file holds ("en"/"jp"), from its contents;
    None when it is not master data at all.

    The contents decide, not the name: a browser names a second download
    "20240405123139.bin (1).e". A file larger than a master ever gets is
    refused unread (the resource dump picked by mistake). The Japanese
    master is recognized by the mission conditions only it has; a sound
    master without them is the Global one.
    """
    import lz4.block
    import msgpack
    from Crypto.Cipher import AES
    from Crypto.Util.Padding import unpad
    size = Path(path).stat().st_size
    if not MIN_MASTER_SIZE < size < MAX_MASTER_SIZE:
        return None
    if size == MASTERS["en"]["size"] and sha256_of(path) == MASTERS["en"]["sha256"]:
        return "en"
    raw = Path(path).read_bytes()
    try:
        decoded = unpad(AES.new(MASTER_KEY, AES.MODE_CBC, MASTER_IV).decrypt(raw), AES.block_size)
        toc, blob = None, None
        try:
            msgpack.unpackb(decoded, raw=False, strict_map_key=False)
        except msgpack.ExtraData as exc:
            toc, blob = exc.unpacked, exc.extra
        if not isinstance(toc, dict) or not blob:
            return None
        for name in ("m_costume", "m_weapon", "m_event_quest_chapter", "m_shop", "m_mom_banner", "m_mission"):
            if name not in toc:
                return None
        for offset, length in toc.values():
            if offset < 0 or length <= 0 or offset + length > len(blob):
                return None
        offset, length = toc["m_mission"]
        obj = msgpack.unpackb(bytes(blob[offset:offset + length]), raw=False, strict_map_key=False)
        if isinstance(obj, msgpack.ExtType) and obj.code == 99:
            # LZ4 ext header (dump_masterdata.read_lz4_ext_header): int32/uint32
            # big-endian size, or a literal small tag.
            tag = obj.data[0]
            if tag == 0xd2:
                ulen, packed = int.from_bytes(obj.data[1:5], "big", signed=True), obj.data[5:]
            elif tag == 0xce:
                ulen, packed = int.from_bytes(obj.data[1:5], "big"), obj.data[5:]
            elif tag <= 0x7f:
                ulen, packed = tag, obj.data[1:]
            else:
                return None
            rows = msgpack.unpackb(lz4.block.decompress(packed, uncompressed_size=ulen), raw=False, strict_map_key=False)
        else:
            rows = obj if isinstance(obj, list) else [obj]
        for row in rows:
            if isinstance(row, list) and len(row) > MISSION_DETAIL and \
                    (row[MISSION_TYPE], row[MISSION_OPTION], row[MISSION_DETAIL]) in JP_ONLY_MISSIONS:
                return "jp"
        return "en"
    except Exception:
        return None


def region_for_package(package):
    """The region a package name belongs to, or None."""
    for key, info in REGIONS.items():
        if info["package"] == package:
            return key
    return None


def package_of_apk(path):
    """The package name in an APK's compiled manifest."""
    with zipfile.ZipFile(path) as apk:
        root = axml.parse(apk.read("AndroidManifest.xml")).root
    found = root.get("package", ns=None)
    if found is None or not found.raw:
        raise SystemExit(f"{path} has no package name; it is not an Android app.")
    return found.raw


def region_of_apk(path):
    """(region, package) for an APK, refusing anything that is not the game."""
    package = package_of_apk(path)
    region = region_for_package(package)
    if region is None:
        known = ", ".join(info["package"] for info in REGIONS.values())
        raise SystemExit(f"{path} is {package!r}, which is not the game this build accepts ({known}).")
    return region, package


def resolve(requested, detected):
    """The region to build, given --region and what the file turned out to be."""
    if requested in (None, "", "auto"):
        return detected
    if requested != detected:
        raise SystemExit(f"--region {requested} contradicts the game files, which are {detected}.")
    return detected
