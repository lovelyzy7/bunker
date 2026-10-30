"""Browser build driver: the same Android build as scripts/build.py, in Pyodide.

The page mirrors the repository under /repo, mounts the player's own files
read-only under /input and the prebuilt bundles under /bundles. Nothing is
uploaded anywhere; everything runs in the browser.
"""
from pathlib import Path
import sys
import zipfile

# The browser mounts the repository at /repo; on a command line this file's own
# parent says where it is, which is what CI and local test runs need.
REPO = Path("/repo") if Path("/repo/android/tools").is_dir() else Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "android/tools"))

import apk_sign  # noqa: E402
import assemble_apk  # noqa: E402
import region  # noqa: E402
import zh_client  # noqa: E402

MASTER = region.MASTER

# Signing material per client (§8.2 key auto-select): JP uses the aligned
# public Bunker key (nieR-jp key, see web/signing/README-KEY-ALIGNMENT.md),
# EN uses the收编 debug key exported from en-client/keys/nier-en.keystore.
SIGNING = {
    "jp": (REPO / "web/signing/bunker-key.pem", REPO / "web/signing/bunker-cert.der"),
    "en": (REPO / "web/signing/nier-en-key.pem", REPO / "web/signing/nier-en-cert.der"),
}


def verify(apk, master, release):
    """Refuse files that are not the release this build's offsets were read from.

    Only the SHA-256 is compared: the size follows from it, and a split APK
    from an app bundle has the same library and metadata but a different
    overall size, which is why the page offers an override.
    """
    expected = region.REGIONS[release]
    if region.sha256_of(apk) != expected["sha256"]:
        raise ValueError(f"The game APK is not the original 3.7.1 {expected['name']} release (SHA-256 does not match)")
    if region.sha256_of(master) != region.MASTER_SHA256:
        raise ValueError(f"The master data is not the original {MASTER} (SHA-256 does not match)")


def addresses(port_offset=0):
    """The game's server addresses (game, assets, accounts), moved by the port offset.

    The endpoint is fixed at 127.0.0.1: the server runs on the device itself,
    so there is no host parameter and no build can bake another IP in.
    """
    port_offset = int(port_offset)
    if not 0 <= port_offset <= 65535 - 8080:
        raise ValueError(f"Port offset must be 0–{65535 - 8080}")
    return tuple(f"127.0.0.1:{port + port_offset}" for port in (8003, 8080, 3000))


def menu_payload(resources, release):
    """The Mod Menu's dex files and library for a release, or None.

    resources is the payload the site ships as bundles/modmenu.zip; a folder
    works too, which is how the payload is edited before it is zipped.
    """
    if not resources:
        return None
    bundle = Path(resources)
    if bundle.is_dir():
        read = lambda name: (bundle / name).read_bytes()
        # as_posix(): on Windows relative_to() yields "en\\libniermenu.so", which
        # never matched the "en/…" keys below — the menu was silently dropped
        # from every Windows build.
        names = {p.relative_to(bundle).as_posix() for p in bundle.rglob("*") if p.is_file()}
        close = lambda: None
    elif bundle.is_file():
        payload = zipfile.ZipFile(bundle)
        names = set(payload.namelist())
        # Not `read = payload.read` for later use: that bound method outlives the
        # with block, and calling it after close() raises "Attempt to use ZIP
        # archive that was already closed". The site ships this as a zip, so the
        # Mod Menu never built in the browser.
        read = payload.read
        close = payload.close
    else:
        return None
    try:
        if "shim.dex" not in names or f"{release}/libniermenu.so" not in names:
            return None
        menu_dex = sorted(n for n in names if n.startswith(release + "/menu") and n.endswith(".dex"))
        if not menu_dex:
            return None
        return {"dex": [read("shim.dex")] + [read(n) for n in menu_dex],
                "lib": read(f"{release}/libniermenu.so")}
    finally:
        close()


def detect_release(apk):
    """The client release ("jp"/"en") of the game APK.

    The worker fetches only that release's font payload before building, so a
    build downloads one font zip instead of both clients' payloads.
    """
    return region.region_of_apk(Path(apk))[0]


def build_android(apk, master, companion, output=None, log=print, port_offset=0, modmenu=None,
                  verify_inputs=True, hand_over=None):
    """Build, sign and verify one product: nier-jp.apk or nier-en.apk (§9.1).

    output is a path or None (§9.1 auto-names the product). hand_over takes the
    signed APK in pieces — the 4205647 contract where output itself is "a path,
    or a function that takes the signed APK in pieces", so a callable output is
    that function too: the product then goes out in pieces and its file is
    deleted once over, so the page never holds it whole twice (a browser keeps
    every file in memory). The product is still assembled, signed and gated on
    a file, because the verification chain reads it.
    """
    # Pyodide delivers JS null as a truthy JsNull proxy (JS undefined → None), so
    # "no output name", "no menu payload" and "no hand-over" from the page must
    # be normalized before the None checks below; Path(JsNull) raises TypeError.
    if type(output).__name__ in ("JsNull", "JsUndefined"):
        output = None
    if type(modmenu).__name__ in ("JsNull", "JsUndefined"):
        modmenu = None
    if type(hand_over).__name__ in ("JsNull", "JsUndefined"):
        hand_over = None
    if callable(output):
        # 4205647's shape: the output parameter itself is the hand-over.
        hand_over, output = output, None
    addresses(port_offset)  # Validate before the slow steps.
    release, package = region.region_of_apk(Path(apk))
    log(f"{region.REGIONS[release]['name']}: {package}")
    if verify_inputs:
        log("Checking the game APK and master data…")
        verify(apk, master, release)
    # Client auto-dispatch + bunker/zh consistency gate (fail-fast). The
    # profile selects the zh patch face (inside assemble), the signing key and
    # the product name; --skip-checks only relaxes the triple assertion (split
    # APK bundles), never the package-level agreement.
    profile = zh_client.dispatch(apk, strict=verify_inputs)
    log(f"Client dispatch: {profile['region']} → {region.REGIONS[release]['client']} "
        f"(key {Path(profile['keystore']).name})")
    menu = menu_payload(modmenu, release)
    if modmenu and menu is None:
        log("The Mod Menu payload is missing; building without it.")
    elif menu:
        log(f"Mod Menu payload: {len(menu['dex'])} dex, 1 library.")
    # Product naming contract (§9.1): auto-named from the client detection,
    # not from a caller-chosen file name.
    if output is None:
        output = Path(profile["product_name"])
    output = Path(output)
    built = assemble_apk.assemble(Path(apk), Path(master), Path(companion), output,
                                  log=log, port_offset=int(port_offset), menu=menu,
                                  strict_detection=verify_inputs, profile=profile)
    log("Signing with the region key…")
    key_pem, cert_der = SIGNING[profile["region"]]
    # The digest comes out of the signing pass, so the finished APK is not read
    # a second time just to hash it.
    certificate, sha256 = apk_sign.sign_and_digest(
        output, key_pem, cert_der,
        progress=lambda percent: log(f"  signing {percent}%…"))
    # Signature gate (§8.2): the product's certificate must match the region key.
    # client_detect_triple is enforced only in strict mode; with skip-check the
    # triple is intentionally unverified (split-APK bundles, skip-check), so it
    # is recorded as "skipped" instead of failing the gate. False still fails.
    cert_ok = certificate == profile["cert_sha256"]
    triple = bool(profile["zh"].get("detected", {}).get("triple_ok"))
    gates = {"client_detect_triple": triple if verify_inputs else "skipped",
             "bunker_zh_consistency": True, "cert_matches_expected": cert_ok, "signed": True}
    gates["ok"] = all(v for v in gates.values() if v != "skipped")
    if not gates["ok"]:
        raise ValueError(f"verification gate failed: {gates} (cert={certificate}, "
                         f"expected={profile['cert_sha256']})")
    patch_counts = {"mod_menu_dex": len(menu["dex"]) if menu else 0,
                    "mod_menu": bool(menu),
                    "fix3_strings": (built.get("fix3_strings") or {}).get("lines_patched"),
                    "font_payload_entries": (built.get("font_payload") or {}).get("count")}
    if "fix4_strings" in built:
        # fix4 两态纯化（EN=fix4 态）；JP=fix3 终态不带 fix4 计数，sidecar 形状不变
        patch_counts["fix4_strings"] = (built.get("fix4_strings") or {}).get("lines_patched")
    sidecar = zh_client.write_manifest_sidecar(
        output, profile, input_apk=Path(apk), cert_sha256=certificate,
        patch_counts=patch_counts,
        verify_gates=gates)
    # L6 产物验证门（签名后，fail-fast）：与 lunar-scripts-zh 侧同 schema
    # （nier-verify-gate/v1）——region 匹配 / 证书断言 / RVA 表按客户端选对 /
    # 字体四条目完整性 / fix3（optional）/ 内嵌 master 文件名不变+文本表结构 /
    # rva_table_version 槽位。断言定义 = upstream/lunar-scripts-zh/shared/。
    import verify_gate_zh
    l6 = verify_gate_zh.product_gate(Path(output), bin_e=None,
                                     client=profile["region"],
                                     product_class="bunker",
                                     sidecar=Path(sidecar),
                                     raise_on_fail=True)
    gates["l6_unified_gate"] = True
    log(f"Signed APK ready to install. Sidecar: {Path(sidecar).name}")
    if hand_over is not None:
        # 4205647's delivery: the signed APK goes to the page in pieces and its
        # file is deleted once over (a browser keeps every file in memory).
        # apk_sign.StreamSigner (the same commit's android/tools half) signs as
        # the APK is written; it takes over here once assemble_apk.assemble
        # accepts a stream — its Path wrapper and pre-sign L6 gate read the
        # product file today, which is why the file exists at all.
        log("Handing the signed APK to the page in pieces…")
        pieces = _Pieces(hand_over)
        with open(output, "rb") as product:
            for chunk in iter(lambda: product.read(pieces.size), b""):
                pieces.write(chunk)
        pieces.flush()
        Path(output).unlink()
        Path(sidecar).unlink()
    built = built if isinstance(built, dict) else {}
    built["sha256"] = sha256
    built["certificate"] = certificate
    built["product_name"] = output.name
    built["product_path"] = str(output)
    built["sidecar"] = str(sidecar)
    built["verify_gates"] = gates
    built["l6_gate"] = l6.to_dict()
    return built


class _Pieces:
    """Hands the APK to the page's function in 4 MB pieces as it is written: it never sits whole in memory here."""

    def __init__(self, hand_over, size=4 << 20):
        self.hand_over, self.size, self.buffer = hand_over, size, bytearray()

    def write(self, data):
        self.buffer += data
        if len(self.buffer) >= self.size:
            self.flush()
        return len(data)

    def flush(self):
        if self.buffer:
            self.hand_over(bytes(self.buffer))
            self.buffer = bytearray()


def _utf8_console():
    """Print 日服, ✓ and … on Windows too: a cp936 console raises or mangles them."""
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass


def main():
    """Command-line entry point: the same build the page runs in the browser."""
    import argparse
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--apk", type=Path, required=True, help="Original ARM64 game 3.7.1 APK (日服 or 全球服)")
    parser.add_argument("--master", type=Path, required=True, help="Original 20240404193219.bin.e")
    parser.add_argument("--companion-apk", type=Path, required=True, help="Built launcher APK (android/app)")
    parser.add_argument("--output", type=Path, default=None,
                        help="Output APK (default: the detected client's product name, "
                             "nier-jp.apk / nier-en.apk; §9.1)")
    parser.add_argument("--port-offset", type=int, default=0)
    parser.add_argument("--mod-menu", nargs="?", const=str(REPO / "web/modmenu"), default=None,
                        help="Add the Mod Menu; optionally name the payload folder or zip")
    parser.add_argument("--skip-checks", action="store_true", help="Build even if the input SHA-256 differs")
    args = parser.parse_args()
    _utf8_console()
    build_android(args.apk, args.master, args.companion_apk, args.output, port_offset=args.port_offset,
                  modmenu=args.mod_menu, verify_inputs=not args.skip_checks)


if __name__ == "__main__":
    main()
