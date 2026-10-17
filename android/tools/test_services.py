#!/usr/bin/env python3
"""Every save-editing service must be wired to the native bridge.

The device has no desktop grant executable: `config.GRANT_EXE_PATH` is not
defined at all. A service whose helpers still shell out to it raises
AttributeError and the page answers `Internal Server Error` the moment it is
used — which is exactly how the Profile, Mission and Quest editors were broken
until adapt_services() covered them.

Run with the Android Python requirements installed (no save is needed):

    python android/tools/test_services.py
"""
from __future__ import annotations

import importlib
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "android/app/src/main/python"))

import android_runtime  # noqa: E402

# Services whose writes go through the grant engine, with their helper names.
SHARED = ("_ensure_shim_available", "_invoke_shim")
PROFILE_NAMES = {"tutorial_service": ("_ensure_shim", "_invoke")}


def services_using_shim() -> list[str]:
    """Modules that still reference the desktop grant executable."""
    found = []
    for path in sorted((ROOT / "android/app/src/main/python/web/services").glob("*.py")):
        text = path.read_text(encoding="utf-8")
        if "GRANT_EXE_PATH" in text and path.stem != "setup_service":  # setup is desktop-only
            found.append(path.stem)
    return found


def main() -> int:
    modules = services_using_shim()
    if not modules:
        raise SystemExit("no service refers to the grant executable; the scan is wrong")

    calls = []

    def native(data_root, asset_root, raw):
        calls.append(json.loads(raw))
        return json.dumps({"ok": True, "applied": 1})

    with tempfile.TemporaryDirectory(prefix="services-") as work:
        data = Path(work) / "saves"
        data.mkdir()
        android_runtime.configure(data, Path(work) / "server", Path(work) / "tools", native, print)
        android_runtime.adapt_services()

    failures = []
    for name in modules:
        module = importlib.import_module("web.services." + name)
        check, invoke = PROFILE_NAMES.get(name, SHARED)
        before = len(failures)
        for helper in (check, invoke):
            fn = getattr(module, helper, None)
            if fn is None:
                failures.append(f"{name}: {helper} missing")
                continue
            # adapt_services() replaces the helper with its own closure; the
            # original one lives in the service module and shells out to the
            # desktop executable (which does not exist on a phone).
            owner = getattr(fn, "__module__", "")
            if owner != "android_runtime":
                failures.append(f"{name}.{helper}: still runs {owner}.{fn.__name__}")
                continue
            if helper != invoke:
                try:
                    fn()
                except Exception as exc:  # the check itself must pass on device
                    failures.append(f"{name}.{helper}(): {exc}")
                continue
            try:
                fn({"action": "probe"})
            except Exception as exc:
                failures.append(f"{name}.{helper}: {exc}")
        print(f"{'OK  ' if len(failures) == before else 'FAIL'} {name}", flush=True)

    payloads = [c for c in calls if c.get("action") == "probe"]
    if not payloads:
        failures.append("the native bridge was never called")
    print(f"{len(modules)} service(s) checked, {len(payloads)} call(s) reached the bridge")
    for failure in failures:
        print("FAIL", failure)
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
