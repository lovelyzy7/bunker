#!/usr/bin/env python3
"""Sign an APK in place with APK Signature Scheme v2.

  apk_sign.py bunker.apk [--key KEY.pem --cert CERT.der]

Needs only pycryptodome, so the web builder can run it in the browser. The
default key material in web/signing is the **mod-menu JP key**
(nier-jp.keystore, alias nier, password lunar-jp, certificate SHA-256
eec23be0cb205c401791be3d4b82e8851560f5c2aed3ec644166093d3d98a2fe), exported to
PEM (PKCS#8) + DER. It was realigned from the original public Bunker key; see
web/signing/README-KEY-ALIGNMENT.md for the export procedure and rollback.
v2 covers every Android version the game supports (7.0 and newer).
"""
import argparse
import hashlib
import os
from pathlib import Path
import struct

from Crypto.Hash import SHA256
from Crypto.PublicKey import RSA
from Crypto.Signature import pkcs1_15

KEYS = Path(__file__).resolve().parents[2] / "web/signing"
CHUNK = 1 << 20
V2_BLOCK_ID = 0x7109871A
RSA_PKCS1_SHA256 = 0x0103
MAGIC = b"APK Sig Block 42"


def _prefixed(data):
    return struct.pack("<I", len(data)) + data


def _end_of_central_directory(f):
    """Offset of the end-of-central-directory record, the directory's offset and the file size."""
    size = f.seek(0, os.SEEK_END)
    f.seek(max(0, size - 65557))
    tail = f.read()
    at = tail.rfind(b"PK\x05\x06")
    if at < 0:
        raise RuntimeError("Not a ZIP file")
    eocd = size - len(tail) + at
    directory = struct.unpack_from("<I", tail, at + 16)[0]
    f.seek(directory - 16)
    if f.read(16) == MAGIC:
        raise RuntimeError("The APK is already signed")
    return eocd, directory, size


def _digest(f, entries_end, central, eocd, whole=None, progress=None):
    """The v2 content digest: SHA-256 over 1 MB chunks of the entries, central directory and end record.

    whole, when given, is a running SHA-256 that receives the entries as they
    are read (the central directory and end record are fed by the caller, which
    writes the final ones); that saves a second pass over a 300 MB APK, the
    slowest step on a phone.
    """
    chunks = []

    def add(data):
        chunks.append(hashlib.sha256(b"\xa5" + struct.pack("<I", len(data)) + data).digest())
    f.seek(0)
    shown = 0
    for position in range(0, entries_end, CHUNK):
        data = f.read(min(CHUNK, entries_end - position))
        if whole is not None:
            whole.update(data)
        add(data)
        if progress is not None:
            percent = min(100, (position + len(data)) * 100 // max(1, entries_end))
            if percent >= shown + 10:
                shown = percent
                progress(percent)
    for section in (central, eocd):
        for position in range(0, len(section), CHUNK):
            add(section[position:position + CHUNK])
    return hashlib.sha256(b"\x5a" + struct.pack("<I", len(chunks)) + b"".join(chunks)).digest()


def sign(apk, key_pem=KEYS / "bunker-key.pem", cert_der=KEYS / "bunker-cert.der"):
    """Sign the APK in place; returns the certificate's SHA-256."""
    return sign_and_digest(apk, key_pem, cert_der)[0]


def sign_and_digest(apk, key_pem=KEYS / "bunker-key.pem", cert_der=KEYS / "bunker-cert.der", progress=None):
    """Sign the APK in place; returns (certificate SHA-256, signed file's SHA-256).

    The file digest comes from the bytes read while signing, so the caller does
    not need a second pass over the finished APK. progress(percent), if given,
    is called every 10% of the read: signing a 300 MB APK is a long silent wait
    on a phone, and the page shows it.
    """
    key = RSA.import_key(Path(key_pem).read_bytes())
    cert = Path(cert_der).read_bytes()
    with open(apk, "r+b") as f:
        eocd_at, directory, size = _end_of_central_directory(f)
        f.seek(directory)
        central = f.read(eocd_at - directory)
        eocd = f.read()
        whole = hashlib.sha256()
        digest = _digest(f, directory, central, eocd, whole, progress)
        signed_data = (_prefixed(_prefixed(struct.pack("<I", RSA_PKCS1_SHA256) + _prefixed(digest)))
                       + _prefixed(_prefixed(cert)) + _prefixed(b""))
        signature = pkcs1_15.new(key).sign(SHA256.new(signed_data))
        signer = (_prefixed(signed_data)
                  + _prefixed(_prefixed(struct.pack("<I", RSA_PKCS1_SHA256) + _prefixed(signature)))
                  + _prefixed(key.publickey().export_key("DER")))
        value = _prefixed(_prefixed(signer))
        pair = struct.pack("<QI", len(value) + 4, V2_BLOCK_ID) + value
        block_size = len(pair) + 8 + len(MAGIC)
        block = struct.pack("<Q", block_size) + pair + struct.pack("<Q", block_size) + MAGIC
        # The block goes between the entries and the central directory, which moves after it.
        moved = bytearray(eocd)
        struct.pack_into("<I", moved, 16, directory + len(block))
        f.seek(directory)
        f.write(block + central + bytes(moved))
        f.truncate()
        whole.update(block)
        whole.update(central)
        whole.update(bytes(moved))
    return hashlib.sha256(cert).hexdigest(), whole.hexdigest()


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("apk", type=Path)
    p.add_argument("--key", type=Path, default=KEYS / "bunker-key.pem", help="RSA private key, PEM")
    p.add_argument("--cert", type=Path, default=KEYS / "bunker-cert.der", help="Certificate for the key, DER")
    args = p.parse_args()
    print(f"Signed {args.apk} (certificate SHA-256 {sign(args.apk, args.key, args.cert)})")


if __name__ == "__main__":
    main()
