#!/usr/bin/env python3
"""Drive the built site in a real Chrome: build an APK end to end.

  build_test.py --base http://127.0.0.1:8914/ --game game.apk --master 20240404193219.bin.e
                [--menu] [--skip] [--mobile]

There is no CI job for this: it needs a real 3.7.1 game APK (254 MB), which the
repository does not carry. Run it before a release, from a machine that has the
game files, against the site built from the tag:

  python3 web/build_site.py --companion-apk android/app/build/outputs/apk/debug/app-debug.apk
  python3 -m http.server -d .build/site 8914 &
  python3 tests/browser/build_test.py --base http://127.0.0.1:8914/ \\
      --game /path/game-jp.apk --master /path/20240404193219.bin.e

It prints the log, the step chips and the result card, and saves a screenshot.
Exits non-zero if the build fails or the page reports an error.
"""
import argparse
import base64
import subprocess
import sys
import tempfile
import time
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
from check_ui import Session, cdp_target, chrome_path  # noqa: E402


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--base", default="http://127.0.0.1:8914/", help="where the built site is served")
    parser.add_argument("--game", type=Path, required=True, help="the original 3.7.1 APK")
    parser.add_argument("--master", type=Path, required=True, help="20240404193219.bin.e")
    parser.add_argument("--menu", action="store_true", help="tick the Mod Menu")
    parser.add_argument("--skip", action="store_true", help="tick skip-the-file-check")
    parser.add_argument("--mobile", action="store_true", help="390px instead of 1280px")
    parser.add_argument("--timeout", type=int, default=1800)
    args = parser.parse_args()

    port = 9335
    profile = tempfile.mkdtemp(prefix="bunker-build-")
    browser = subprocess.Popen([chrome_path(), "--headless=new", "--disable-gpu", "--no-first-run",
                                "--no-proxy-server", f"--user-data-dir={profile}",
                                f"--remote-debugging-port={port}", "--remote-allow-origins=*", "about:blank"],
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        for _ in range(80):
            try:
                urllib.request.urlopen(f"http://127.0.0.1:{port}/json/version", timeout=1).read()
                break
            except Exception:
                time.sleep(0.25)
        session = Session(cdp_target(port, args.base))
        session.call("Page.enable")
        session.call("DOM.enable")
        if args.mobile:
            session.call("Emulation.setDeviceMetricsOverride", width=390, height=900, deviceScaleFactor=2, mobile=True)
        for _ in range(120):
            if session.evaluate("document.readyState === 'complete' && !!document.getElementById('build')"):
                break
            time.sleep(0.2)
        time.sleep(0.5)
        if args.menu:
            session.evaluate("document.getElementById('mod-menu').checked = true")
        if args.skip:
            session.evaluate("document.getElementById('skip-check').checked = true")
        root = session.call("DOM.getDocument", depth=2)["root"]["nodeId"]
        for selector, path in (("#game", args.game), ("#master", args.master)):
            node = session.call("DOM.querySelector", nodeId=root, selector=selector)["nodeId"]
            session.call("DOM.setFileInputFiles", files=[str(path)], nodeId=node)
        time.sleep(0.5)
        session.evaluate("document.getElementById('build').click()")

        start, seen = time.time(), 0
        while time.time() - start < args.timeout:
            text = session.evaluate("document.getElementById('log').textContent") or ""
            if len(text) > seen:
                print(text[seen:].rstrip(), flush=True)
                seen = len(text)
            if session.evaluate("getComputedStyle(document.getElementById('result')).display !== 'none'"
                                " || !document.getElementById('failure').hidden"):
                break
            time.sleep(2)
        print("elapsed: %.0fs" % (time.time() - start), flush=True)
        print("steps: " + str(session.evaluate(
            "[...document.querySelectorAll('#steps li')].map(l=>l.className||'-').join(',')")), flush=True)
        if not session.evaluate("document.getElementById('failure').hidden"):
            print("FAILED: " + " | ".join(str(session.evaluate(f"document.getElementById('{k}').textContent"))
                                          for k in ("fail-title", "fail-hint", "fail-raw")), flush=True)
            return 1
        for key in ("built-version", "built-region", "built-menu", "built-size", "built-sha", "built-source"):
            print(key + ": " + str(session.evaluate(f"document.getElementById('{key}').textContent")), flush=True)
        print("download: " + str(session.evaluate("document.getElementById('download').textContent")), flush=True)
        shot = Path(tempfile.gettempdir()) / "bunker-build.png"
        shot.write_bytes(base64.b64decode(session.call("Page.captureScreenshot", format="png")["data"]))
        print("screenshot: " + str(shot), flush=True)
        return 0
    finally:
        browser.terminate()


if __name__ == "__main__":
    sys.exit(main())
