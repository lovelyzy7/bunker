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

# lunar-scripts-zh（kind=directory 条目）的调用面契约文件集：pin 摘要按
# path 升序、逐文件 sha256，以规范 JSON（无空白）拼接后再 sha256。
# 与 upstream.lock.json 的 pin.files / pin.sha256 同账本；变更即 bump lock。
ZH_CONTRACT_FILES = (
    "en-client/MANIFEST.json",
    "en-client/keys/nier-en.keystore",
    "en-client/patches/patch_apk_en.py",
    "en-client/patches/patch_auth_dynamic_en.py",
    "jp-client/MANIFEST.json",
    "jp-client/bin-edit.default.json",
    "jp-client/build_bin_e.py",
    "jp-client/keys/nier-jp.keystore",
    "jp-client/patches/patch_apk_jp.py",
    "shared/detect_client.py",
    "shared/manifest_sidecar.py",
    "shared/dump_masterdata.py",
    "shared/gate_defs.py",
    "shared/schemas.json",
    "shared/verify_gate.py",
)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def zh_contract_digest(module):
    """The contract-digest pin for a lunar-scripts-zh checkout (directory form)."""
    rows = [{"path": name, "sha256": digest(module / name)} for name in sorted(ZH_CONTRACT_FILES)]
    return hashlib.sha256(json.dumps(rows, separators=(",", ":")).encode("utf-8")).hexdigest()


def check_zh_module(name, entry):
    """Verify one kind=directory upstream entry: mount + contract digest pin."""
    module = ROOT / "upstream" / name
    if not module.exists():
        raise RuntimeError(
            f"{name}: mount {module} is missing. Recreate the directory junction "
            f"(Windows: New-Item -ItemType Junction -Path '{module}' -Target "
            f"'{entry.get('location')}'), or see .gitmodules upstream-local notes.")
    if not module.is_dir():
        raise RuntimeError(f"{name}: {module} is not a directory/junction mount.")
    pin = entry.get("pin") or {}
    if pin.get("mode") != "contract-digest":
        raise RuntimeError(f"{name}: unsupported pin mode {pin.get('mode')!r}; "
                           f"expected 'contract-digest' for a directory entry.")
    expected_files = tuple(pin.get("files") or ())
    if expected_files != tuple(sorted(ZH_CONTRACT_FILES)):
        raise RuntimeError(f"{name}: upstream.lock.json pin.files disagrees with "
                           f"scripts/prepare.py ZH_CONTRACT_FILES; fix one of them.")
    actual = zh_contract_digest(module)
    if actual != pin.get("sha256"):
        raise RuntimeError(
            f"{name} must be pinned to {pin.get('sha256')}; the directory content digest "
            f"is {actual}. Update upstream.lock.json after reviewing the change "
            f"(equivalent of bumping a submodule commit pin).")
    return actual


def export(name, target, *paths):
    archive = subprocess.check_output([
        "git", "-C", str(ROOT / "upstream" / name), "archive", "HEAD", *paths
    ])
    with tarfile.open(fileobj=io.BytesIO(archive)) as source:
        source.extractall(target, filter="data")


def prepare():
    pins = json.loads((ROOT / "upstream.lock.json").read_text(encoding="utf-8"))
    for name, expected in pins.items():
        if isinstance(expected, dict):
            # kind=directory 等价登记（lunar-scripts-zh）：非 git 仓，不走
            # submodule 的 commit pin；预检 = 挂载 + 契约摘要 pin（见上）。
            check_zh_module(name, expected)
            continue
        module = ROOT / "upstream" / name
        if not (module / ".git").exists():
            raise RuntimeError("Run git submodule update --init --recursive first")
        actual = subprocess.check_output(["git", "-C", str(module), "rev-parse", "HEAD"], text=True).strip()
        if actual != expected:
            raise RuntimeError(f"{name} must be pinned to {expected}; run git submodule update --init --recursive")
        dirty = subprocess.check_output(["git", "-C", str(module), "status", "--porcelain", "--untracked-files=no"], text=True)
        if dirty:
            raise RuntimeError(f"{name} has edits. Put Android changes in overlays/ or patches/.")

    # L6 跨仓验证门（setup 期）：装载 lunar-scripts-zh 后 MANIFEST 预检 + 字体
    # payload 四条目断言（fail-fast）。断言定义/执行器 = upstream/lunar-scripts-zh
    # shared/gate_defs.py + shared/verify_gate.py（同 schema nier-verify-gate/v1）。
    import sys
    tools_dir = ROOT / "android" / "tools"
    if str(tools_dir) not in sys.path:
        sys.path.insert(0, str(tools_dir))
    import verify_gate_zh
    verify_gate_zh.setup_gate()

    work = ROOT / ".build"
    work.mkdir(exist_ok=True)
    marker = work / "prepared.json"
    # A marker written on Windows holds `server\\go.mod`; this script keys every
    # path with forward slashes, so normalize on load (Windows and POSIX runs
    # then agree about what it generated and what is a hand edit).
    previous = ({name.replace("\\", "/"): value
                 for name, value in json.loads(marker.read_text(encoding="utf-8")).items()}
                if marker.exists() else {})
    for name, expected in previous.items():
        path = ROOT / name
        if path.exists() and digest(path) != expected:
            raise RuntimeError(f"Generated file was edited: {name}. Save that edit in overlays/ before rebuilding.")

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
        # dump tools are mirrored in lunar-scripts-zh/shared/ (call-face switch:
        # BUNKER-ADAPT-PLAN §1.7.2 #9 — the lunar-scripts originals stay pinned
        # for provenance but no longer serve the build).
        shutil.copy2(base / "tools" / "extract_names.py", python / "tools" / "extract_names.py")
        for name in ("dump_masterdata.py", "schemas.json"):
            shutil.copy2(ROOT / "upstream/lunar-scripts-zh/shared" / name, python / "tools" / name)
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
            raise RuntimeError("Will not replace: prepare.py did not make " + ", ".join(unowned[:10]))
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
