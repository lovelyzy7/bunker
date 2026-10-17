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
    },
    "jp": {
        "name": "日服 (JP)",
        "package": JP_PACKAGE,
        "patcher": "upstream/lunar-scripts-jp/android/patch_apk_jp.py",
    },
}

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
