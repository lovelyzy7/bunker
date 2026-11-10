#!/usr/bin/env python3
"""Merges .i18n-staging/*.json (EN→ZH page strings) into bunker-i18n.js's ZH dict.

Each staging file is a JSON object: English original → Chinese. Keys are
normalized the way bunker-i18n.js matches text (whitespace collapsed, trimmed)
and inserted into the ZH dictionary; an entry whose key is already there is
left alone (the existing translation wins). Run again whenever a staging file
changes; the merge is idempotent.

  python scripts/merge_i18n.py          # merge every .i18n-staging/*.json
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DICT = ROOT / "overlays/python/web/static/js/bunker-i18n.js"
STAGING = ROOT / ".i18n-staging"


def norm(s):
    return " ".join(s.split())


def js_string(s):
    return json.dumps(s, ensure_ascii=False)


def main():
    text = DICT.read_text(encoding="utf-8")
    # The ZH dictionary: from `var ZH = {` to its closing `};`.
    begin = re.search(r"var ZH = \{", text)
    if not begin:
        raise SystemExit("bunker-i18n.js: no ZH dictionary")
    end = text.index("\n  };", begin.end())
    head, body, tail = text[:begin.end()], text[begin.end():end], text[end:]
    have = set(re.findall(r'^\s*"((?:[^"\\]|\\.)*)":', body, re.M))
    have = {norm(bytes(k, "utf-8").decode("unicode_escape") if "\\u" in k else k) for k in have}
    # JSON-unescape the keys properly (the file's keys are JSON string literals).
    have = set()
    for line in body.splitlines():
        m = re.match(r'^\s*("(?:[^"\\]|\\.)*")\s*:', line)
        if m:
            have.add(norm(json.loads(m.group(1))))
    added = 0
    lines = []
    for path in sorted(STAGING.glob("*.json")):
        entries = json.loads(path.read_text(encoding="utf-8"))
        for en, zh in entries.items():
            key = norm(en)
            if key in have or not zh:
                continue
            have.add(key)
            lines.append(f"    {js_string(key)}: {js_string(zh)},")
            added += 1
    if lines:
        body = body.rstrip() + "\n" + "\n".join(lines) + "\n  "
        DICT.write_text(head + body + tail[len("\n  "):], encoding="utf-8")
    print(f"merge_i18n: {added} entries added from {len(list(STAGING.glob('*.json')))} staging files")


if __name__ == "__main__":
    main()
