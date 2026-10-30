#!/usr/bin/env python3
"""patch_masterdata.py 的薄适配层 → lunar-scripts-zh jp-client/build_bin_e.py。

BUNKER-ADAPT-PLAN §1.7.2 #4/#7：`scripts/build.py` 与 `android/tools/assemble_apk.py`
对原版 `lunar-scripts/patch_masterdata.py`（--input/--output 契约）的调用改道到
`upstream/lunar-scripts-zh/jp-client/build_bin_e.py`。build_bin_e 参数面不同，故在
bunker 侧 tools/ 放本薄适配层（**不改 build_bin_e 语义**）：

| 旧契约（patch_masterdata.py） | 新契约（build_bin_e.py） | 适配 |
|---|---|---|
| `--input X` | `--bin-e X` | 直译 |
| `--output Y` | `--out-bin-e Y` | 直译 + 文件名不变量暂存 |
| `--dry-run` | `--dry-run` | 直译 |
| `--key/--iv/--key-file/--iv-file` | （无；内置 KEY/IV） | 仅接受与内置 KEY/IV 相等的值，否则拒 |
| （无） | `--bin-edit/--report` | 透传（可选扩展）；`--text-from/--zh-base/--orig-bin-e` 留给 zh 成对流水线 |

两处语义差的处置：
1. **文件名不变量**：build_bin_e 强制「输出名==输入名」（§9.2 硬性规则），旧 CLI 不
   强制（assemble_apk.patch_master 用 in.bin.e→out.bin.e）。适配层内部以输出基名
   暂存输入副本再交 build_bin_e，产出字节不变（bin.e 内容与文件名无关），最后落到
   调用方指定的 --output 路径——旧 CLI 行为保持，build_bin_e 不变量亦保持。
2. **编辑面**：build_bin_e 缺省 = 全量编辑面（DEFAULT_EDITS），即原版
   patch_masterdata.py 的编辑面（见 bin-edit.default.json 注释）；调用方可传
   --bin-edit 收窄/切换。

用法（与旧 CLI 逐字兼容）：
    python patch_masterdata_zh.py --input original.bin.e --output patched.bin.e
"""
from __future__ import annotations

import argparse
import importlib.util
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ZH_BUILD_BIN_E = ROOT / "upstream/lunar-scripts-zh/jp-client/build_bin_e.py"
ZH_BIN_EDIT_DEFAULT = ROOT / "upstream/lunar-scripts-zh/jp-client/bin-edit.default.json"

# 内置 AES key/IV（= build_bin_e.KEY/IV = 旧 patch_masterdata DEFAULT_KEY/IV）。
BUILTIN_KEY_HEX = "36436230313332314545356536624265"
BUILTIN_IV_HEX = "45666341656634434165356536446141"


def _load_build_bin_e():
    if not ZH_BUILD_BIN_E.is_file():
        raise SystemExit(
            f"[patch_masterdata_zh] lunar-scripts-zh 挂载位缺失或 build_bin_e.py 不在: "
            f"{ZH_BUILD_BIN_E}（见 .gitmodules upstream-local 登记）")
    spec = importlib.util.spec_from_file_location("zh_build_bin_e", ZH_BUILD_BIN_E)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _check_key_iv(args):
    """旧契约的 key/IV 覆盖面：只接受与 build_bin_e 内置值相等的值（语义不改）。"""
    if args.key is not None and args.key.lower() != BUILTIN_KEY_HEX:
        raise SystemExit("[patch_masterdata_zh] build_bin_e 语义不改：--key 仅接受内置 key"
                         f"（{BUILTIN_KEY_HEX}）；自定义 key 不支持。")
    if args.iv is not None and args.iv.lower() != BUILTIN_IV_HEX:
        raise SystemExit("[patch_masterdata_zh] build_bin_e 语义不改：--iv 仅接受内置 IV"
                         f"（{BUILTIN_IV_HEX}）；自定义 IV 不支持。")
    if args.key_file is not None:
        if Path(args.key_file).read_bytes().hex().lower() != BUILTIN_KEY_HEX:
            raise SystemExit("[patch_masterdata_zh] --key-file 与内置 key 不一致；拒绝。")
    if args.iv_file is not None:
        if Path(args.iv_file).read_bytes().hex().lower() != BUILTIN_IV_HEX:
            raise SystemExit("[patch_masterdata_zh] --iv-file 与内置 IV 不一致；拒绝。")


def patch_file(input_path, output_path, *, bin_edit=None, report=None, dry_run=False):
    """旧 --input/--output 契约 → build_bin_e()；返回 build_bin_e 的报告 dict。"""
    src, dst = Path(input_path), Path(output_path)
    if not src.is_file():
        raise SystemExit(f"[patch_masterdata_zh] 输入不存在: {src}")
    mod = _load_build_bin_e()
    if bin_edit is None and ZH_BIN_EDIT_DEFAULT.is_file():
        bin_edit = ZH_BIN_EDIT_DEFAULT  # 缺省 = 全量编辑面（与旧 patch_masterdata 等价）
    if not dry_run:
        dst.parent.mkdir(parents=True, exist_ok=True)
    # 文件名不变量暂存：内部两侧同名（=输出基名）交给 build_bin_e，
    # 其 SystemExit 断言语义原样透传（--dry-run 也走同一路径，不变量同检）。
    with tempfile.TemporaryDirectory(prefix="patch-master-") as temp:
        stage = Path(temp)
        staged_in = stage / "in" / dst.name
        staged_out = stage / "out" / dst.name
        staged_in.parent.mkdir(parents=True)
        shutil.copy2(src, staged_in)
        result = mod.build_bin_e(bin_e=staged_in, out_bin_e=staged_out,
                                 bin_edit=bin_edit, report_path=report, dry_run=dry_run)
        if not dry_run:
            shutil.copy2(staged_out, dst)
    return result


def patch_bytes(original: bytes) -> bytes:
    """In-memory 形态（assemble_apk.patch_master 的旧契约）。"""
    with tempfile.TemporaryDirectory(prefix="patch-master-") as temp:
        source, target = Path(temp) / "in.bin.e", Path(temp) / "out.bin.e"
        source.write_bytes(original)
        patch_file(source, target)
        return target.read_bytes()


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Patch master data (thin adapter over lunar-scripts-zh jp-client/build_bin_e.py)")
    parser.add_argument("--input", required=True, help="Input bin.e (original; read-only)")
    parser.add_argument("--output", required=True, help="Output bin.e (filename may differ; "
                        "the build_bin_e filename invariant is honored internally)")
    parser.add_argument("--key", default=None, help="(compat) hex key; only the built-in value")
    parser.add_argument("--key-file", default=None, help="(compat) raw key file; only the built-in key")
    parser.add_argument("--iv", default=None, help="(compat) hex IV; only the built-in value")
    parser.add_argument("--iv-file", default=None, help="(compat) raw IV file; only the built-in IV")
    parser.add_argument("--bin-edit", default=None,
                        help="Edit config JSON (default: zh jp-client/bin-edit.default.json = "
                             "the original patch_masterdata full edit surface)")
    parser.add_argument("--report", default=None, help="JSON report output path")
    parser.add_argument("--dry-run", action="store_true", help="Report only; write nothing")
    args = parser.parse_args()
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:  # noqa: BLE001
            pass
    _check_key_iv(args)
    patch_file(args.input, args.output, bin_edit=args.bin_edit,
               report=args.report, dry_run=args.dry_run)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
