#!/usr/bin/env python3
"""Dumps the pre-patch staged tree (what prepare.py builds before patches/)."""
import shutil, subprocess, sys, tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

out = Path(sys.argv[1] if len(sys.argv) > 1 else ROOT / ".patch-stage")
if out.exists():
    shutil.rmtree(out)
out.mkdir(parents=True)


def export(name, target, *paths):
    result = subprocess.run(["git", "-C", str(ROOT / "upstream" / name), "archive", "HEAD", *paths],
                            capture_output=True, check=True)
    import io, tarfile
    with tarfile.open(fileobj=io.BytesIO(result.stdout)) as tar:
        tar.extractall(target)


export("lunar-tear", out, "server")
base = out / "_base"
export("lunar-base", base, "web", "tools", "LICENSE")
patcher = out / "_patcher"
export("lunar-tear-masterdata-patcher", patcher,
       "patch_masterdata.py", "config.json", "IDs.md", "LICENSE", "README.md")

python = out / "android/app/src/main/python"
python.mkdir(parents=True)
shutil.copytree(base / "web", python / "web")
(python / "tools").mkdir()
shutil.copy2(base / "tools" / "extract_names.py", python / "tools" / "extract_names.py")
shutil.copytree(patcher, python / "patcher")
(python / "patcher/__init__.py").touch()
grant = out / "server/internal/lunarbase"
grant.mkdir()
for path in (base / "tools/grant/src").glob("*.go"):
    (grant / path.name).write_bytes(
        path.read_bytes().replace(b"package main", b"package lunarbase"))
shutil.copy2(base / "LICENSE", grant / "LICENSE")
shutil.copytree(ROOT / "overlays/server", out / "server", dirs_exist_ok=True)
shutil.copytree(ROOT / "overlays/python", python, dirs_exist_ok=True)
print(f"pre-patch stage: {out}")
