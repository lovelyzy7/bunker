#!/usr/bin/env python3
"""Every tracked text file must be UTF-8 without a BOM and without mojibake.

  python3 tests/browser/encoding_scan.py   (run from the repository root)
"""
import subprocess, sys
from pathlib import Path

TRACKED = subprocess.run(["git", "ls-files", "-z"], capture_output=True).stdout.split(b"\0")
BINARY = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".ico", ".zip", ".apk", ".jar", ".so", ".dex", ".p12",
          ".der", ".pem", ".bin", ".e", ".wasm", ".ttf", ".otf", ".wav", ".ogg", ".mp3", ".7z", ".iml",
          ".whl", ".gz", ".tgz", ".pyc", ".pkl", ".a", ".o"}
MOJIBAKE = ("â€", "Ã©", "Ã¢", "Â", "ï¿½", "锟斤拷", "锟", "烫烫")
problems = []
for raw in TRACKED:
    if not raw:
        continue
    path = Path(raw.decode("utf-8", "replace"))
    if path.suffix.lower() in BINARY or not path.is_file():
        continue
    data = path.read_bytes()
    if data.startswith(b"\xef\xbb\xbf"):
        problems.append((path, "UTF-8 BOM"))
    if b"\0" in data:
        problems.append((path, "NUL byte"))
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError as error:
        problems.append((path, f"not UTF-8 at byte {error.start}"))
        continue
    for pattern in MOJIBAKE:
        if pattern in text:
            line = text[:text.index(pattern)].count("\n") + 1
            problems.append((path, f"mojibake {pattern!r} on line {line}"))
    if "\ufffd" in text:
        problems.append((path, "U+FFFD replacement character"))
for path, why in problems:
    print(f"{path}: {why}")
print(f"{len(problems)} problem(s) in {len(TRACKED)} tracked files")
sys.exit(1 if problems else 0)
