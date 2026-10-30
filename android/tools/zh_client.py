#!/usr/bin/env python3
"""bunker ↔ lunar-scripts-zh 客户端自动分派与一致性校验。

调用链上接入 `upstream/lunar-scripts-zh/shared/detect_client.py`——识别 →
选 jp-client/en-client（补丁器 / 签名 key / 产物名），未知客户端 fail-fast
（无默认分支）；与 bunker 自家 region.py 识别做**一致性校验**：两处判定必须
一致，不一致即拒（SystemExit）。

分派档案（dispatch() 返回）：

| 字段 | 含义 |
|---|---|
| region / package / name | 判定结果（= region.py 口径） |
| product_name | 产物名契约：jp→nier-jp.apk，en→nier-en.apk |
| patcher / patcher_path | REGIONS 补丁器（zh 双前端补丁器） |
| keystore / key_alias / key_pass / cert_sha256 | 签名 key 自动选 |
| zh | detect_client 判定档案全文（manifest sidecar 的 region_info 输入） |

用法：
    from zh_client import dispatch
    profile = dispatch(apk)                  # 严格模式（三元组硬断言）
    profile = dispatch(apk, strict=False)    # 仅 webbuild --skip-checks 覆盖用：
                                             # 跳过三元组断言（拆分包场景），但
                                             # 包名级判定一致性仍强制。
"""
from __future__ import annotations

import importlib.util
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
ZH_MOUNT = ROOT / "upstream/lunar-scripts-zh"

sys.path.insert(0, str(Path(__file__).resolve().parent))
import region  # noqa: E402


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def zh_root() -> Path:
    """lunar-scripts-zh 挂载位（upstream/lunar-scripts-zh 目录联接）。"""
    if not ZH_MOUNT.is_dir():
        raise SystemExit(
            f"[zh_client] lunar-scripts-zh 挂载位缺失: {ZH_MOUNT}\n"
            f"  重建目录联接（Windows）: New-Item -ItemType Junction "
            f"-Path '{ZH_MOUNT}' -Target '<lunar-scripts-zh 实际路径>'\n"
            f"  （见 .gitmodules upstream-local 登记 / upstream.lock.json kind=directory 条目）")
    return ZH_MOUNT


def detect_module():
    return _load("zh_detect_client", zh_root() / "shared/detect_client.py")


def product_name_for(region_key: str) -> str:
    """产物名契约（§9.1）：jp→nier-jp.apk，en→nier-en.apk；未知 fail-fast。"""
    info = region.REGIONS.get(region_key)
    if info is None:
        raise SystemExit(f"[zh_client] 未知 region（无默认分支）: {region_key!r}")
    return info["product"]


def key_for(region_key: str) -> dict:
    """签名 key 自动选（§8.2）：jp→nier-jp.keystore，en→nier-en.keystore。"""
    info = region.REGIONS.get(region_key)
    if info is None:
        raise SystemExit(f"[zh_client] 未知 region（无默认分支）: {region_key!r}")
    key = zh_root() / info["keystore"]
    if not key.is_file():
        raise SystemExit(f"[zh_client] {region_key} 签名 key 缺失: {key}")
    return {
        "region": region_key,
        "keystore": key,
        "alias": info["key_alias"],
        "pass": info["key_pass"],
        "cert_sha256": info["cert_sha256"],
    }


def dispatch(apk, expect: str | None = None, strict: bool = True) -> dict:
    """识别 + 一致性校验 + 分派档案（fail-fast，无默认分支）。

    1. bunker region.region_of_apk() 判定（包名）；
    2. zh detect_client 判定（strict=True：包名 + 三元组硬断言；strict=False：
       仅包名——仅供 webbuild 的 --skip-checks 拆分包覆盖，日志留痕）；
    3. 一致性校验：两处 region/包名判定必须一致，不一致即 SystemExit；
    4. expect 契约断言：--region 显式指定时矛盾即拒（§3.2）。
    """
    apk = Path(apk)
    region_key, package = region.region_of_apk(apk)
    if expect not in (None, "", "auto") and region_key != expect:
        raise SystemExit(
            f"[zh_client] --region {expect} 与识别结果 {region_key} 矛盾即拒（{apk}）")

    dc = detect_module()
    if strict:
        info = dc.detect_client(apk, expect=region_key)
    else:
        pkg = dc.apk_package_name(apk)
        matched = [r for r, v in dc.REGIONS.items() if v["package"] == pkg]
        if not matched:
            raise SystemExit(
                f"[zh_client] 未知客户端（包名不在 zh REGIONS）: {pkg!r}（{apk}）")
        info = dict(dc.REGIONS[matched[0]])
        info["detected"] = {"path": str(apk.resolve()), "package": pkg,
                            "bytes": apk.stat().st_size, "sha256": None,
                            "triple_ok": False}
        info["keystore_path"] = str((zh_root() / info["keystore"]).resolve())
        info["patch_set_paths"] = [str((zh_root() / p).resolve()) for p in info["patch_set"]]

    # 一致性校验：两处判定必须一致，不一致即拒。
    if info.get("region") != region_key or info.get("package") != package:
        raise SystemExit(
            f"[zh_client] 判定不一致即拒：bunker region.py = {region_key!r}/{package!r}"
            f"，zh detect_client = {info.get('region')!r}/{info.get('package')!r}（{apk}）")
    # 事实表交叉核对（REGIONS 双表同源；漂移即拒）。
    mine, theirs = region.REGIONS[region_key], info
    for field, key in (("package", "package"), ("size", "bytes"), ("sha256", "sha256"),
                       ("libil2cpp_size", "libil2cpp_size"),
                       ("product", "product_name"), ("cert_sha256", "cert_sha256"),
                       ("keystore", "keystore"), ("key_alias", "ks_alias"),
                       ("key_pass", "ks_pass")):
        if mine.get(field) != theirs.get(key):
            raise SystemExit(
                f"[zh_client] REGIONS 事实表不一致即拒（{region_key}.{field}）："
                f"bunker={mine.get(field)!r} zh={theirs.get(key)!r}")
    # 补丁器挂载点必须指向 zh 双前端（§1.7.2 #1/#2 语义断言）。
    expected_suffix = {"jp": "jp-client/patches/patch_apk_jp.py",
                       "en": "en-client/patches/patch_apk_en.py"}[region_key]
    if not mine["patcher"].endswith(expected_suffix):
        raise SystemExit(
            f"[zh_client] REGIONS patcher 未改道 lunar-scripts-zh：{mine['patcher']!r}")
    if not (ROOT / mine["patcher"]).is_file():
        raise SystemExit(f"[zh_client] 补丁器缺失: {ROOT / mine['patcher']}")

    return {
        "region": region_key,
        "package": package,
        "name": mine["name"],
        "product_name": mine["product"],
        "patcher": mine["patcher"],
        "patcher_path": (ROOT / mine["patcher"]).resolve(),
        "keystore": (zh_root() / mine["keystore"]).resolve(),
        "key_alias": mine["key_alias"],
        "key_pass": mine["key_pass"],
        "cert_sha256": mine["cert_sha256"],
        "strict": strict,
        "zh": info,
    }


def write_manifest_sidecar(product_apk, profile: dict, **kwargs):
    """产物 manifest sidecar（§9.1）：`<产物名>.manifest.json` 随产物落盘。"""
    sidecar_mod = _load("zh_manifest_sidecar", zh_root() / "shared/manifest_sidecar.py")
    sidecar = sidecar_mod.build_sidecar(Path(product_apk), region_info=profile["zh"], **kwargs)
    return sidecar_mod.write_sidecar(Path(product_apk), sidecar)
