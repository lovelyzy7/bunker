#!/usr/bin/env python3
"""Download a build input: the original game APK or the master data file.

  fetch_input.py https://drive.google.com/file/d/FILE_ID/view game.apk
  fetch_input.py https://github.com/OWNER/REPO/releases/download/TAG/NAME master.bin.e
  fetch_input.py https://api.github.com/repos/OWNER/REPO/releases/assets/123 game.apk

A browser download link for a private release asset answers 404 even with a
token, so those go through the API (`Accept: application/octet-stream`) or
through `gh release download` when the CLI is installed. Google Drive links
need a confirmation token, so `gdown` handles them when available.

Nothing here is specific to this repository; the CI workflow and a local build
use the same code path. SHA-256 verification is optional but recommended.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import urllib.request

BLOCK = 1 << 20


def classify(url):
    """(kind, parts) for a URL: drive, gh-release, gh-asset or plain."""
    if re.search(r"drive\.google\.com|drive\.usercontent\.google\.com", url):
        return "drive", url
    match = re.match(r"https?://(?:www\.)?github\.com/([^/]+)/([^/]+)/releases/download/([^/]+)/(.+)$", url)
    if match:
        return "gh-release", match.groups()
    match = re.match(r"https?://api\.github\.com/repos/([^/]+)/([^/]+)/releases/assets/(\d+)$", url)
    if match:
        return "gh-asset", match.groups()
    return "plain", url


def drive_id(url):
    match = re.search(r"/file/d/([A-Za-z0-9_-]+)", url) or re.search(r"[?&]id=([A-Za-z0-9_-]+)", url)
    if not match:
        raise SystemExit(f"Cannot find a file id in {url}")
    return match.group(1)


def download(url, output, token=None, log=print):
    """Fetch url into output; returns the downloaded size."""
    kind, parts = classify(url)
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    if kind == "drive":
        file_id = drive_id(url)
        try:
            import gdown
        except ImportError:
            gdown = None
        if gdown:
            log(f"Google Drive {file_id} with gdown")
            gdown.download(id=file_id, output=str(output), quiet=False, fuzzy=True, confirm=True)
            return output.stat().st_size
        # No gdown: the usercontent host skips the virus-scan interstitial.
        url = f"https://drive.usercontent.google.com/download?id={file_id}&export=download&confirm=t"
        kind = "plain"
    if kind == "gh-release":
        owner, repo, tag, name = parts
        if token and shutil.which("gh"):
            log(f"Release asset {owner}/{repo}@{tag}/{name} with gh")
            subprocess.run(["gh", "release", "download", tag, "-R", f"{owner}/{repo}", "-p", name,
                            "-O", str(output), "--clobber"], check=True, env={**os.environ, "GH_TOKEN": token})
            return output.stat().st_size
        api = f"https://api.github.com/repos/{owner}/{repo}/releases/tags/{tag}"
        log(f"Release {owner}/{repo}@{tag} with the API")
        url = f"https://api.github.com/repos/{owner}/{repo}/releases/assets/{asset_id(api, name, token)}"
        kind = "gh-asset"
    request = urllib.request.Request(url, headers={"User-Agent": "bunker-build"})
    if kind == "gh-asset":
        if token:
            request.add_header("Authorization", f"Bearer {token}")
        request.add_header("Accept", "application/octet-stream")
    log(f"GET {url}")
    total = 0
    with urllib.request.urlopen(request) as response, open(output, "wb") as target:
        length = int(response.headers.get("Content-Length") or 0)
        while chunk := response.read(BLOCK):
            target.write(chunk)
            total += len(chunk)
            if length:
                log(f"  {total / length:5.1%}  {total / (1 << 20):.0f} MiB", )
    return total


def asset_id(api, name, token):
    """The numeric id of a release asset, by file name."""
    request = urllib.request.Request(api, headers={"User-Agent": "bunker-build"})
    if token:
        request.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(request) as response:
        release = json.load(response)
    for asset in release.get("assets", []):
        if asset.get("name") == name:
            return asset["id"]
    raise SystemExit(f"{name} is not an asset of {api}")


def sha256(path):
    digest = hashlib.sha256()
    with open(path, "rb") as source:
        while chunk := source.read(BLOCK):
            digest.update(chunk)
    return digest.hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("url")
    parser.add_argument("output", type=Path)
    parser.add_argument("--sha256", help="Expected SHA-256; the download is refused when it differs")
    parser.add_argument("--token", default=os.environ.get("GAME_ASSET_TOKEN"),
                        help="GitHub token for private release assets (default: $GAME_ASSET_TOKEN)")
    args = parser.parse_args()
    size = download(args.url, args.output, token=args.token)
    print(f"Downloaded {size} bytes to {args.output}")
    if args.sha256:
        got = sha256(args.output)
        if got.lower() != args.sha256.lower():
            args.output.unlink(missing_ok=True)
            raise SystemExit(f"SHA-256 mismatch: expected {args.sha256}, got {got}")
        print(f"SHA-256 matches {got}")


if __name__ == "__main__":
    main()
