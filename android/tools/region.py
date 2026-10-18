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

import axml

EN_PACKAGE = "com.square_enix.android_googleplay.nierspww"
JP_PACKAGE = "com.square_enix.android_googleplay.nierspjp"

# The package names the game uses, in the order the build tries them.
REGIONS = {
    "en": {
        "name": "全球服 (EN)",
        "package": EN_PACKAGE,
        # The upstream patcher, present in every lunar-scripts checkout.
        "patcher": "upstream/lunar-scripts/android/patch_apk.py",
        # The 3.7.1 release this build's offsets were read from. A different
        # build is refused unless the caller allows it: its metadata offsets
        # move, and the patched metadata would corrupt the game.
        "size": 263571029,
        "sha256": "9ded0797ee607b6892b531ba3a02f4c4510774f5fe098ccada78ccff881c9209",
    },
    "jp": {
        "name": "日服 (JP)",
        "package": JP_PACKAGE,
        "patcher": "upstream/lunar-scripts-jp/android/patch_apk_jp.py",
        "size": 254131762,
        "sha256": "25b6326c610290dd1f581fc3b41e60efb1126172aae45804d5345caa0b653609",
    },
}

# The master data both releases use, named after its release date. The build
# patches it, so it must be the untouched file.
MASTER = "20240404193219.bin.e"
MASTER_SIZE = 7801104
MASTER_SHA256 = "60555788242de9a0580b0d86f6d109d67bd9cabd16d7bcda9b9a99745f270778"

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
