#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""fix3_zh.py — fix3 内置串 + fix4 两态纯化 + 字体 payload 的纯文件变换（Pyodide 可执行）。

把 lunar-scripts-zh 的 fix3/fix4/字体阶段移植为 assemble/webbuild 可调用的纯函数：
stdlib-only，不依赖 UnityPy / apktool，手机浏览器（Pyodide）与桌面同一代码。

上游对照（步骤级替换，凡 lunar-scripts(-jp) 步骤均取 lunar-scripts-zh 对应物）：
  * 映射构建 —— 复用上游模块自身函数（jp fix3 repl_map / en key_map+meta_repl /
                ko key_map(含 KO_OVERRIDE) / fix3l FIX3L_KEYS），零口径漂移；
  * fix4 数据面 —— en-client 专有两态纯化数据（EN 段=原版英文、ko 段=中文；JP 仅 fix3）：
                EN 段 81 键还原值 = en-client/fix4_orig_en_values.json 复制；
                ko 段 67 nt 新译 = en-client/patch_fix4.py 内嵌 NT_KO_TRANSLATIONS 导出；
                调用点在 fix3l 之后（patch_fix4.py apply 4d/7 语义，纯文件变换）；
  * metadata  —— 复用上游 patch_metadata（stringLiteral 原地替换：len(new)<=len(old)、
                写新值 + 尾部 NUL 填充、回写 length 字段；纯 struct 实现，两边同源）；
  * TextAsset —— 本模块纯重写（上游用 UnityPy 重写 SerializedFile）：
                v21 单 TextAsset 布局 = m_Name + m_Script 两个 4 字节对齐串，
                重写对象数据并回写对象 byte_size / 文件 file_size，
                header 与 metadata 其余字节不动。
  * 字体 payload —— jp/en-client/fonts/payload/assets/bin/Data 四条目替换写入
                （sha 断言 = gate_defs.FONTS_ZH_{JP,EN} 单一事实源）。

文本行替换语义与上游 patch_textasset* 逐行同源：
  * JP（patch_fix3）：值级精确匹配（行 value == 原文才换）；
  * EN/ko/fix3l：键级替换（行 key 命中键名单才换）；ko 段与 fix3l-ko 段带
    len(new)<=len(old) 硬约束（T01 机制），超长 SKIP_TOO_LONG；
  * fix4-en（patch_fix4 EN 还原）：键级替换（EN 段 81 键 → 原版英文值，无长度约束）；
  * fix4-ko（patch_fix4 ko nt 翻译）：键级替换（nt(ko) 67 键 → 中文，≤原字节硬约束）。
    KO_OVERRIDE 2 条短译除外规则保持（fix3-ko 阶段既有口径，fix4 不触碰）。
"""
from __future__ import annotations

import importlib.util
import json
import struct
import sys
from pathlib import Path

META_ENTRY = "assets/bin/Data/Managed/Metadata/global-metadata.dat"
FONT_ENTRY_PREFIX = "assets/bin/Data/"

# TextAsset 载体（jp fix3 / en fix3 同口径）
JP_TS_ENTRIES = {
    "assets/bin/Data/35005335013ad4314b0ac8afbfe27b9c": "ui",
    "assets/bin/Data/5296ae89c03c14825a9f664b0c355ccc": "titleflow",
    "assets/bin/Data/ed79b6250ad8541b1ba6f2a229fcc9bf": "nt",
}
EN_TS = {
    "assets/bin/Data/a1e9ec10c664743ac927859dda597701": "ui(en)",
    "assets/bin/Data/6c88814b67ea44496a219083a723a1e5": "titleflow(en)",
    "assets/bin/Data/1dc4624c9ddde409fb4ffb1b0cb2faeb": "nt(en)",
}
KO_TS = {
    "assets/bin/Data/311a825b7b4ba4b7b854ee567c51d486": "ui(ko)",
    "assets/bin/Data/3286caf719be04314bd3208e16bc0e0e": "titleflow(ko)",
    "assets/bin/Data/d3f332a247d3c418d94d377ae81104c7": "nt(ko)",
}

FONT_ENTRIES = {
    "6f937efa0660c47f59d5215d276b1cbb": "UI RodinPro subset",
    "7089ac60979c94824ac549baab08cfa7": "STORY TalkingStd subset",
    "ad1489eb70ff840d19d7d0841bcdd3a9": "FOTK-YDHopeL subset",
    "550e0743a6b6344cfa3380b9a07f58b6": "FOTK-YDWingsM subset",
}

# fix4 数据面（en-client 专有，随站点 payload 发货；EN=fix4 态，JP=fix3 不动）：
#   fix4_orig_en_values.json     —— EN 段 81 键还原值（en-client/fix4_orig_en_values.json
#                                   复制，字节一致）
#   fix4_nt_ko_translations.json —— ko 段 67 nt 新译（en-client/patch_fix4.py 内嵌
#                                   NT_KO_TRANSLATIONS 表导出，逐键一致）
FIX4_DIR = Path(__file__).resolve().parent
FIX4_ORIG_EN_JSON = FIX4_DIR / "fix4_orig_en_values.json"
FIX4_NT_KO_JSON = FIX4_DIR / "fix4_nt_ko_translations.json"
# fix4-ko 载体（patch_fix4.py 仅译 nt(ko) 一张表）
FIX4_KO_NT_TS = {"assets/bin/Data/d3f332a247d3c418d94d377ae81104c7": "nt(ko)"}


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"[fix3_zh] cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


# ---------------------------------------------------------------- 上游映射面
def zh_root_of(bunker_root: Path) -> Path:
    """lunar-scripts-zh 挂载位（upstream/lunar-scripts-zh 目录联接）。"""
    zh = Path(bunker_root) / "upstream" / "lunar-scripts-zh"
    if not zh.is_dir():
        raise RuntimeError(f"[fix3_zh] lunar-scripts-zh mount missing: {zh}")
    return zh


def table_entries(zh: Path, tier: str = "all") -> list:
    """builtin_strings.json 权威表（tier 语义同上游 load_table）。"""
    table = zh / "jp-client" / "fix3" / "builtin_strings.json"
    data = json.loads(table.read_text(encoding="utf-8"))
    want = {"apply", "supplement"} if tier == "all" else {"apply"}
    return [e for e in data["entries"] if e["tier"] in want]


def upstream_maps(zh: Path, release: str) -> dict:
    """上游各补丁器自身的映射构建（纯函数，模块只定义常量与映射）。"""
    entries = table_entries(zh, "all")
    if release == "jp":
        jp = _load("fix3_zh_jp", zh / "jp-client" / "fix3" / "patch_fix3.py")
        return {"value_repl": jp.repl_map(entries),
                "meta_repl": jp.repl_map(entries),
                "ta": dict(JP_TS_ENTRIES),
                "patch_metadata": jp.patch_metadata}
    en = _load("fix3_zh_en", zh / "en-client" / "patch_fix3_en.py")
    ko = _load("fix3_zh_ko", zh / "en-client" / "patch_fix3_ko.py")
    l = _load("fix3_zh_l", zh / "en-client" / "patch_fix3l.py")
    return {"en_key": en.key_map(entries),
            "ko_key": ko.key_map(entries),
            "fix3l_en": {k: v["en"] for k, v in l.FIX3L_KEYS.items()},
            "fix3l_ko": {k: v["ko"] for k, v in l.FIX3L_KEYS.items()},
            "meta_repl": en.meta_repl(entries),
            "ta_en": dict(EN_TS), "ta_ko": dict(KO_TS),
            "patch_metadata": en.patch_metadata}


def fix4_maps() -> dict:
    """fix4 两态映射（纯 JSON 读取，Pyodide 可执行）。

    EN 段 81 键还原值来自 en-client/fix4_orig_en_values.json（本目录 = 站点发货复制，
    字节与 en-client 一致）；ko 段 NT_KO_TRANSLATIONS 67 条为 en-client/patch_fix4.py
    内嵌表导出的 JSON 数据文件（逐键一致）。返回
    {"fix4_orig_en": {key: 原版英文}, "fix4_ko_nt": {key: 中文译文}}。
    """
    for p in (FIX4_ORIG_EN_JSON, FIX4_NT_KO_JSON):
        if not p.is_file():
            raise RuntimeError(f"[fix3_zh] fix4 data file missing: {p}")
    orig_en = json.loads(FIX4_ORIG_EN_JSON.read_text(encoding="utf-8"))
    nt = json.loads(FIX4_NT_KO_JSON.read_text(encoding="utf-8"))
    return {"fix4_orig_en": orig_en,
            "fix4_ko_nt": {k: v["zh"] for k, v in nt.items()}}


# ---------------------------------------------------------------- TextAsset 纯重写
def _align4(n: int) -> int:
    return (n + 3) & ~3


def _read_aligned_str(buf: bytes, off: int):
    (ln,) = struct.unpack_from("<i", buf, off)
    off += 4
    raw = bytes(buf[off:off + ln])
    return raw, _align4(off + ln)


def _pack_aligned_str(raw: bytes) -> bytes:
    """4 字节对齐串（写入位为 4 对齐起点时与 Unity 对齐口径一致）。"""
    pad = (-len(raw)) % 4
    return struct.pack("<i", len(raw)) + raw + b"\x00" * pad


def _parse_sf(buf: bytes):
    """SerializedFile v21 最小解析：返回 (data_off, objects)。

    objects 每项: class_id / byte_start / byte_size / 三处回写偏移（start/size 字段位）。
    逐字节走完 metadata 并断言落在 20+metadata_size，布局不符即抛错（fail-fast）。
    """
    if len(buf) < 20:
        raise ValueError("[fix3_zh] SerializedFile too small")
    meta_size, file_size, version, data_off = struct.unpack_from(">IIII", buf, 0)
    if version != 21:
        raise ValueError(f"[fix3_zh] SerializedFile version {version} != 21")
    if file_size != len(buf):
        raise ValueError(f"[fix3_zh] file_size {file_size} != actual {len(buf)}")

    def u32(off):
        return struct.unpack_from("<I", buf, off)[0]

    off = 20
    off = buf.index(b"\x00", off) + 1                 # unity version
    off += 4 + 1                                      # target platform + enableTypeTree
    type_count = struct.unpack_from("<i", buf, off)[0]; off += 4
    classes = []
    for _ in range(type_count):
        class_id = struct.unpack_from("<i", buf, off)[0]; off += 4
        off += 1                                      # isStrippedType
        off += 2                                      # scriptTypeIndex
        if class_id < 0 or class_id == 114:
            off += 16                                 # script_id
        off += 16                                     # old_type_hash
        classes.append(class_id)
    obj_count = struct.unpack_from("<i", buf, off)[0]; off += 4
    objects = []
    for _ in range(obj_count):
        off = _align4(off)
        off += 8                                      # path_id (v>=14: int64)
        start_off = off
        byte_start = u32(off); off += 4
        size_off = off
        byte_size = u32(off); off += 4
        type_ix = struct.unpack_from("<i", buf, off)[0]; off += 4
        objects.append({"class_id": classes[type_ix], "byte_start": byte_start,
                        "byte_size": byte_size, "start_off": start_off,
                        "size_off": size_off})
    # script types (v>=11): count + (i32 + i64) each
    n = struct.unpack_from("<i", buf, off)[0]; off += 4
    off += 12 * n
    # externals (v>=6): count + (NUL str + guid16 + i32 + NUL str) each
    n = struct.unpack_from("<i", buf, off)[0]; off += 4
    for _ in range(n):
        off = buf.index(b"\x00", off) + 1
        off += 20
        off = buf.index(b"\x00", off) + 1
    # ref types (v>=20)
    n = struct.unpack_from("<i", buf, off)[0]; off += 4
    if n:
        raise ValueError("[fix3_zh] ref types present; layout not supported")
    off = buf.index(b"\x00", off) + 1                 # userInformation
    if off != 20 + meta_size:
        raise ValueError(f"[fix3_zh] metadata walk ended at {off}, expected {20 + meta_size}")
    return data_off, objects


def read_textassets(buf: bytes) -> list:
    """读出文件内全部 TextAsset 的 (m_Name, m_Script)。"""
    data_off, objects = _parse_sf(buf)
    out = []
    for obj in objects:
        if obj["class_id"] != 49:
            raise ValueError(f"[fix3_zh] object class {obj['class_id']} != TextAsset(49)")
        raw = buf[data_off + obj["byte_start"]: data_off + obj["byte_start"] + obj["byte_size"]]
        name_b, o2 = _read_aligned_str(raw, 0)
        script_b, o3 = _read_aligned_str(raw, o2)
        if o3 != obj["byte_size"]:
            raise ValueError(f"[fix3_zh] TextAsset layout mismatch: consumed {o3} of {obj['byte_size']}")
        out.append((name_b.decode("utf-8"), script_b.decode("utf-8")))
    return out


def patch_textasset(buf: bytes, transform) -> tuple:
    """纯重写 TextAsset：transform(m_Name, text) -> None | (new_text, log_rows)。

    对象数据重建后回写每个对象的 byte_start/byte_size 与文件 file_size；
    无任何改动时原样返回（保持原始字节，上游同语义）。
    """
    data_off, objects = _parse_sf(buf)
    meta = bytearray(buf[:data_off])
    data = bytearray()
    log = []
    changed_any = False
    for obj in objects:
        raw = buf[data_off + obj["byte_start"]: data_off + obj["byte_start"] + obj["byte_size"]]
        name_b, o2 = _read_aligned_str(raw, 0)
        script_b, o3 = _read_aligned_str(raw, o2)
        if o3 != obj["byte_size"]:
            raise ValueError(f"[fix3_zh] TextAsset layout mismatch: consumed {o3} of {obj['byte_size']}")
        result = transform(name_b.decode("utf-8"), script_b.decode("utf-8"))
        if result is None:
            new_raw, rows = raw, []
        else:
            new_text, rows = result
            new_raw = _pack_aligned_str(name_b) + _pack_aligned_str(new_text.encode("utf-8"))
            changed_any = True
        struct.pack_into("<I", meta, obj["start_off"], len(data))
        struct.pack_into("<I", meta, obj["size_off"], len(new_raw))
        log.append({"asset": name_b.decode("utf-8"), "changed": rows,
                    "changed_count": len(rows)})
        data += new_raw
    if not changed_any:
        return buf, log
    struct.pack_into(">I", meta, 4, data_off + len(data))
    return bytes(meta) + bytes(data), log


# ---------------------------------------------------------------- 行替换（上游同源）
def _edit_lines(text: str, matcher):
    """上游 patch_textasset 的行循环（matcher(key, value) -> (new_value, rows) | None）。"""
    trailing = text.endswith("\n")
    lines = text.split("\n")
    if trailing and lines and lines[-1] == "":
        lines = lines[:-1]
    changed = []
    for i, line in enumerate(lines):
        stripped = line.strip()
        if not stripped or stripped.startswith("//"):
            continue
        sep = line.find(":")
        if sep <= 0:
            continue
        key, value = line[:sep], line[sep + 1:]
        result = matcher(key, value)
        if result is None:
            continue
        new_value, rows = result
        if new_value != value:
            lines[i] = f"{key}:{new_value}"
            changed.append({"key": key, "old": value, "new": new_value, **rows})
    return "\n".join(lines) + ("\n" if trailing else ""), changed


def _matcher_value(repl: dict):
    """JP 口径：值级精确匹配（行 value == 原文才换）。"""
    def match(key, value):
        if value in repl and repl[value] != value:
            return repl[value], {}
        return None
    return match


def _ta_transform_lines(text, matcher):
    new_text, changed = _edit_lines(text, matcher)
    return (new_text, changed) if changed else None


def patch_ta_value(buf: bytes, repl: dict):
    """值级精确替换（JP fix3 口径）。"""
    def transform(name, text):
        return _ta_transform_lines(text, _matcher_value(repl))
    return patch_textasset(buf, transform)


def patch_ta_keyed(buf: bytes, kmap: dict, enforce_len: bool = False):
    """键级替换（EN/ko/fix3l 口径；enforce_len=ko 段 ≤原字节 硬约束，超长 SKIP_TOO_LONG）。"""
    skipped_all = []

    def match(key, value):
        if key not in kmap:
            return None
        new = kmap[key]
        if new == value:
            return None
        ob, nb = value.encode("utf-8"), new.encode("utf-8")
        if enforce_len and len(nb) > len(ob):
            skipped_all.append({"key": key, "old": value, "new": new,
                                "status": "SKIP_TOO_LONG",
                                "old_bytes": len(ob), "new_bytes": len(nb)})
            return None
        return new, {}

    def transform(name, text):
        return _ta_transform_lines(text, match)
    out, log = patch_textasset(buf, transform)
    for row in log:
        row["skipped"] = list(skipped_all)
    return out, log


# ---------------------------------------------------------------- 组装期入口
def ta_entries(release: str) -> dict:
    if release == "jp":
        return dict(JP_TS_ENTRIES)
    return {**EN_TS, **KO_TS}


def apply_fix3_workdir(release: str, work: Path, zh: Path) -> dict:
    """对解包目录就地打 fix3（metadata + TextAsset），与上游 apply --tier all 同序：

    私服补丁之后、字体之前（就地改保证已写入 metadata 的服务器地址不被覆盖）。
    work/META_ENTRY 与 work/<TA> 存在时逐个补丁；返回报告（含逐文件日志）。
    """
    work = Path(work)
    maps = upstream_maps(zh, release)
    report = {"release": release, "tier": "all", "files": {}}
    # 1) metadata（stringLiteral 原地替换，上游 patch_metadata 纯函数）
    mp = work / META_ENTRY
    if mp.is_file():
        raw = mp.read_bytes()
        out, mlog = maps["patch_metadata"](raw, maps["meta_repl"])
        report["files"][META_ENTRY] = {"changed": raw != out, "log": mlog}
        if raw != out:
            mp.write_bytes(out)
    else:
        report["files"][META_ENTRY] = {"missing": True}
        raise RuntimeError(f"[fix3_zh] {META_ENTRY} missing in work dir")
    # 2) TextAsset（jp=值级；en=fix3-EN 键级 + fix3-ko 键级(≤原字节) + fix3l 双段
    #    + fix4 两态纯化，调用点在 fix3l 之后）
    if release == "jp":
        stages = [("fix3", dict(JP_TS_ENTRIES), "value", maps["value_repl"], False)]
    else:
        maps.update(fix4_maps())
        stages = [("fix3-en", dict(EN_TS), "key", maps["en_key"], False),
                  ("fix3-ko", dict(KO_TS), "key", maps["ko_key"], True),
                  ("fix3l-en", dict(EN_TS), "key", maps["fix3l_en"], False),
                  ("fix3l-ko", dict(KO_TS), "key", maps["fix3l_ko"], True),
                  # fix4（patch_fix4.py apply 语义）：EN 段 81 键还原原版英文 +
                  # ko 段 nt 67 键新译=中文（≤原字节）；JP 无此阶段。
                  ("fix4-en", dict(EN_TS), "key", maps["fix4_orig_en"], False),
                  ("fix4-ko", dict(FIX4_KO_NT_TS), "key", maps["fix4_ko_nt"], True)]
    for stage, entries, mode, repl, enforce in stages:
        for entry, label in entries.items():
            p = work / entry
            if not p.is_file():
                report["files"][entry] = {"missing": True, "stage": stage}
                raise RuntimeError(f"[fix3_zh] {entry} missing in work dir")
            raw = p.read_bytes()
            if mode == "value":
                out, log = patch_ta_value(raw, repl)
            else:
                out, log = patch_ta_keyed(raw, repl, enforce_len=enforce)
            report["files"].setdefault(entry, {"stages": []})
            report["files"][entry]["stages"].append(
                {"stage": stage, "changed": raw != out,
                 "changed_count": sum(x["changed_count"] for x in log), "log": log})
            if raw != out:
                p.write_bytes(out)
    return report


def _meta_values(buf: bytes) -> list:
    """global-metadata stringLiteral 表项值列表（同上游 meta_entries 口径）。"""
    sl_off, sl_size = struct.unpack_from("<II", buf, 8)
    sld_off, _sld_size = struct.unpack_from("<II", buf, 16)
    out = []
    for i in range(sl_size // 8):
        e_off = sl_off + i * 8
        e_len, e_idx = struct.unpack_from("<II", buf, e_off)
        out.append(bytes(buf[sld_off + e_idx:sld_off + e_idx + e_len]))
    return out


def fix3_readback(release: str, read_entry) -> dict:
    """逐串回读：builtin_strings.json 为准，TA 键值 == target_zh、metadata 表项命中数达标。

    read_entry(entry_name) -> bytes（如 ZipFile.read）。返回 {ok, checked, ok_count, rows}。
    """
    zh = Path(__file__).resolve().parents[2] / "upstream" / "lunar-scripts-zh"
    if not zh.is_dir():
        raise RuntimeError(f"lunar-scripts-zh module not found at {zh}")
    entries = table_entries(zh, "all")
    rows = []
    ok_count = 0
    # TA 键值表（jp 一张全量面；en 以 EN 段为回读面）
    kv = {}
    tables = list(JP_TS_ENTRIES) if release == "jp" else list(EN_TS)
    for entry in tables:
        try:
            text = read_textassets(read_entry(entry))[0][1]
        except KeyError:
            continue
        for line in text.split("\n"):
            sep = line.find(":")
            if sep > 0:
                kv[line[:sep]] = line[sep + 1:]
    meta_values = _meta_values(read_entry(META_ENTRY))
    for e in entries:
        target = e.get("target_zh") or ""
        if not target:
            continue
        keys = [k for k in e.get("keys", []) if not k.startswith("metadata.")]
        hits = {k: kv.get(k) for k in keys}
        # S44-S46 为 metadata-only 条目（无 TA 键），TA 面不适用
        ta_ok = (not keys) or all(v == target for v in hits.values())
        want_meta = e.get("expected_metadata") or 0
        meta_hits = meta_values.count(target.encode("utf-8"))
        meta_ok = meta_hits >= want_meta
        ok = ta_ok and meta_ok
        ok_count += bool(ok)
        rows.append({"id": e["id"], "source_ja": e["source_ja"], "target_zh": target,
                     "keys": keys, "values": hits, "meta_hits": meta_hits,
                     "expected_metadata": want_meta, "ok": ok})
    total = len(rows)
    return {"release": release, "ok": ok_count == total and total > 0,
            "checked": total, "ok_count": ok_count, "rows": rows}


def _has_cjk(s: str) -> bool:
    return any("\u4e00" <= c <= "\u9fff" for c in s)


def _kv_of(read_entry, entries) -> dict:
    kv = {}
    for entry in entries:
        try:
            text = read_textassets(read_entry(entry))[0][1]
        except KeyError:
            continue
        for line in text.split("\n"):
            sep = line.find(":")
            if sep > 0:
                kv[line[:sep]] = line[sep + 1:]
    return kv


def fix4_readback(read_entry, zh: Path | None = None) -> dict:
    """fix4 两态回读（en 产物）：EN 段 81 键=原版英文 + ko 段 148 键值=中文 + metadata 7 值=中文
    + fix3 spot 串在 ko/metadata 承载（与 build_en_zh.verify_fix4_final_apk 同口径）。

    read_entry(entry_name) -> bytes（如 ZipFile.read）。返回
    {ok, en_restore, ko, ko_nt, metadata, spots}。
    """
    if zh is None:
        zh = Path(__file__).resolve().parents[2] / "upstream" / "lunar-scripts-zh"
        if not zh.is_dir():
            raise RuntimeError(f"lunar-scripts-zh module not found at {zh}")
    maps = upstream_maps(zh, "en")
    maps.update(fix4_maps())
    orig_en, nt_ko = maps["fix4_orig_en"], maps["fix4_ko_nt"]
    # ko 段 148 键 = fix3-ko(68) + fix3l-ko(13) + fix4 nt(67) 的键并集
    ko_expected = sorted(set(maps["ko_key"]) | set(maps["fix3l_ko"]) | set(nt_ko))
    res = {"release": "en"}

    # 1) EN 段：81 键 = 原版英文
    kv_en = _kv_of(read_entry, EN_TS)
    en_hits = {k: kv_en.get(k) for k in orig_en}
    en_bad = [k for k, v in en_hits.items() if v != orig_en[k]]
    res["en_restore"] = {"keys_expected": len(orig_en),
                         "keys_found": sum(1 for v in en_hits.values() if v is not None),
                         "match": len(orig_en) - len(en_bad), "bad": en_bad}

    # 2) ko 段：148 键值含中文；nt 67 键 = NT 新译精确值
    kv_ko = _kv_of(read_entry, KO_TS)
    per_table = {}
    for entry, label in KO_TS.items():
        try:
            text = read_textassets(read_entry(entry))[0][1]
        except KeyError:
            continue
        vals = [line.split(":", 1)[1] for line in text.split("\n")
                if line.strip() and not line.strip().startswith("//") and line.find(":") > 0]
        per_table[label] = {"values": len(vals),
                            "cjk": sum(1 for v in vals if _has_cjk(v))}
    ko_missing = [k for k in ko_expected if k not in kv_ko]
    ko_not_cjk = [k for k in ko_expected if k in kv_ko and not _has_cjk(kv_ko[k])]
    res["ko"] = {"keys_expected": len(ko_expected),
                 "keys_found": len(ko_expected) - len(ko_missing),
                 "cjk": sum(1 for k in ko_expected if k in kv_ko and _has_cjk(kv_ko[k])),
                 "per_table": per_table,
                 "missing": ko_missing, "not_cjk": ko_not_cjk}
    nt_bad = [k for k, zh_v in nt_ko.items() if kv_ko.get(k) != zh_v]
    res["ko_nt"] = {"keys_expected": len(nt_ko),
                    "keys_found": sum(1 for k in nt_ko if k in kv_ko),
                    "match": len(nt_ko) - len(nt_bad), "bad": nt_bad}

    # 3) metadata：7 值=中文（旧值残留 0；termofservice 条目不计）
    mrep = {}
    for e in table_entries(zh, "all"):
        if e.get("expected_metadata") and e.get("target_zh"):
            s = e["source_ja"]
            if s.startswith("titleflow.dialog.termofservice"):
                continue
            mrep[s] = e["target_zh"]
    meta_values = _meta_values(read_entry(META_ENTRY))
    meta_rows = {}
    for old, new in mrep.items():
        old_n = meta_values.count(old.encode("utf-8"))
        new_n = meta_values.count(new.encode("utf-8"))
        meta_rows[old] = {"new": new, "old_remaining": old_n, "new_hits": new_n,
                          "ok": old_n == 0 and new_n >= 1}
    res["metadata"] = {"expected": len(mrep),
                       "match": sum(1 for r in meta_rows.values() if r["ok"]),
                       "rows": meta_rows}

    # 4) fix3 spot 串在 ko/metadata 承载（EN 段已还原英文，spot 由 ko 段+metadata 承载）
    gate = _load("fix3_zh_gate_defs", zh / "shared" / "gate_defs.py")
    ko_meta = read_entry(META_ENTRY)
    for entry in KO_TS:
        ko_meta += read_entry(entry)
    spot_rows = {}
    for s in gate.FIX3_SPOTS:
        b = s.encode("utf-8")
        spot_rows[s] = {"ko_metadata_hits": ko_meta.count(b)}
    res["spots"] = spot_rows

    ok = (not res["en_restore"]["bad"] and res["en_restore"]["keys_found"] == len(orig_en)
          and not ko_missing and not ko_not_cjk
          and not nt_bad and res["ko_nt"]["keys_found"] == len(nt_ko)
          and res["metadata"]["match"] == len(mrep)
          and all(r["ko_metadata_hits"] >= 1 for r in spot_rows.values()))
    res["ok"] = ok
    return res


# ---------------------------------------------------------------- 字体 payload
def font_payload_entries(release: str, zh: Path) -> dict:
    """字体 payload 四条目 {apk 条目: payload 文件}，sha 断言 = gate_defs.FONTS_ZH_*。

    jp: upstream/lunar-scripts-zh/jp-client/fonts/payload/assets/bin/Data
    en: upstream/lunar-scripts-zh/en-client/fonts/payload/assets/bin/Data（同名四条目，
        EN=Hangul 版 payload3；sha 与 jp 不同，按客户端断言）。
    """
    gate = _load("fix3_zh_gate_defs", zh / "shared" / "gate_defs.py")
    expect = gate.CLIENTS[release]["fonts_zh"]
    payload = zh / f"{release}-client" / "fonts" / "payload" / "assets" / "bin" / "Data"
    if not payload.is_dir():
        raise RuntimeError(f"[fix3_zh] font payload missing: {payload}")
    out = {}
    for name in gate.FONT_NAMES:
        f = payload / name
        if not f.is_file():
            raise RuntimeError(f"[fix3_zh] font payload lacks {name}")
        digest = gate.sha256_file(f)
        if digest != expect[name]:
            raise RuntimeError(f"[fix3_zh] font payload sha mismatch for {name}: "
                               f"{digest[:16]}… != {expect[name][:16]}…")
        out[FONT_ENTRY_PREFIX + name] = f
    return out
