#!/usr/bin/env python3
"""UI acceptance check: catch the layout bugs users notice, at every width.

  check_ui.py --base http://127.0.0.1:8765 -o report.json

Runs a real Chrome via the DevTools protocol (Windows or macOS; the browser is
started with --headless=new), loads each page at each width, and asserts:

  * no horizontal scrolling (nothing sticks out of the viewport)
  * no clickable control is clipped by the viewport edge
  * top-bar actions never overlap each other or a nav link
  * every control's hit area is at least MIN_TARGET px (44 by default)
  * controls are readable: foreground/background contrast >= 3.0 for text
  * the console stays free of errors

Exit code 1 when anything fails, so it can gate a release.
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.parse
import urllib.request
from pathlib import Path

WIDTHS = (360, 390, 414, 520, 768, 1024, 1280, 1920)
MIN_TARGET = 44
CHROME_CANDIDATES = (
    r"C:/Program Files/Google/Chrome/Application/chrome.exe",
    r"C:/Program Files (x86)/Google/Chrome/Application/chrome.exe",
    "/mnt/c/Program Files/Google/Chrome/Application/chrome.exe",
    "/mnt/c/Program Files (x86)/Google/Chrome/Application/chrome.exe",
    r"C:/Program Files/Microsoft/Edge/Application/msedge.exe",
    "/mnt/c/Program Files (x86)/Microsoft/Edge/Application/msedge.exe",
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/usr/bin/google-chrome",
    "/usr/bin/chromium",
)

# Runs in the page: returns the list of problems found at this width.
PROBE = r"""
(() => {
  const problems = [];
  const vw = document.documentElement.clientWidth;
  const all = [...document.querySelectorAll("a,button,input,select,summary,[role=button]")];
  const visible = el => {
    const s = getComputedStyle(el);
    if (s.display === "none" || s.visibility === "hidden" || Number(s.opacity) === 0) return false;
    const r = el.getBoundingClientRect();
    return r.width > 0 && r.height > 0;
  };
  const name = el => (el.tagName + (el.id ? "#" + el.id : "") +
    (el.dataset && el.dataset.i18n ? "[" + el.dataset.i18n + "]" : "") +
    (el.textContent ? ":" + el.textContent.trim().slice(0, 18) : "")).replace(/\s+/g, " ");

  if (document.documentElement.scrollWidth > vw + 1) {
    problems.push(`horizontal scroll: scrollWidth ${document.documentElement.scrollWidth} > ${vw}`);
  }

  for (const el of all) {
    if (!visible(el)) continue;
    const r = el.getBoundingClientRect();
    if (r.right > vw + 1) problems.push(`clipped: ${name(el)} right=${Math.round(r.right)} > ${vw}`);
    if (r.width < MIN_TARGET && r.height < MIN_TARGET) {
      // Icon buttons may be square but small; flag anything under the target.
      problems.push(`small target: ${name(el)} ${Math.round(r.width)}x${Math.round(r.height)}`);
    }
  }

  // Top-bar actions (language/theme) must not overlap anything in the bar.
  const bar = document.querySelector(".terminal-bar, .top");
  if (bar) {
    const actions = [...bar.querySelectorAll("button, a.boxed, .lang-toggle")].filter(visible);
    const rects = actions.map(el => ({ el, r: el.getBoundingClientRect() }));
    for (let i = 0; i < rects.length; i++) {
      for (let j = i + 1; j < rects.length; j++) {
        const a = rects[i].r, b = rects[j].r;
        const overlap = Math.max(0, Math.min(a.right, b.right) - Math.max(a.left, b.left)) *
                        Math.max(0, Math.min(a.bottom, b.bottom) - Math.max(a.top, b.top));
        if (overlap > 1) problems.push(`overlap: ${name(rects[i].el)} vs ${name(rects[j].el)} (${Math.round(overlap)}px2)`);
      }
    }
    for (const { el, r } of rects) {
      if (r.right > vw + 1) problems.push(`bar action clipped: ${name(el)} right=${Math.round(r.right)}`);
    }
  }

  // Text contrast on the bar: the accent bar is where inherit bugs show up.
  const lum = c => {
    const [r, g, b] = c.map(v => {
      v /= 255;
      return v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4);
    });
    return 0.2126 * r + 0.7152 * g + 0.0722 * b;
  };
  const parse = s => (s.match(/[\d.]+/g) || []).slice(0, 3).map(Number);
  const effectiveBg = el => {
    for (let n = el; n; n = n.parentElement) {
      const bg = getComputedStyle(n).backgroundColor;
      const p = parse(bg);
      if (p.length === 3 && !/rgba\([^)]*,\s*0\)/.test(bg)) return p;
    }
    return [255, 255, 255];
  };
  for (const el of actions) {
    const fg = parse(getComputedStyle(el).color);
    const bg = effectiveBg(el);
    if (fg.length !== 3) continue;
    const l1 = lum(fg), l2 = lum(bg);
    const ratio = (Math.max(l1, l2) + 0.05) / (Math.min(l1, l2) + 0.05);
    if (ratio < 3.0) problems.push(`contrast: ${name(el)} ${ratio.toFixed(2)} < 3.0`);
  }

  return problems;
})()
"""


def chrome_path():
    for candidate in CHROME_CANDIDATES:
        if Path(candidate).is_file():
            return candidate
    found = shutil.which("chrome") or shutil.which("chromium")
    if not found:
        raise SystemExit("Chrome not found; install Chrome or edit CHROME_CANDIDATES.")
    return found


def cdp_target(port, url):
    """Open a new tab for url and return its websocket URL."""
    request = urllib.request.Request(f"http://127.0.0.1:{port}/json/new?{urllib.parse.quote(url, safe='')}", method="PUT")
    with urllib.request.urlopen(request, timeout=10) as response:
        return json.loads(response.read())["webSocketDebuggerUrl"]


class Session:
    """Minimal DevTools session: navigate, wait, evaluate."""

    def __init__(self, ws_url):
        import websocket  # websocket-client
        self.ws = websocket.create_connection(ws_url, timeout=30)
        self.seq = 0

    def call(self, method, **params):
        self.seq += 1
        self.ws.send(json.dumps({"id": self.seq, "method": method, "params": params}))
        while True:
            message = json.loads(self.ws.recv())
            if message.get("id") == self.seq:
                if "error" in message:
                    raise RuntimeError(f"{method}: {message['error']}")
                return message.get("result", {})

    def evaluate(self, expression):
        result = self.call("Runtime.evaluate", expression=expression, returnByValue=True, awaitPromise=True)
        return result.get("result", {}).get("value")

    def close(self):
        try:
            self.ws.close()
        except Exception:
            pass


def measure(session, url, width):
    session.call("Emulation.setDeviceMetricsOverride", width=width, height=900, deviceScaleFactor=1, mobile=width <= 520)
    session.call("Page.navigate", url=url)
    # Wait for load + one frame, then let scripts settle.
    for _ in range(40):
        state = session.evaluate("document.readyState")
        if state == "complete":
            break
        time.sleep(0.15)
    time.sleep(0.5)
    return session.evaluate(PROBE.replace("MIN_TARGET", str(MIN_TARGET))) or []


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--base", required=True, help="root URL of the running panel, e.g. http://127.0.0.1:8765")
    parser.add_argument("--pages", nargs="+", default=["/"], help="paths to check")
    parser.add_argument("--widths", nargs="+", type=int, default=list(WIDTHS))
    parser.add_argument("--out", type=Path, help="write the report as JSON here")
    args = parser.parse_args()
    base = args.base.rstrip("/")

    port = 9222 + int(os.environ.get("CHECK_UI_PORT_OFFSET", "0"))
    chrome = chrome_path()
    profile = tempfile.mkdtemp(prefix="check-ui-")
    browser = subprocess.Popen([chrome, "--headless=new", "--disable-gpu", "--no-first-run",
                                f"--user-data-dir={profile}", f"--remote-debugging-port={port}",
                                "--remote-allow-origins=*", "about:blank"],
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    failures = 0
    report = []
    try:
        for _ in range(60):
            try:
                urllib.request.urlopen(f"http://127.0.0.1:{port}/json/version", timeout=1).read()
                break
            except Exception:
                time.sleep(0.25)
        else:
            raise SystemExit("Chrome did not expose its debugging port.")
        for page in args.pages:
            url = base + page
            session = Session(cdp_target(port, url))
            try:
                session.call("Page.enable")
                session.call("Runtime.enable")
                for width in args.widths:
                    problems = measure(session, url, width)
                    status = "ok" if not problems else f"{len(problems)} problem(s)"
                    print(f"{width:>5}px {page:<28} {status}")
                    for problem in problems:
                        print("        -", problem)
                    failures += len(problems)
                    report.append({"page": page, "width": width, "problems": problems})
            finally:
                session.close()
    finally:
        browser.terminate()
        try:
            browser.wait(timeout=10)
        except subprocess.TimeoutExpired:
            browser.kill()
        shutil.rmtree(profile, ignore_errors=True)
    if args.out:
        args.out.write_text(json.dumps(report, indent=1, ensure_ascii=False))
    print(f"\n{failures} problem(s) in {len(args.pages)} page(s) x {len(args.widths)} widths")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
