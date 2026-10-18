#!/usr/bin/env python3
"""The Mod Menu parity check's own rules: catalog parsing, the hot-switch strip, the allowlist."""
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import check_menu_parity as parity  # noqa: E402

MAIN = '''jobjectArray GetFeatureList(JNIEnv *env, jobject context) {
    std::vector<std::string> feats;
    feats.push_back("Category_战斗功能");
    feats.push_back("1_SeekBar_伤害倍率_1_333");
    feats.push_back("2_SeekBar_防御倍率(讨伐战禁用)_1_333");
    feats.push_back("3_True_Toggle_角色技能无CD");
    CATEGORY_AND_HOT_SWITCH
    feats.push_back("19_Button_刷新自检");
    feats.push_back(std::string("17_RichTextView_自检基址: ") + (g_diagBase[0] ? g_diagBase : "等待游戏库…"));
    feats.push_back(std::string("18_RichTextView_自检挂钩: ") + (g_diagHook[0] ? g_diagHook : "等待游戏库…"));
    jobjectArray ret;
}'''

HOT_SWITCH = '''    feats.push_back("Category_服务器热切换");
    feats.push_back("7_InputText_服务器地址(IP/域名:端口)");
    feats.push_back("8_Button_保存到地址簿");
    feats.push_back("10_Spinner_地址簿_");
    feats.push_back("14_True_Toggle_失败自动切换");
    feats.push_back("16_RichTextView_");'''


def checkout(folder, hot_switch):
    source = Path(folder) / "en-client" / parity.CATALOG_FILE
    source.parent.mkdir(parents=True, exist_ok=True)
    source.write_text(MAIN.replace("CATEGORY_AND_HOT_SWITCH", HOT_SWITCH if hot_switch else ""), encoding="utf-8")
    return Path(folder)


class CatalogTest(unittest.TestCase):
    def test_reads_the_feature_entries_in_order(self):
        with tempfile.TemporaryDirectory() as work:
            repo = checkout(work, False)
            self.assertEqual(parity.catalog(repo, "en-client"), [
                "Category_战斗功能", "1_SeekBar_伤害倍率_1_333", "2_SeekBar_防御倍率(讨伐战禁用)_1_333",
                "3_True_Toggle_角色技能无CD", "19_Button_刷新自检",
                "17_RichTextView_自检基址: ", "18_RichTextView_自检挂钩: "])

    def test_removes_the_hot_switch_group_only(self):
        with tempfile.TemporaryDirectory() as work:
            device = parity.without_hot_switch(parity.catalog(checkout(f"{work}/device", False), "en-client"))
            upstream = parity.without_hot_switch(parity.catalog(checkout(f"{work}/upstream", True), "en-client"))
            self.assertEqual(device, upstream)

    def test_keeps_a_renamed_label_visible(self):
        with tempfile.TemporaryDirectory() as work:
            repo = checkout(work, False)
            source = repo / "en-client" / parity.CATALOG_FILE
            source.write_text(source.read_text(encoding="utf-8").replace("伤害倍率", "伤害倍率(倍)"), encoding="utf-8")
            self.assertNotEqual(parity.without_hot_switch(parity.catalog(repo, "en-client")),
                                parity.without_hot_switch(parity.catalog(checkout(f"{work}/other", True), "en-client")))

    def test_feature_numbers(self):
        self.assertEqual(parity.feature_number("7_InputText_x"), 7)
        self.assertEqual(parity.feature_number("Category_x"), None)
        self.assertEqual(parity.feature_number("17_RichTextView_ 自检"), 17)


class AllowTest(unittest.TestCase):
    def test_comments_and_blank_lines_are_ignored(self):
        with tempfile.TemporaryDirectory() as work:
            path = Path(work) / "allow"
            path.write_text("# a reason\n\nmodmenu/a.java   # why\nmodmenu/b.cpp\n", encoding="utf-8")
            self.assertEqual(sorted(parity.allow_list(path)), ["modmenu/a.java", "modmenu/b.cpp"])

    def test_missing_file_is_an_empty_list(self):
        self.assertEqual(parity.allow_list(Path("/nonexistent/allow")), {})


class TreeTest(unittest.TestCase):
    def test_skips_build_output_and_keeps_sources(self):
        with tempfile.TemporaryDirectory() as work:
            root = Path(work)
            (root / "app/build").mkdir(parents=True)
            (root / "app/build/out.class").write_text("x", encoding="utf-8")
            (root / "app/__pycache__").mkdir(parents=True)
            (root / "app/__pycache__/x.pyc").write_text("x", encoding="utf-8")
            (root / "app").mkdir(exist_ok=True)
            (root / "app/Menu.java").write_text("class Menu {}", encoding="utf-8")
            found = parity.tree(root)
            self.assertEqual(list(found), ["app/Menu.java"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
