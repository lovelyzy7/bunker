#!/usr/bin/env python3
"""Compare the two Mod Menu repositories, so the device menu and the original stay in step.

  check_menu_parity.py [--bunker DIR] [--original DIR] [--update] [--json]

Bunker's menu lives in `lovelyzy7/bunker-modmenu`; the upstream menu, with the
server hot-switch, in `lovelyzy7/NieR-Re-In-Carnation-Mod_Menu`. They are two
independent repositories (option A): this script is the governance between them.
It checks three things:

  1. **Pins.** The checkouts are at the SHAs in `menu.lock.json` (a warning, and
     a failure, when they have moved; `--update` records the new pair after a
     review).
  2. **Files.** Every file under `{en,jp}-client/modmenu` is compared byte for
     byte. Only the files in `scripts/menu_parity.allow` may differ, and each
     entry says why. A difference anywhere else means one repository changed
     something the other has not seen.
  3. **Features.** The menu's feature catalog (`Main.cpp`) must match: the same
     entries, the same labels, the same types and ranges, in the same order —
     with the server hot-switch group (feature numbers 7–16) removed, which is
     the one deliberate difference. A renamed label or a changed slider range
     fails here even though it lives in an allowed-to-differ file.

Exit code 0 when everything matches, 1 otherwise, so it can gate a sync.
"""
import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOCK = ROOT / "menu.lock.json"
ALLOW = ROOT / "scripts/menu_parity.allow"
CLIENTS = ("en-client", "jp-client")

# What the device build leaves out: the server hot-switch category and its
# features. Everything else must match the original menu exactly.
HOT_SWITCH_CATEGORY = "Category_服务器热切换"
HOT_SWITCH_NUMBERS = range(7, 17)
HOT_SWITCH_MARKERS = ("srvInit", "srvNote", "hotSwitchBox", "服务器热切换")

# Build output, IDE state and signing material: not sources, not compared.
SKIP_DIRS = {".gradle", "build", ".cxx", ".idea", ".git", "dist", "__pycache__", "logs", "output", "backups"}
SKIP_NAMES = {"local.properties", ".DS_Store"}
SKIP_SUFFIXES = (".iml", ".log", ".apk", ".aab", ".pyc", ".err", ".out")

# The menu module and the scripts that build and inject it: what a build uses.
# The original repository also keeps research scripts (archive/, dist/), which
# the device repository was started without.
COMPARED = ("modmenu", "tools")
CATALOG_FILE = "modmenu/app/src/main/jni/Main.cpp"


def skip(path, root):
    rel = path.relative_to(root)
    if any(part in SKIP_DIRS for part in rel.parts):
        return True
    if path.name in SKIP_NAMES or path.name.endswith(SKIP_SUFFIXES):
        return True
    return False


def tree(root):
    """Relative path → sha256, for every source file under a checkout."""
    found = {}
    for path in sorted(root.rglob("*")):
        if path.is_file() and not skip(path, root):
            found[path.relative_to(root).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    return found


def allow_list(path=ALLOW):
    """Paths that may differ, relative to a client folder; `#` starts a reason."""
    entries = {}
    if not path.is_file():
        return entries
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.split("#", 1)[0].strip()
        if line:
            entries[line] = True
    return entries


def head(repo):
    """(sha, clean) for a checkout, or (None, None) when it is not one."""
    try:
        sha = subprocess.run(["git", "-C", str(repo), "rev-parse", "HEAD"],
                             capture_output=True, text=True, check=True).stdout.strip()
        status = subprocess.run(["git", "-C", str(repo), "status", "--porcelain"],
                                capture_output=True, text=True, check=True).stdout
    except Exception:
        return None, None
    return sha, not status.strip()


def catalog(repo, client):
    """The ordered feature list from Main.cpp: ["Category_战斗功能", "1_SeekBar_…", …]."""
    source = Path(repo) / client / CATALOG_FILE
    text = source.read_text(encoding="utf-8", errors="replace")
    if "std::vector<std::string> feats;" not in text:
        raise SystemExit(f"{source} has no feats vector; the menu changed shape")
    block = text.split("std::vector<std::string> feats;", 1)[1].split("jobjectArray", 1)[0]
    items = re.findall(r'feats\.push_back\("([^"]*)"\)|feats\.push_back\(std::string\("([^"]*)"\)', block)
    return [a or b for a, b in items]


def feature_number(entry):
    match = re.match(r"(\d+)_", entry)
    return int(match.group(1)) if match else None


def without_hot_switch(features):
    """The catalog minus the server hot-switch category and features 7–16."""
    kept = []
    for entry in features:
        if entry == HOT_SWITCH_CATEGORY:
            continue
        if feature_number(entry) in HOT_SWITCH_NUMBERS:
            continue
        kept.append(entry)
    return kept


def markers(repo, client):
    """Which hot-switch identifiers a checkout still contains."""
    base = Path(repo) / client / "modmenu/app/src/main"
    text = ""
    for name in ("java", "jni"):
        for path in (base / name).rglob("*"):
            if path.is_file() and path.suffix in (".java", ".cpp", ".hpp", ".h", ".c"):
                text += path.read_text(encoding="utf-8", errors="replace")
    return {marker: text.count(marker) for marker in HOT_SWITCH_MARKERS}


def resolve(args):
    """The two checkouts: --bunker/--original, then the environment, then nearby folders."""
    home = Path.home()
    candidates = {
        "bunker": [args.bunker, os.environ.get("LUNAR_MENU_BUNKER"),
                   ROOT / "bunker-modmenu", ROOT.parent / "bunker-modmenu",
                   home / "bunker-modmenu"],
        "original": [args.original, os.environ.get("LUNAR_MENU_ORIGINAL"),
                     ROOT.parent / "NieR-Re-In-Carnation-Mod_Menu",
                     ROOT.parent / "NieRReincarnation" / "NieR-Re-In-Carnation-Mod_Menu",
                     home / "NieR-Re-In-Carnation-Mod_Menu"],
    }
    found = {}
    for key, options in candidates.items():
        for option in options:
            if option and Path(option).is_dir() and (Path(option) / ".git").exists():
                found[key] = Path(option).resolve()
                break
        else:
            tried = ", ".join(str(o) for o in options if o)
            raise SystemExit(f"{key} menu repository not found (tried: {tried}); "
                             f"pass --{key} or set LUNAR_MENU_{key.upper()}")
    return found["bunker"], found["original"]


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--bunker", type=Path, help="checkout of lovelyzy7/bunker-modmenu")
    parser.add_argument("--original", type=Path, help="checkout of lovelyzy7/NieR-Re-In-Carnation-Mod_Menu")
    parser.add_argument("--update", action="store_true", help="record the checkouts' current SHAs in menu.lock.json")
    parser.add_argument("--json", action="store_true", help="print the report as JSON")
    args = parser.parse_args()

    bunker, original = resolve(args)
    lock = json.loads(LOCK.read_text(encoding="utf-8")) if LOCK.is_file() else {"bunker": None, "original": None}
    allowed = allow_list()

    report = {"pins": {}, "files": {}, "features": {}, "problems": [], "warnings": []}
    problems, warnings = report["problems"], report["warnings"]

    # 1. Pins.
    for key, repo in (("bunker", bunker), ("original", original)):
        sha, clean = head(repo)
        if sha is None:
            problems.append(f"{key}: {repo} is not a git checkout")
            continue
        if not clean:
            warnings.append(f"{key}: {repo.name} has uncommitted changes; the comparison is of the working tree")
        pinned = lock.get(key)
        report["pins"][key] = {"path": str(repo), "head": sha, "pinned": pinned, "clean": clean}
        if pinned and pinned != sha and not args.update:
            problems.append(f"{key}: HEAD is {sha[:12]} but menu.lock.json pins {pinned[:12]} "
                            f"(review the change, then rerun with --update)")
    if args.update:
        lock = {"bunker": report["pins"].get("bunker", {}).get("head"),
                "original": report["pins"].get("original", {}).get("head"),
                "note": "Pinned by scripts/check_menu_parity.py --update after a review."}
        LOCK.write_text(json.dumps(lock, indent=1) + "\n", encoding="utf-8")
        report["pins"]["updated"] = True

    # 2. Files.
    for client in CLIENTS:
        left, right = {}, {}
        for folder in COMPARED:
            left.update({f"{folder}/{p}": h for p, h in tree(bunker / client / folder).items()})
            right.update({f"{folder}/{p}": h for p, h in tree(original / client / folder).items()})
        differing = sorted(p for p in left if p in right and left[p] != right[p])
        only_bunker = sorted(set(left) - set(right))
        only_original = sorted(set(right) - set(left))
        for path in differing:
            if path not in allowed:
                problems.append(f"{client}: {path} differs but is not in scripts/menu_parity.allow")
        for path in only_bunker:
            if path not in allowed:
                problems.append(f"{client}: {path} exists only in the bunker repository")
        for path in only_original:
            if path not in allowed:
                problems.append(f"{client}: {path} exists only in the original repository")
        for path in sorted(allowed):
            if path in left and path in right and left[path] == right[path]:
                warnings.append(f"{client}: {path} no longer differs; remove it from scripts/menu_parity.allow")
        report["files"][client] = {"compared": len(set(left) | set(right)), "differing": differing,
                                   "only_bunker": only_bunker, "only_original": only_original}

    # 3. Features: the same menu, minus the hot-switch group.
    for client in CLIENTS:
        bunker_features = without_hot_switch(catalog(bunker, client))
        original_features = catalog(original, client)
        if without_hot_switch(original_features) != bunker_features:
            missing = [f for f in without_hot_switch(original_features) if f not in bunker_features]
            extra = [f for f in bunker_features if f not in without_hot_switch(original_features)]
            problems.append(f"{client}: the feature catalog differs from the original's (minus the hot-switch)"
                            + (f"; missing in bunker: {missing}" if missing else "")
                            + (f"; only in bunker: {extra}" if extra else "")
                            + ("" if missing or extra else "; same entries, different order"))
        report["features"][client] = {"bunker": len(bunker_features),
                                      "original_without_hot_switch": len(without_hot_switch(original_features)),
                                      "hot_switch_entries": len(original_features) - len(without_hot_switch(original_features))}
    if catalog(bunker, "en-client") != catalog(bunker, "jp-client"):
        problems.append("bunker: the en-client and jp-client menus list different features")
    if catalog(original, "en-client") != catalog(original, "jp-client"):
        problems.append("original: the en-client and jp-client menus list different features")

    # 4. Markers: the hot-switch is the only difference, and only in the original.
    for client in CLIENTS:
        device, upstream = markers(bunker, client), markers(original, client)
        still_there = {k: v for k, v in device.items() if v}
        gone = {k: v for k, v in upstream.items() if not v}
        if still_there:
            problems.append(f"{client}: the bunker menu still contains {sorted(still_there)}")
        if gone:
            problems.append(f"{client}: the original menu has lost {sorted(gone)} (was the removal carried back?)")

    report["ok"] = not problems
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=1))
    else:
        for key, pin in report["pins"].items():
            if key == "updated":
                print("pins: menu.lock.json updated")
            else:
                state = "pinned" if pin["pinned"] == pin["head"] else f"pinned {pin['pinned']}"
                print(f"{key}: {pin['head'][:12]} ({state}){' · dirty' if not pin['clean'] else ''}")
        for client, files in report["files"].items():
            print(f"{client}: {files['compared']} files, {len(files['differing'])} allowed to differ"
                  + (f" ({', '.join(Path(p).name for p in files['differing'])})" if files["differing"] else ""))
        for client, feats in report["features"].items():
            print(f"{client}: {feats['bunker']} features, matching the original minus "
                  f"{feats['hot_switch_entries']} hot-switch entries")
        for line in warnings:
            print("warning:", line)
        for line in problems:
            print("problem:", line)
        print("result:", "OK" if report["ok"] else f"FAIL ({len(problems)} problem(s))")
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
