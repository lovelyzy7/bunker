/* 档案馆中文（默认中文，右下角 中文/EN 切换）。
 *
 * 模板以英文撰写；这里按「英文原文 → 中文」翻译文本与属性，切换时还原原文。
 * 游戏内容（角色名、服装名、剧情台词、曲名等）不在词典里，因此保持原样。
 */
(function () {
  "use strict";
  var ZH = {
    "Archive": "档案馆",
    "Archives": "档案",
    "Battle motions ·": "战斗动作 ·",
    "Building the archive index": "正在构建档案索引",
    "Characters": "角色",
    "Close": "关闭",
    "Companions": "随从",
    "Costume story": "服装故事",
    "Costumes": "服装",
    "Debris": "碎片",
    "Done": "完成",
    "End of transmission // Glory to mankind": "通信结束 // 愿人类荣光永存",
    "Events": "活动",
    "Files read": "已读取文件",
    "First 60 matches.": "前 60 条匹配。",
    "Gallery": "画廊",
    "Gallery ·": "画廊 ·",
    "Home": "首页",
    "Library": "文库",
    "Loop": "循环",
    "Main": "主线",
    "Memoirs": "回忆",
    "Motion": "动作",
    "Movies": "影片",
    "Music": "音乐",
    "Next ›": "下一页 ›",
    "No lines found": "没有找到台词",
    "No records found": "没有找到记录",
    "No scenes": "没有场景",
    "Nothing for sale.": "没有可购买的内容。",
    "Nothing here.": "这里什么都没有。",
    "Operator link // Standing by": "操作员链路 // 待命",
    "Part Play": "部件播放",
    "Preparing the model…": "正在准备模型…",
    "Records": "记录",
    "Records ·": "记录 ·",
    "Reports": "报告",
    "Rest pose": "静止姿势",
    "Save PNG": "保存 PNG",
    "Scene": "场景",
    "Scenes": "场景",
    "Schedule": "日程",
    "Season": "赛季",
    "Seasons": "赛季",
    "Shards": "碎片",
    "Shops": "商店",
    "Side": "支线",
    "Soundtrack": "原声",
    "Step": "步骤",
    "Story": "剧情",
    "Story lines ·": "剧情台词 ·",
    "Summons": "召唤",
    "The archive could not be built": "无法构建档案",
    "The live service's own dates, in UTC. Some rows carry a placeholder date in 2099 instead of their real dates; they are listed under \"No date in the game data\" with what the game files show about them.": "线上服务当时的日期（UTC）。部分条目以 2099 年的占位日期代替真实日期；这些条目列在「游戏数据中没有日期」下，并附上游戏文件中的信息。",
    "This scene has no text.": "此场景没有文本。",
    "Track": "曲目",
    "Try again": "重试",
    "View in 3D": "3D 查看",
    "Voice": "语音",
    "Weapons": "武器",
    "and": "与",
    "costume": "套服装",
    "costumes · companions · cast · enemies": "服装 · 随从 · 演员 · 敌人",
    "image": "图片",
    "main story · character stories · events · side stories · library": "主线 · 角色故事 · 活动 · 支线 · 文库",
    "main · season · chapter ·": "主线 · 赛季 · 章节 ·",
    "of": "／",
    "soundtrack": "原声带",
    "stills · event scenes · library art · photos": "剧照 · 活动场景 · 文库插画 · 照片",
    "summons · events · shops · banners · campaigns, with their dates": "召唤 · 活动 · 商店 · 卡池 · 战役，含各自时间",
    "voiced line": "语音台词",
    "weapon stories · reports · lost archives · memoirs · debris": "武器故事 · 报告 · 失落档案 · 回忆 · 碎片",
    "‹ Back": "‹ 返回",
    "‹ Prev": "‹ 上一页",
    "‹ Scenes": "‹ 场景",
    "› Characters": "› 角色",
    "› Gallery": "› 画廊",
    "› Movies": "› 影片",
    "› Music": "› 音乐",
    "› Records": "› 记录",
    "› Schedule": "› 日程",
    "› Story": "› 剧情",
    "▶ Play scene": "▶ 播放场景",
  };
  var PATTERNS = [
    ["^(\\d+) costumes?$", "{1} 套服装"],
    ["^(\\d+) weapons?$", "{1} 把武器"],
    ["^(\\d+) companions?$", "{1} 名随从"],
    ["^(\\d+) memoirs?$", "{1} 套回忆"],
    ["^(\\d+) records?$", "{1} 条记录"],
    ["^(\\d+) movies?$", "{1} 部影片"],
    ["^(\\d+) tracks?$", "{1} 首曲目"],
    ["^(\\d+) scenes?$", "{1} 个场景"],
    ["^(\\d+) characters?$", "{1} 名角色"],
    ["^Story lines · Season (\\d+)$", "剧情台词 · 赛季 {1}"],
    ["^(.*) · Season (\\d+)$", "{1} · 赛季 {2}"],
    ["^(.*) · Season (\\d+) · (.*)$", "{1} · 赛季 {2} · {3}"],
    ["^Season (\\d+)$", "赛季 {1}"],
    ["^(\\d+) of (\\d+)$", "{1} / {2}"],
  ];
  var KEY = "archive_lang";
  var SKIP = {SCRIPT: 1, STYLE: 1, PRE: 1, CODE: 1, TEXTAREA: 1, SELECT: 1};
  var ATTRS = ["placeholder", "title", "aria-label", "alt"];
  var originals = [];
  var attrOriginals = new WeakMap();

  function stored() { try { return localStorage.getItem(KEY); } catch (e) { return null; } }
  if (stored() === null) { try { localStorage.setItem(KEY, "zh"); } catch (e) {} }
  function lang() { return stored() === "en" ? "en" : "zh"; }
  function norm(s) { return String(s).replace(/\s+/g, " ").trim(); }

  function zhText(text) {
    if (ZH[text] !== undefined) return ZH[text];
    for (var i = 0; i < PATTERNS.length; i++) {
      var m = text.match(PATTERNS[i][0]);
      if (!m) continue;
      return PATTERNS[i][1].replace(/\{(\d)\}/g, function (_, n) {
        return m[Number(n)] !== undefined ? m[Number(n)] : "";
      });
    }
    return null;
  }

  function apply() {
    originals.forEach(function (item) {
      if (item.node) item.node.nodeValue = item.original;
      else {
        var saved = attrOriginals.get(item.el);
        if (saved && saved[item.attr] !== undefined) item.el.setAttribute(item.attr, saved[item.attr]);
      }
    });
    originals = [];
    if (lang() !== "zh") return;
    var walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT, {
      acceptNode: function (node) {
        var p = node.parentElement;
        if (!p || SKIP[p.tagName]) return NodeFilter.FILTER_REJECT;
        return zhText(norm(node.nodeValue)) !== null ? NodeFilter.FILTER_ACCEPT : NodeFilter.FILTER_SKIP;
      }
    });
    var nodes = [];
    while (walker.nextNode()) nodes.push(walker.currentNode);
    nodes.forEach(function (node) {
      var raw = node.nodeValue, zh = zhText(norm(raw));
      if (zh === null) return;
      originals.push({node: node, original: raw});
      node.nodeValue = raw.match(/^\s*/)[0] + zh + raw.match(/\s*$/)[0];
    });
    document.querySelectorAll("*").forEach(function (el) {
      ATTRS.forEach(function (attr) {
        var value = el.getAttribute(attr);
        if (!value) return;
        var zh = zhText(norm(value));
        if (zh === null) return;
        var saved = attrOriginals.get(el) || {};
        if (saved[attr] === undefined) saved[attr] = value;
        attrOriginals.set(el, saved);
        el.setAttribute(attr, zh);
        originals.push({el: el, attr: attr});
      });
    });
  }

  function setLang(target) {
    try { localStorage.setItem(KEY, target); } catch (e) {}
    apply();
    var toggle = document.getElementById("archive-lang");
    if (toggle) toggle.textContent = lang() === "zh" ? "EN" : "中文";
  }

  window.ArchiveI18N = {phrases: ZH, lang: lang, apply: apply, set: setLang};
  apply();
  // 翻译已就位：显示页面（base.html 在中文会话里先隐藏了 body）。
  try { document.documentElement.classList.remove("i18n-loading"); } catch (e) {}

  // 按钮在 base.html 的顶部操作区里（不在 nav 内）
  var toggle = document.getElementById("archive-lang");
  if (toggle) {
    toggle.textContent = lang() === "zh" ? "EN" : "中文";
    toggle.addEventListener("click", function () { setLang(lang() === "zh" ? "en" : "zh"); });
  }
})();
