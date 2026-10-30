#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""verify_gate_zh.py — L6 bunker 侧验证门（setup 预检 + 产物验证门，fail-fast）。

断言定义/期望值/报告口径 = lunar-scripts-zh/shared/gate_defs.py（单一事实源），
检查过程 = lunar-scripts-zh/shared/verify_gate.py（统一执行器）。本模块只做
bunker 侧接线：挂载位装载（upstream/lunar-scripts-zh 目录联接）、setup 预检
（MANIFEST + 字体 payload）、产物门（按产物类取断言强度），并以 fail-fast
抛 ValueError 供 prepare.py / assemble_apk.py / webbuild.py 链路消费。

产物类（product_class）：
  deliverable — zh 交付物（nier-jp.apk / nier-en.apk / 集成 bin.e）：
                字体=zh payload、fix3 必需、bin.e 文本须带简体强度。
  bunker      — bunker 链路自产（原版 APK+原版 master 改版产物）：
                字体=四条目完整性（zh 或原版皆可，报 which）、fix3 optional、
                bin.e 文本 CJK-only（该链路 webbuild.verify 强制原版 master，
                文本为原版日文；zh 强度断言在 deliverable 类启用）。
  pre-sign    — assemble_apk 产出（未签名）：同 bunker 但证书断言 skip。

用法：
  python verify_gate_zh.py setup
  python verify_gate_zh.py product --apk out.apk [--bin-e m.bin.e] \\
      [--client jp|en] [--class deliverable|bunker|pre-sign] [--out-json r.json]
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
import zipfile
from pathlib import Path

BUNKER_ROOT = Path(__file__).resolve().parents[2]          # E:\NieRReincarnation\bunker
REPO_ROOT = BUNKER_ROOT.parent                             # E:\NieRReincarnation
ZH_MOUNT = BUNKER_ROOT / "upstream" / "lunar-scripts-zh"
MASTER_ENTRY = "assets/lunar/20240404193219.bin.e"


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ValueError(f"[verify_gate_zh] 无法装载 {path}")
    module = importlib.util.module_from_spec(spec)
    # dataclass（py3.14）按 cls.__module__ 查 sys.modules；exec 前先登记
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def zh_mount() -> Path:
    """lunar-scripts-zh 挂载位（upstream/lunar-scripts-zh 目录联接）。"""
    if not ZH_MOUNT.is_dir():
        raise ValueError(
            f"[verify_gate_zh] lunar-scripts-zh 挂载位缺失: {ZH_MOUNT}\n"
            f"- 建修复: New-Item -ItemType Junction -Path '{ZH_MOUNT}' "
            f"-Target '<lunar-scripts-zh 实际路径>'")
    return ZH_MOUNT


def load_gate_modules():
    zh = zh_mount()
    shared = zh / "shared"
    gate_defs = _load("l6_gate_defs", shared / "gate_defs.py")
    # verify_gate 自身 import gate_defs/detect_client 依赖 shared 在 sys.path
    if str(shared) not in sys.path:
        sys.path.insert(0, str(shared))
    verify_gate = _load("l6_verify_gate", shared / "verify_gate.py")
    return gate_defs, verify_gate


# ---------------------------------------------------------------- setup 预检
def setup_gate(raise_on_fail: bool = True):
    """setup 期预检（prepare.py 装载 lunar-scripts-zh 后调用）：
    ① MANIFEST 预检（jp-client / en-client 权威副本逐项 sha256）；
    ② 字体 payload 四条目在位且 sha256 == 期望（jp=模块内 payload2；
       en=payload3 在 zh-l10n/work/fonts-fix4/out3（模块外，可达则检））。"""
    gate_defs, verify_gate = load_gate_modules()
    G = gate_defs
    rep = G.GateReport(gate="bunker-setup", target={"zh_mount": str(ZH_MOUNT)})

    for client in ("jp", "en"):
        cdir = ZH_MOUNT / f"{client}-client"
        s, d, det = verify_gate.check_manifest_precheck(cdir)
        rep.add("manifest_precheck", s, f"[{client}] {d}", actual=det)

    payload_dirs = {
        "jp": ZH_MOUNT / "jp-client" / "fonts" / "payload" / "assets" / "bin" / "Data",
        "en": REPO_ROOT / "zh-l10n" / "work" / "fonts-fix4" / "out3" / "payload3"
              / "assets" / "bin" / "Data",
    }
    for client, pdir in payload_dirs.items():
        expect = G.CLIENTS[client]["fonts_zh"]
        if not pdir.is_dir():
            # en payload 在模块外（构建工作区）；不在则明确 skip，不算 fail
            rep.add("font_payload", "skip",
                    f"[{client}] payload 目录不可达（模块外构建工作区）: {pdir}", None)
            continue
        bad = []
        got = {}
        for name in G.FONT_NAMES:
            f = pdir / name
            if not f.is_file():
                bad.append(f"缺 {name[:8]}")
                continue
            h = G.sha256_file(f)
            got[name] = h
            if h != expect[name]:
                bad.append(f"{name[:8]} sha 不符: {h[:16]}…")
        detail = {"dir": str(pdir), "entries": {k[:8]: v[:16] for k, v in got.items()}}
        if bad:
            rep.add("font_payload", "fail",
                    f"[{client}] 字体 payload 四条目: {'; '.join(bad)}", actual=detail)
        else:
            rep.add("font_payload", "pass",
                    f"[{client}] 字体 payload 四条目 OK（{pdir}）", actual=detail)

    for line in rep.render_lines():
        print(line, flush=True)
    if not rep.ok and raise_on_fail:
        raise ValueError(f"[verify_gate_zh] setup 预检失败（fail-fast）: "
                         f"{rep.to_dict()['summary']}")
    return rep


# ---------------------------------------------------------------- 产物门
def _embedded_bin_e(apk: Path, dest: Path) -> Path | None:
    with zipfile.ZipFile(apk) as zf:
        if MASTER_ENTRY in zf.namelist():
            dest.write_bytes(zf.read(MASTER_ENTRY))
            return dest
    return None


def product_gate(apk: Path | None = None, bin_e: Path | None = None,
                 client: str | None = None,
                 product_class: str = "bunker", expect_bin_e_name: str | None = None,
                 sidecar: Path | None = None, out_json: Path | None = None,
                 raise_on_fail: bool = True):
    """产物验证门（assemble_apk.py / webbuild.py 链路 / 自测共用）。

    按 product_class 取断言强度（见模块 docstring）。产物只读；缺省从产物内
    抽 assets/lunar/20240404193219.bin.e 到临时文件做 A3/A5。fail-fast 抛
    ValueError。"""
    gate_defs, verify_gate = load_gate_modules()
    apk = Path(apk) if apk is not None else None
    import tempfile
    tmpdir = Path(tempfile.mkdtemp(prefix="l6-gate-"))
    try:
        if bin_e is None and apk is not None:
            # 保留条目原名：A3 文件名不变量按产物内条目名判定
            bin_e = _embedded_bin_e(apk, tmpdir / Path(MASTER_ENTRY).name)
        if product_class == "deliverable":
            font_mode, fix3_mode, require_zh = "zh", "required", True
        else:
            font_mode, fix3_mode, require_zh = "known", "optional", False
        if expect_bin_e_name is None and bin_e is not None:
            # 不变量：产物内 master 名不变（20240404193219.bin.e）；
            # 交付物独立 bin.e（如 bin_zh_fix6.bin.e）走 CLI --expect-bin-e-name。
            expect_bin_e_name = "20240404193219.bin.e"
            if product_class == "deliverable" and bin_e.name != expect_bin_e_name:
                expect_bin_e_name = bin_e.name
        rep = verify_gate.run_gate(
            apk=apk, bin_e=bin_e, client=client,
            expect_bin_e_name=expect_bin_e_name, sidecar=sidecar,
            manifest_dir=None, font_mode=font_mode, fix3_mode=fix3_mode,
            require_zh_text=require_zh,
            gate_name=f"bunker-product[{product_class}]")
        if product_class == "pre-sign":
            for c in rep.checks:
                if c["id"] == "cert_assertion":
                    c["status"] = "skip"
                    c["detail"] = "产物未签名；证书断言在签名后门（webbuild）执行"
    finally:
        for f in tmpdir.glob("*"):
            try:
                f.unlink()
            except OSError:
                pass
    for line in rep.render_lines():
        print(line, flush=True)
    if out_json:
        rep.write_json(Path(out_json))
    if not rep.ok and raise_on_fail:
        raise ValueError(f"[verify_gate_zh] 产物验证门失败（fail-fast）: "
                         f"{apk} class={product_class} {rep.to_dict()['summary']}")
    return rep


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description="L6 bunker 侧验证门")
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("setup", help="setup 预检（MANIFEST + 字体 payload）")
    pr = sub.add_parser("product", help="产物验证门")
    pr.add_argument("--apk", type=Path, default=None)
    pr.add_argument("--bin-e", type=Path, default=None)
    pr.add_argument("--client", choices=("jp", "en"), default=None)
    pr.add_argument("--class", dest="pclass", default="deliverable",
                    choices=("deliverable", "bunker", "pre-sign"))
    pr.add_argument("--expect-bin-e-name", default=None)
    pr.add_argument("--sidecar", type=Path, default=None)
    pr.add_argument("--out-json", type=Path, default=None)
    args = p.parse_args(argv)
    if args.cmd == "setup":
        setup_gate(raise_on_fail=True)
        return 0
    product_gate(args.apk, bin_e=args.bin_e, client=args.client,
                 product_class=args.pclass,
                 expect_bin_e_name=args.expect_bin_e_name,
                 sidecar=args.sidecar, out_json=args.out_json,
                 raise_on_fail=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
