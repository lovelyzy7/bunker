#!/usr/bin/env python3
"""Assemble generated build sources from the exact submodule commits."""
from pathlib import Path
import hashlib
import io
import json
import shutil
import subprocess
import tarfile
import tempfile

ROOT = Path(__file__).resolve().parents[1]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def export(name, target, *paths):
    archive = subprocess.check_output([
        "git", "-C", str(ROOT / "upstream" / name), "archive", "HEAD", *paths
    ])
    with tarfile.open(fileobj=io.BytesIO(archive)) as source:
        source.extractall(target, filter="data")


def prepare():
    pins = json.loads((ROOT / "upstream.lock.json").read_text(encoding="utf-8"))
    for name, expected in pins.items():
        module = ROOT / "upstream" / name
        if not (module / ".git").exists():
            raise RuntimeError("Run git submodule update --init --recursive first")
        actual = subprocess.check_output(["git", "-C", str(module), "rev-parse", "HEAD"], text=True).strip()
        if actual != expected:
            raise RuntimeError(f"{name} must be pinned to {expected}; run git submodule update --init --recursive")
        dirty = subprocess.check_output(["git", "-C", str(module), "status", "--porcelain", "--untracked-files=no"], text=True)
        if dirty:
            raise RuntimeError(f"{name} has edits. Put Android changes in overlays/ or patches/.")

    work = ROOT / ".build"
    work.mkdir(exist_ok=True)
    marker = work / "prepared.json"
    previous = json.loads(marker.read_text(encoding="utf-8")) if marker.exists() else {}
    for name, expected in previous.items():
        path = ROOT / name
        if path.exists() and digest(path) != expected:
            raise RuntimeError(f"Generated file was edited: {name}. Preserve that edit in overlays/ before rebuilding.")

    with tempfile.TemporaryDirectory(prefix="prepare-", dir=work) as temp:
        stage = Path(temp)
        output = stage / "output"
        output.mkdir()
        export("lunar-tear", output, "server")
        base = stage / "base"
        export("lunar-base", base, "web", "tools", "LICENSE")
        patcher = stage / "patcher"
        export("lunar-tear-masterdata-patcher", patcher,
               "patch_masterdata.py", "config.json", "IDs.md", "LICENSE", "README.md")

        python = output / "android/app/src/main/python"
        python.mkdir(parents=True)
        shutil.copytree(base / "web", python / "web")
        (python / "tools").mkdir()
        # extract_names.py still lives in lunar-base's tools; the master-data
        # dump tools moved to the lunar-scripts repos (lunar-base dropped them).
        shutil.copy2(base / "tools" / "extract_names.py", python / "tools" / "extract_names.py")
        for name in ("dump_masterdata.py", "schemas.json"):
            shutil.copy2(ROOT / "upstream/lunar-scripts" / name, python / "tools" / name)
        (python / "tools/__init__.py").touch()
        shutil.copytree(patcher, python / "patcher")
        (python / "patcher/__init__.py").touch()

        grant = output / "server/internal/lunarbase"
        grant.mkdir()
        for path in (base / "tools/grant/src").glob("*.go"):
            # Byte-for-byte: text mode decoded with the locale codec (GBK on this
            # host) and rewrote LF as CRLF, which made every patch fail to apply.
            (grant / path.name).write_bytes(
                path.read_bytes().replace(b"package main", b"package lunarbase"))
        shutil.copy2(base / "LICENSE", grant / "LICENSE")
        shutil.copytree(ROOT / "overlays/server", output / "server", dirs_exist_ok=True)
        shutil.copytree(ROOT / "overlays/python", python, dirs_exist_ok=True)
        for patch in sorted((ROOT / "patches").glob("*.patch")):
            applied = subprocess.run(["git", "apply", "--directory=" + output.relative_to(ROOT).as_posix(),
                                      str(patch)], cwd=ROOT, capture_output=True, text=True)
            if applied.returncode:
                raise RuntimeError(f"{patch.name} did not apply: {applied.stderr.strip()[:800]}")

        files = {str(path.relative_to(output)): digest(path) for path in output.rglob("*") if path.is_file()}
        # Validate the entire update before replacing any generated source.
        unowned = [name for name, expected in files.items()
                   if name not in previous and (ROOT / name).exists()
                   and digest(ROOT / name) != expected]
        if unowned:
            raise RuntimeError("Refusing to replace unowned files: " + ", ".join(unowned[:10]))
        for name in previous.keys() - files.keys():
            (ROOT / name).unlink(missing_ok=True)
        for name in files:
            target = ROOT / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(output / name, target)
        pending = marker.with_suffix(".tmp")
        pending.write_text(json.dumps(files, indent=2) + "\n", encoding="utf-8")
        pending.replace(marker)
    print(f"Prepared {len(files)} files from five pinned submodules.")


if __name__ == "__main__":
    prepare()
