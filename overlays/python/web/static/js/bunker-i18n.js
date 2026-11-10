/* Pod Programs（Bunker）中文词典与页面翻译。
 *
 * lunar-base 的 i18n.js 用 data-i18n 标注它自己的模板；Bunker 的页面沿用英文
 * 原文，因此这里按「英文原文 → 中文」翻译文本节点与 placeholder/title 等属性，
 * 切换语言时把原文放回。数字、日期、标题等变化的文案由下方的正则规则处理。
 *
 * 默认中文：lb_lang 未设置即中文（i18n.js 的 currentLang 只在显式选择过英文时
 * 才用英文，配合这里的默认值即为「中文为主」）。
 *
 * 只在 main / nav / footer / .terminal-bar 内工作，跳过 script/style/pre/code/
 * textarea/select 与 .no-i18n，因此不会动到用户数据、物品名与代码示例。
 */
(function () {
  "use strict";

  var ZH = {
    "\"Premium items\" stores an acquisition timestamp instead of a quantity, so its total is not shown.": "「高级物品」记录的是获得时间而不是数量，因此不显示总数。",
    "(none)": "（无）",
    "(unset)": "（未设置）",
    "+ more": "+ 更多",
    "+amount": "+数量",
    "/ weapons · CATALOG: owned / total · missing": "/ 武器 · 图鉴：已拥有 / 总数 · 缺少",
    "10-draw guarantee": "十连保底",
    "144 weeks, until": "144 周，直到",
    "2 of 2 currencies": "2 / 2 种货币",
    "Add All Missing Companions": "补齐所有缺少的随从",
    "Add All Missing Debris": "补齐所有缺少的碎片",
    "Add costumes and choose karma effects. Story-starter costumes are earned through play. Each change is backed up first.": "添加服装并选择因果效果。剧情初始服装需在游戏中获得。每次修改前都会先备份。",
    "Add weapons, including their skills and stories. Story-starter weapons are earned through play. The inventory limit is 999 weapons. Each change is backed up first.": "添加武器，包括其技能与故事。剧情初始武器需在游戏中获得。背包上限为 999 把武器。每次修改前都会先备份。",
    "Advanced configuration": "高级配置",
    "All Missing Remnants": "补齐所有缺少的残片",
    "All characters, weapons, items and story progress.": "全部角色、武器、物品与剧情进度。",
    "All events, summons and shops stay open.": "所有活动、召唤与商店保持开放。",
    "Also": "另外",
    "Amount": "数量",
    "Amounts are added to your inventory. Each change is backed up first.": "数量会加入背包。每次修改前都会先备份。",
    "Anything you skip can't be claimed later.": "跳过的内容之后无法补领。",
    "Applies to regular and multi-step summons from the next draw. The game's Rates page shows these values. Experimental.": "对之后的普通与多段召唤生效。游戏内的「概率」页面会显示这些数值。实验性。",
    "Apply": "应用",
    "Applying… Keep Pod Programs open.": "正在应用… 请保持 Pod Programs 开启。",
    "Arena seasons and monthly passes end with rewards.": "竞技场赛季与月度通行证会结算奖励。",
    "Back up & restore": "备份与恢复",
    "Based on NavHobbyDev's lunar-tear-masterdata-patcher.": "基于 NavHobbyDev 的 lunar-tear-masterdata-patcher。",
    "Build a Set": "生成一套",
    "Build a four-star set, upgrade memoirs to level 15, or change their stats. Each change is backed up first.": "生成一套四星回忆、将回忆升到 15 级，或修改其属性。每次修改前都会先备份。",
    "Building game data… Keep Pod Programs open.": "正在读取游戏数据… 请保持 Pod Programs 开启。",
    "Bunker Terminal": "地堡终端",
    "Calendar on": "日历已开启",
    "Cancel": "取消",
    "Characters": "角色",
    "Characters & equipment": "角色与装备",
    "Checking…": "检查中…",
    "Choose which events and shops to include. Your current data is backed up first.": "选择要包含的活动与商店。当前数据会先备份。",
    "Closes": "关闭时间",
    "Coming up": "即将开放",
    "Companions": "随从",
    "Consumable items": "消耗品",
    "Consumables": "消耗品",
    "Content": "内容",
    "Content patcher": "内容修补器",
    "Costume Editor": "服装编辑",
    "Costumes": "服装",
    "Costumes & karma": "服装与因果",
    "Costumes in ★3 (%)": "★3 中的服装占比（%）",
    "Costumes in ★4 (%)": "★4 中的服装占比（%）",
    "Create backup": "创建备份",
    "Currencies": "货币",
    "Current:": "当前：",
    "Date": "日期",
    "Default (60 / 25 / 10 / 4.7 / 0.3)": "默认（60 / 25 / 10 / 4.7 / 0.3）",
    "Deploy and sign in to the game once on this device, then you can choose which player it uses.": "先在本机部署并登录一次游戏，之后即可选择使用哪位玩家。",
    "Display": "显示",
    "Distinct IDs": "去重 ID 数",
    "Distinct items": "去重物品数",
    "End of transmission // Glory to mankind": "通信结束 // 愿人类荣光永存",
    "Ends": "结束时间",
    "Event medals expire when their shop closes.": "活动兑换币会在其商店关闭时失效。",
    "Event or summon name": "活动或召唤名称",
    "Choose the player": "选择玩家",
    "Events & shops": "活动与商店",
    "Everything open": "全部开放",
    "Exalt All Available Characters": "升华所有可用角色",
    "Experimental: higher settings use more battery and make the device warmer. The game uses them the next time it opens.": "实验性：数值越高越耗电、机身越热。游戏下次启动时生效。",
    "Export current master data": "导出当前主数据",
    "FILTER": "筛选",
    "FREE": "免费",
    "Featured share (%)": "当期占比（%）",
    "Fill All Karma Slots": "填满所有因果槽",
    "Fill Mythic Slab Pages of all Available Characters": "填满所有可用角色的秘传石板",
    "Fix Slots on a Memoir": "修正一条回忆的副词条",
    "Frame rate": "帧率",
    "Frame rate & resolution": "帧率与分辨率",
    "Free Gems": "免费宝石",
    "Free gems": "免费宝石",
    "GRANT": "发放",
    "GRANT ALL CHOSEN": "发放所选全部",
    "GRANT ALL MISSING ()": "补齐全部缺少（）",
    "GRANT SET AT LV15": "以 15 级发放整套",
    "Gems": "宝石",
    "Gems, gold & materials": "宝石、金币与素材",
    "ID": "ID",
    "IN USE": "使用中",
    "INVENTORY:": "背包：",
    "Identity": "身份",
    "Important Items": "重要物品",
    "Important items": "重要物品",
    "Imported master data": "已导入的主数据",
    "Inventory": "背包",
    "Item Editor": "物品编辑",
    "Items": "物品",
    "Jump": "跳转",
    "Jump to": "跳转到",
    "Jump to…": "跳转到…",
    "Kept": "保留",
    "Last login": "最近登录",
    "Leftover summon shards become Medals soon after a summon ends.": "召唤结束后，剩余的召唤碎片会很快转为奖章。",
    "Length": "时长",
    "Level": "等级",
    "Level / EXP": "等级 / 经验",
    "Logins": "登录次数",
    "Loop": "循环",
    "Lunar Base by NMeliksah · Masterdata Patcher by NavHobbyDev": "Lunar Base 由 NMeliksah 制作 · 主数据修补器由 NavHobbyDev 制作",
    "MAX ALL": "全部拉满",
    "MISSING": "缺少",
    "Marks every Dark Memory weapon cutscene as already played (84 entries). Use after mass-adding Dark Memory weapons to bypass the queued first-launch cutscene loop that otherwise soft-locks progression.": "把所有黑之记忆的武器剧情标记为已观看（84 条）。批量添加黑之记忆武器后使用，可跳过首次启动时排队播放的剧情，否则进度会卡住。",
    "Mass Actions": "批量操作",
    "Mass Upgrades": "批量强化",
    "Master-data snapshot": "主数据快照",
    "Materials": "素材",
    "Memoir": "回忆",
    "Memoir Editor": "回忆编辑",
    "Memoirs": "回忆",
    "Message": "留言",
    "Move ahead": "前进",
    "Moves at the daily reset. Stamina and daily missions keep normal time.": "随每日重置移动。体力与日常任务照常计时。",
    "Multi-step summons raise ★4 on steps 1, 3 and 5": "多段召唤会在第 1、3、5 步提升 ★4 概率",
    "NOT OWNED": "未拥有",
    "Name": "名称",
    "New player": "新玩家",
    "Next update": "下次更新",
    "Next week": "下周",
    "No backups yet.": "还没有备份。",
    "No changes yet.": "还没有变更。",
    "No memoirs owned yet. Build a set above first.": "还没有回忆。请先在上方生成一套。",
    "No more updates in this loop.": "本循环内没有更多更新。",
    "No users found in the database.": "数据库中没有找到用户。",
    "Nothing is open right now.": "当前没有开放的内容。",
    "Now": "now",
    "OWNED": "已拥有",
    "Only current events, summons and shops are open.": "仅开放当前的活动、召唤与商店。",
    "Open now": "当前开放",
    "Open there": "在那里打开",
    "Opens": "开放时间",
    "Operator link // Standing by": "操作员链路 // 待命",
    "Or pick a week": "或选择某一周",
    "Original": "原始",
    "Original calendar": "原始日历",
    "Original file & export": "原始文件与导出",
    "Original master data": "原始主数据",
    "Other 4-Star": "其他四星",
    "Owned: / . Enter percentage stats multiplied by 10: 3% = 30, 12.5% = 125.": "已拥有：/ 。百分比属性请乘以 10 输入：3% = 30，12.5% = 125。",
    "PAID": "付费",
    "Paid Gems": "付费宝石",
    "Paid gems": "付费宝石",
    "Parts": "部件",
    "Patch configuration": "修补配置",
    "Picks the chosen effect for every unlocked karma slot. If a costume's odds pool doesn't contain the chosen effect, falls back to the rarest pool entry. Overwrites existing rolls. Run Upgrade All Costumes first to unlock slots.": "为每个已解锁的因果槽抽选指定效果。若该服装的池子里没有指定效果，则退回池中最稀有的条目。会覆盖已有结果。请先运行「强化所有服装」解锁槽位。",
    "Play the game once to create a save.": "先玩一次游戏以生成存档。",
    "Player ID": "玩家 ID",
    "Players": "玩家",
    "Pod Programs": "Pod Programs",
    "Premium items": "高级物品",
    "Presets": "预设",
    "Presets are off while the calendar is on.": "日历开启时预设不可用。",
    "Previous versions": "历史版本",
    "Profile & inventory": "档案与背包",
    "Programs": "程序",
    "RESTORE": "RESTORE",
    "REWRITE SLOTS": "重写副词条",
    "RUN": "运行",
    "Recollections of Dusk": "黄昏的记忆",
    "Registered": "注册时间",
    "Registered Users": "已注册用户",
    "Replays the game from launch day, once the first summons opened. Events, summons and seasons open and close on their original dates.": "从开服当天重播，直到首个召唤开放。活动、召唤与赛季按原始日期开启与结束。",
    "Resolution": "分辨率",
    "Restore": "恢复",
    "Restoring…": "正在恢复…",
    "SLOT": "词条",
    "SLOT : --": "词条：--",
    "Save": "保存",
    "Save Data": "存档",
    "Save backups": "存档备份",
    "Save data": "存档",
    "Save editors keep a backup before each change.": "存档编辑器在每次修改前都会先备份。",
    "Save speed": "存档速度",
    "Schedule": "日程",
    "Search": "搜索",
    "Search by costume name, character, or id...": "按服装名、角色或 ID 搜索…",
    "Search by name or id...": "按名称或 ID 搜索…",
    "Search by weapon name or id...": "按武器名或 ID 搜索…",
    "Search consumables by name or id...": "按名称或 ID 搜索消耗品…",
    "Search events and summons": "搜索活动与召唤",
    "Search important items by name or id...": "按名称或 ID 搜索重要物品…",
    "Search materials by name or id...": "按名称或 ID 搜索素材…",
    "Set": "设置",
    "Sets & stats": "套装与属性",
    "Show": "显示",
    "Skip All Dark Memory Cutscenes": "跳过所有黑之记忆剧情",
    "Skips": "跳过",
    "Slot (locked or no costume)": "词条槽（未解锁或未选服装）",
    "Slot 1 (locked or no costume)": "词条槽 1（未解锁或未选服装）",
    "Slot 2 (locked or no costume)": "词条槽 2（未解锁或未选服装）",
    "Slot 3 (locked or no costume)": "词条槽 3（未解锁或未选服装）",
    "Source table": "来源表",
    "Special Gift Roulette": "特别赠礼轮盘",
    "Speed": "速度",
    "Stackables": "可叠加物品",
    "Start a new player on this device. The current player is kept, and you can switch back to it here.": "在本机开始一位新玩家。当前玩家会保留，之后可在此切回。",
    "Start calendar": "开启日历",
    "Starts": "开始时间",
    "Subjugation": "讨伐战",
    "Summon Rates": "召唤概率",
    "Summon rates": "召唤概率",
    "Switch language": "切换语言",
    "Switch to English": "切换到英文",
    "Switch to everything open": "切换到「全部开放」",
    "Switch to 中文": "切换到中文",
    "The bundled original is used for every preset. You can replace it with your own original master data.": "所有预设都会使用内置原始文件。你可以替换为自己的原始主数据。",
    "The frame rate never goes above the screen's refresh rate; Screen maximum uses the highest it supports. The resolution applies to the game's higher graphics settings and never goes above the screen's own. Power saving keeps its lower frame rate.": "帧率不会超过屏幕刷新率；「屏幕最大值」使用其支持的最高值。分辨率作用于游戏较高的画质档，且不会超过屏幕本身。「省电模式」保持其较低帧率。",
    "The game plays as player . Use this player instead? Player is kept, and your save is backed up first.": "游戏将以玩家 的身份运行。要改用这位玩家吗？当前玩家会保留，存档会先备份。",
    "The game plays as the player marked IN USE. Open another player to switch.": "游戏以标记为「使用中」的玩家运行。打开其他玩家即可切换。",
    "The game plays as this player on this device.": "游戏在本机以这位玩家的身份运行。",
    "The game restarts from launch on your next Deploy.": "下次「部署」时游戏会从头重新开始。",
    "The latest 50 backups are kept. Changes are backed up automatically.": "保留最近 50 份备份。每次修改都会自动备份。",
    "The latest backups are kept. Changes are backed up automatically.": "保留最新的若干份备份。每次修改都会自动备份。",
    "The menu's gem wheel, up to 6 spins a day. Chance of each amount, adding up to 100%.": "菜单中的宝石轮盘，每天最多 6 次。各档概率之和为 100%。",
    "This device": "本机",
    "Thoughts (memoirs)": "思念（回忆）",
    "Today": "今天",
    "Total count": "总数",
    "Total logins": "累计登录",
    "Type": "类型",
    "Type RESTORE": "输入 RESTORE",
    "Type RESTORE to confirm": "输入 RESTORE 以确认",
    "UPDATE ALL KARMA EFFECTS ()": "更新所有因果效果（）",
    "UUID": "UUID",
    "Upgrade All Companions": "强化所有随从",
    "Upgrade All Costumes": "强化所有服装",
    "Upgrade All Memoirs": "强化所有回忆",
    "Upgrade All Weapons": "强化所有武器",
    "Upgrade Manager": "强化管理",
    "Upgrade characters and equipment without spending gold or materials. Each change is backed up first.": "无需消耗金币或素材即可强化角色与装备。每次修改前都会先备份。",
    "Upgrades": "强化",
    "Use original file": "使用原始文件",
    "Use this player": "使用这位玩家",
    "User ID": "用户 ID",
    "Users": "用户",
    "Weapon Editor": "武器编辑",
    "Weapons": "武器",
    "Weapons & evolutions": "武器与进化",
    "Week": "周",
    "Week of": "所属周",
    "Week ·": "周 ·",
    "What changes": "变更内容",
    "When a draw lands on a rarity and type that has featured items, this is the chance it is a featured one.": "当抽卡落在具有「当期」物品的稀有度与类型时，此即抽到当期物品的概率。",
    "YoRHa": "YoRHa",
    "You can only move forward. To replay, start a new loop.": "只能向前推进。要重玩请开启新的循环。",
    "You miss": "你会损失",
    "You still get": "你仍可获得",
    "Your current save will be backed up before restoring.": "恢复前会先备份当前存档。",
    "[ EDIT COSTUMES ]": "[ 编辑服装 ]",
    "[ EDIT ITEMS ]": "[ 编辑物品 ]",
    "[ EDIT WEAPONS ]": "[ 编辑武器 ]",
    "[ MEMOIR EDITOR ]": "[ 回忆编辑 ]",
    "[ UPGRADE MANAGER ]": "[ 强化管理 ]",
    "[PRIORITY]": "[优先级]",
    "[R40/30/20] = rarity tier. [Ngrp] = how many distinct odds groups in the game include this effect (more = more costumes will match this exact pick; the rest fall back to rarest in their own pool).": "[R40/30/20] = 稀有度档位。[Ngrp] = 游戏中有多少个不同的概率组包含此效果（越多表示越多服装能匹配该选择；其余服装会退回各自池中最稀有的条目）。",
    "[R] [grp]": "[R] [组]",
    "[] · lv · main_id= · uuid=…": "[] · 等级 · main_id= · uuid=…",
    "add": "添加",
    "and more": "以及更多",
    "campaigns": "活动",
    "day": "天",
    "event items expire": "活动物品失效",
    "first on": "首次于",
    "gems (%)": "宝石（%）",
    "in the original": "原始数据中",
    "missing of total (Important Items prefixed \"Remnant\")": "缺少 / 总数（「重要物品」中以「残片」开头者）",
    "missing of total (one Thought item per costume's awakening 5; Upgrade All Costumes also grants these naturally)": "缺少 / 总数（每套服装觉醒 5 各 1 个思念；「强化所有服装」也会自然发放）",
    "missing of total (skips known game-breaking ids 54-62)": "缺少 / 总数（跳过已知会导致故障的 ID 54-62）",
    "more": "更多",
    "n/a": "不适用",
    "never": "从未",
    "of owned chars below max (5)": "/ 已拥有角色中未满级（5）的数量",
    "of owned companions below max level 50": "/ 已拥有随从中未满级 50 的数量",
    "owned / total": "已拥有 / 总数",
    "owned / total · missing": "已拥有 / 总数 · 缺少",
    "owned costumes — awaken to 5 (grants Debris), ascend to 4, enhance to cap, active skill to lv15, unlock 3 karma slots (SSR; rolls left to player)": "已拥有服装 — 觉醒至 5（发放碎片）、升华至 4、强化至上限、主动技能至 15 级、解锁 3 个因果槽（SSR；具体结果留给玩家抽取）",
    "owned memoirs — sets every part level to (sub-status rows untouched).": "已拥有回忆 — 将所有部件等级设为（副词条不动）。",
    "owned weapons — ascend, evolve to chain end, refine if eligible, enhance to cap, all skills + abilities to lv15 (cost-bypassing)": "已拥有武器 — 升华、进化至链末、符合条件则精炼、强化至上限、所有技能 + 能力升至 15 级（免消耗）",
    "panels across owned chars (both monuments, all 3 ranks)": "个石板，覆盖已拥有角色（两座纪念碑、全部 3 阶）",
    "rewards": "奖励",
    "until": "直到",
    "week day": "周 日",
    "· needs a save": "· 需要存档",
    "· week of": "· 周次",
    "← All users": "← 所有用户",
    "★3 or higher": "★3 或更高",
    "★3 rate (%)": "★3 概率（%）",
    "★4 & featured odds": "★4 与当期概率",
    "★4 rate (%)": "★4 概率（%）",
    "Game default": "游戏默认",
    "Screen maximum": "屏幕最大值",
    "Screen's own resolution": "屏幕本身分辨率",
    "30 fps (game default)": "30 fps（游戏默认）",
    "60 fps": "60 fps",
    "90 fps": "90 fps",
    "120 fps": "120 fps",
    "Total: 100%": "合计：100%",
    "Default (5% ★4, 15% ★3)": "默认（5% ★4，15% ★3）",
    "Generous (15% ★4, 30% ★3)": "宽松（15% ★4，30% ★3）",
    "Featured first (10% ★4, always featured, ★4 in every 10-draw)": "当期优先（10% ★4，必为当期，十连必出 ★4）",
    "3-Star": "三星",
    "Save backups": "存档备份",
    "Summon rates": "召唤概率",
    "Frame rate": "帧率",
    "Resolution": "分辨率",
    "Deck Builder": "卡组构建器",
    "Decks picked the way experienced players picked them at the end of service, equipped from the game's own data, with the game's exact Force. Choose a deck, see why each piece is in it, and write it to the Arena or Loadout decks you choose. Your other decks stay as they are, and Save Data keeps a snapshot from before every write.": "按照停服前资深玩家的思路挑选卡组，装备来自游戏自身数据，使用游戏精确的战力。选择一套卡组，查看每个部件入选的原因，然后将其写入你选择的竞技场或配装卡组。你的其他卡组保持不变，存档会在每次写入前保留快照。",
    "Player": "玩家",
    "Deck for": "用途",
    "Attack": "攻击",
    "Defense": "防御",
    "Build from": "构建来源",
    "What I own": "我所拥有的",
    "All maxed": "全部满级",
    "All maxed ranks the best decks in a world where you own everything: every costume of every character, fully raised. Each costume you own adds to its character's stats, so if you're missing some, the deck does a little worse for you than shown. Writing a deck adds missing pieces maxed and raises your own costumes and characters.": "「全部满级」在一个你拥有一切的世界里排列最佳卡组：每个角色的每套服装都完全提升。你拥有的每套服装都会增加对应角色的属性，所以如果缺少一些，卡组实际表现会略低于展示。写入卡组会以满级添加缺失部件，并提升你自己的服装和角色。",
    "What I own uses your costumes as they are. Allow up to": "「我所拥有的」按原样使用你的服装。允许最多添加",
    "pieces to be added.": "个部件。",
    "All": "全部",
    "Boss": "Boss",
    "Difficulty": "难度",
    "Against": "对手",
    "General best": "综合最佳",
    "Filters": "筛选",
    "Clear all": "全部清除",
    "Close": "关闭",
    "Find a character": "查找角色",
    "Tap a costume once to require it (✓), again to leave it out (✕), again to clear it.": "点击一次服装设为必选（✓），再点一次排除（✕），再点一次清除。",
    "Loading…": "加载中…",
    "Strategy": "策略",
    "Any": "任意",
    "Stall": "拖延",
    "Burst": "爆发",
    "Dauntless": "无畏",
    "Compromise counter": "反击妥协",
    "Tank & provoke": "坦克与挑衅",
    "Mono-element": "单属性",
    "Must have these effects": "必须具有以下效果",
    "Compromise": "妥协",
    "Cleanse": "净化",
    "Revive": "复活",
    "Provoke": "挑衅",
    "Indomitable": "不屈",
    "Usable from start": "开局可用",
    "Element by slot": "按位置选属性",
    "Left": "左",
    "Middle": "中",
    "Right": "右",
    "Fire": "火",
    "Water": "水",
    "Wind": "风",
    "Light": "光",
    "Dark": "暗",
    "Leave out elements": "排除属性",
    "Minimum per character": "每个角色最低要求",
    "Agility": "敏捷",
    "HP": "生命",
    "ATK": "攻击",
    "Crit rate ‰": "暴击率 ‰",
    "Similar decks are folded into one, so the list doesn't repeat the same deck with one piece changed.": "相似卡组会合并为一条，列表不会重复只换了一个部件的同一卡组。",
    "Clear": "清除",
    "Show decks": "显示卡组",
    "Decks": "卡组",
    "Sort": "排序",
    "Best match": "最佳匹配",
    "Force": "战力",
    "Fewest to add": "添加最少",
    "Back to the decks": "返回卡组列表",
    "Read more": "展开更多",
    "Read less": "收起",
    "Main weapon": "主武器",
    "Sub weapon": "副武器",
    "Companion": "随从",
    "Debris": "碎片",
    "Raise what you own?": "提升你拥有的？",
    "Write to": "写入到",
    "Arena": "竞技场",
    "Loadout": "配装",
    "Empty": "空",
    "CANCEL": "取消",
    "REPLACE": "替换",
    "WRITE DECK": "写入卡组",
    "Data override.": "数据覆盖。",
    "Also used in": "同时用于",
    "Adds": "添加",
    "piece": "个部件",
    "pieces": "个部件",
    "fully raised.": "完全提升。",
    "over the three decks,": "总计三套卡组，",
    "damage": "伤害",
    "wins": "胜率",
    "Three decks, nine characters": "三套卡组，九个角色",
    "Deck": "卡组",
    "knock-down": "击倒",
    "Support": "辅助",
    "Couldn't load the costumes.": "无法加载服装。",
    "No costume matches.": "没有匹配的服装。",
    "That deck is no longer listed": "该卡组已不在列表中",
    "Choose a deck slot to write to": "请选择要写入的卡组位置",
    "Deck slots are Arena or Loadout decks 1 to": "卡组位置为竞技场或配装卡组 1 至",
    "Only a costume of this deck that is below the staged level can be raised": "只能提升此卡组中低于暂存等级的服装",
    "Only a costume of this loadout that is below the staged level can be raised": "只能提升此配装中低于暂存等级的服装",
    "Unknown player": "未知玩家",
    "The Deck Builder stage is not ready": "卡组构建器暂存区尚未就绪",
    "Stop Lunar Tear before changing the player.": "切换玩家前请先停止 Lunar Tear。",
    "Saved.": "已保存。",
    "Preparing…": "准备中…",
    "Preparing the Deck Builder stage…": "正在准备卡组构建器暂存区…",
    "Arena deck": "竞技场卡组",
    "Loadout deck": "配装卡组",
    "Why": "原因",
    "Costume": "服装",
    "Rank": "排名",
    "Win rate": "胜率",
    "To add": "需添加",
    "Expert pick": "专家推荐",
    "Data pick": "数据推荐",
    "beats": "击败",
    "by": "概率",
    "Variants": "变体",
    "Damage": "伤害",
    "Knockdowns": "击倒次数",
    "Standing": "站位",
    "Phase": "阶段",
    "score": "分数",
    "pts": "分",
    "Operator 6O": "操作员 6O",
    "costume": "服装",
    "element": "属性",
    "slot": "位置",
    "new": "新",
    "Deck 1": "卡组 1",
    "Deck 2": "卡组 2",
    "Deck 3": "卡组 3",
    "Gift": "礼物",
    "Send yourself anything the game can hold. You claim it in the game's Gift Box like any other gift. The game keeps running: the Gift Box shows it after your next action.": "送给自己任何游戏能容纳的东西。你像领取其他礼物一样在游戏的礼物箱中领取它。游戏继续运行：下次操作后礼物箱就会显示。",
    "> The first gift also adds its text to the game data, so the game returns to its title screen to load it.": "› 第一份礼物还会将文本写入游戏数据，因此游戏会返回标题画面重新加载。",
    "1 :: Choose": "1 :: 选择",
    "Search every category by name": "按名称搜索所有分类",
    "2 :: Send": "2 :: 发送",
    "Nothing chosen yet": "尚未选择",
    "SEND": "发送",
    "Count": "数量",
    "Pick a category, or search.": "选择一个分类，或直接搜索。",
    "Waiting in the Gift Box": "礼物箱中等待领取",
    "Nothing from Bunker is waiting.": "没有来自地堡的礼物在等待。",
    "One copy per gift. A copy you already own turns into its usual exchange items when you claim it.": "每份礼物限一个。已拥有的副本在领取时会转化为通常的兑换道具。",
    "One per gift.": "每份限一个。",
    "Nothing matches.": "没有匹配项。",
    "Checking how many can be claimed…": "正在查询可领取数量……",
    "Nothing more of this can be claimed now.": "此物品当前无法再领取更多。",
    "Enter a whole number, 1 or more.": "请输入 1 或更大的整数。",
    "The gift was not sent": "礼物未能发送",
    "Story Jump": "剧情跳转",
    "Jump to the start of a chapter, or to a quest in one: every story quest before it is cleared and pays its first-clear rewards (characters, weapons, companions, key items, gems). Missions and drops are not paid. The save is backed up first. Forward only.": "跳转到某一章节的开头或其中的任务：之前的所有剧情任务都会被通关并发放首次通关奖励（角色、武器、从者、关键道具、宝石）。任务和掉落不发放。存档会先备份。只能向前跳转。",
    "Route": "路线",
    "cleared": "已通关",
    "Jump to start": "跳转到开头",
    "you are here": "▶ 你在这里",
    "other route": "另一条路线",
    "Working out what this clears…": "正在计算本次跳转将通关的内容……",
    "[ JUMP ]": "[ 跳转 ]",
    "Missions and drops are not paid. This can only be undone by restoring the backup taken first.": "任务和掉落不发放。此操作只能通过恢复先前创建的备份来撤销。",
    "Jumping…": "正在跳转……",
    "Done": "完成",
    "exp and gold for each quest": "每个任务的经验值和金币",
    "user, possession_type, possession_id and count are required": "需要提供 user、possession_type、possession_id 和 count",
    "whole numbers only": "仅限整数",
    "Chapter": "章节",
    "Season": "季",
    "Quest": "任务",
    "Cleared": "已通关",
    "Clears": "将通关",
    "quest": "个任务",
    "quests": "个任务",
    "and gave:": "并发放：",
    "and gives:": "并将发放：",
    "gems": "宝石",
    "Backup:": "备份：",
    "Jumped to": "已跳转到",
    "User": "用户",
    "this save took route": "此存档已走路线",
    "the start of Chapter": "章节开头",
    "of Chapter": "的",
    "The calendar's game data could not be rebuilt": "日历的游戏数据未能重建",
    "the chapter opens at the next calendar change.": "该章节将在下次日历变更时开放。",
    "The calendar's game data was rebuilt, so the chapter is open.": "日历的游戏数据已重建，该章节已开放。",
    "quests. Backup:": " 个任务。备份：",
    "Up to": "最多还可领取 ",
    "more.": " 个。",
    "That is more than can be claimed now: up to": "超出当前可领取数量：最多 ",
    "Sent:": "已发送：",
    ". It is in the game's Gift Box.": "。已放入游戏的礼物箱。",
    "×": " ×",
    "Send yourself anything": "给自己发任意物品",
    "Arena decks, explained": "竞技场卡组，附解析",
    "Skip ahead to a chapter": "跳转到章节",
    "> The game is still running. After a change to your save or the game's data, it returns to its title screen to load it. Turning the calendar off, switching \"Show original dates\" or starting a new day closes it.": "> 游戏仍在运行。修改存档或游戏数据后，游戏会回到标题画面加载。关闭日历、切换「显示原始日期」或开始新的一天会关闭游戏。",
    "● Game running · a change sends it back to its title screen": "● 游戏运行中 · 修改会送它回标题画面",
    "Game running · a change sends it back to its title screen": "游戏运行中 · 修改会送它回标题画面",
    "Mods": "模组",
    "Mods :: Lunar Base": "模组 :: Lunar Base",
    "Changes to how the game plays, for every player on this device. Every mod is off until you turn it on; turning it off again goes back to the original game. Mods never change your save on their own, and they apply without a restart. Challenges change the game data, so the game goes back to its title screen to load them.": "改变游戏的玩法，作用于本机的所有玩家。每个功能默认关闭，开启才生效；再次关闭即恢复原版游戏。功能从不擅自修改你的存档，并且无需重启即可生效。挑战会修改游戏数据，因此游戏会返回标题画面重新加载。",
    "Preset": "预设",
    "Every mod off: the game as it was.": "全部关闭：恢复游戏原貌。",
    "Comfort": "舒适",
    "The Comfort Mod's set: its eight mods on, rewards ×10.": "Comfort Mod 的组合：开启其中八项，奖励 ×10。",
    "Everything": "全部",
    "Every mod on, rewards and EXP ×10. Challenges stay off.": "开启全部功能，奖励与 EXP ×10。挑战保持关闭。",
    "Current: your own choice of mods below.": "当前：下方自选的功能组合。",
    "Use preset": "使用预设",
    "Economy": "经济",
    "Quests": "任务",
    "Summons": "召唤",
    "World": "世界",
    "Challenges": "挑战",
    "Free stamina": "免费体力",
    "Quests and skips cost no stamina.": "任务与跳过不消耗体力。",
    "Stamina items become gold": "体力道具换金币",
    "Stamina recovery items you receive arrive as gold instead. Items you already hold stay.": "收到的体力恢复道具会改为金币发放。已持有的道具不变。",
    "Premium tickets become gems": "付费券换宝石",
    "Premium summon tickets you receive arrive as free gems instead. Tickets you already hold stay.": "收到的付费召唤券会改为免费宝石发放。已持有的券不变。",
    "Unlimited shop stock": "商店无限库存",
    "Shop items that restock daily, weekly or monthly never run out. Items with a lifetime limit keep it.": "每日、每周或每月补货的商店商品永不售罄。终身限购的商品保留限购。",
    "Lost Items give gems": "Lost Item 给宝石",
    "Picking up a Lost Item gives a random amount of free gems.": "拾取 Lost Item 会随机获得免费宝石。",
    "Unlimited daily plays": "每日次数无限",
    "Quests with a daily clear limit can be played as often as you like.": "有每日通关次数限制的关卡可以随意重复挑战。",
    "Free skips": "免费跳过",
    "Skipping a quest uses no skip tickets.": "跳过关卡不消耗跳过券。",
    "Reward multiplier": "奖励倍率",
    "Multiplies a quest's drops, gold and gems. Dark Memory quests, memoirs, costumes and weapons stay as they are.": "倍增关卡的掉落、金币与宝石。Dark Memory 关卡、回忆、服装与武器不变。",
    "EXP multiplier": "EXP 倍率",
    "Multiplies the EXP a quest gives you, your characters and their costumes.": "倍增关卡给予你、角色与服装的经验值。",
    "No duplicate ★4": "★4 不重复",
    "A ★4 costume or weapon you already own is swapped for one you don't from the same summon, until you own them all.": "抽到已拥有的 ★4 服装或武器时，会在同一卡池内换成未拥有的，直到集齐为止。",
    "Medals become gems": "奖章换宝石",
    "Every 100 summon medals become 1,000 paid gems and 100 Mama Points, sent to the gift box.": "每 100 枚召唤奖章换成 1,000 付费宝石和 100 点 Mama 点数，发送至礼物箱。",
    "Friends from the story": "剧情好友",
    "2B, 9S, Fio, Lars and others join your friends, cheer you every day and fight with their own costumes in the Arena.": "2B、9S、菲奥、拉尔斯等角色会加入你的好友，每天为你应援，并穿着各自的服装在竞技场出战。",
    "Hard enemies": "强敌",
    "Every enemy's HP, attack and defense, in quests and events. Subjugation bosses stay as they are.": "提升任务与活动中所有敌人的 HP、攻击与防御。讨伐战 Boss 不变。",
    "Weakness only": "弱点限定",
    "Hits that aren't super-effective do half damage. Rewards ×2.": "非弱点克制的攻击只造成一半伤害。奖励 ×2。",
    "Slow skills": "技能变慢",
    "Your skills take 50% longer to come back. Rewards ×2.": "你的技能冷却时间延长 50%。奖励 ×2。",
    "Off": "关闭",
    "Off (×1)": "关闭（×1）",
    "Enemies ×1.5 — rewards ×2": "敌人 ×1.5 — 奖励 ×2",
    "Enemies ×2 — rewards ×3": "敌人 ×2 — 奖励 ×3",
    "Enemies ×3 — rewards ×4": "敌人 ×3 — 奖励 ×4",
    "Enemies ×5 — rewards ×6": "敌人 ×5 — 奖励 ×6",
    "Challenge bonus on quest rewards": "任务奖励的挑战加成",
    "Turn on a challenge to earn it.": "开启一项挑战即可获得加成。",
    "Paused: an Economy, Quests or Summons mod is on.": "已暂停：经济、任务或召唤中有功能开启。",
    "Paused until tomorrow: you started a new day.": "暂停至明天：你开始了新的一天。",
    "Earned on every quest clear.": "每次通关任务都会获得。",
    "Bonuses multiply, up to ×10. The bonus counts only while the Economy, Quests and Summons mods are off; World mods don't matter. After Start a new day, it pauses until the next day. A change here sends the game to its title screen to load it.": "加成可相乘，最高 ×10。仅当经济、任务与召唤中的功能全部关闭时才计入加成；世界功能无影响。开始新的一天后，加成暂停至次日。此处的改动会让游戏返回标题画面加载。",
    "Start a new day": "开始新的一天",
    "Everything daily starts over at once: quest plays, missions, shop restocks, free summons, cheers and the login bonus. Weekly limits and the calendar don't move. The game closes so it starts the day fresh; tap Deploy to play. The challenge bonus pauses until the next day.": "所有每日内容立即重置：关卡次数、任务、商店补货、免费召唤、应援与登录奖励。每周限额与日历不受影响。游戏会关闭以便从新的一天开始；点击 Deploy 即可游玩。挑战加成暂停至次日。",
    "Most mods come from the": "大多数模组来自",
    "Lunar Tear Comfort Mod": "Lunar Tear 舒适 Mod",
    "by NavHobbyDev (MIT).": "由 NavHobbyDev 制作（MIT）。",
    "Comfort changes, off by default": "舒适性修改，默认关闭",
    "> Saved. The mods are in use from the game's next action, with no restart.": "> 已保存。功能从游戏的下一次操作起生效，无需重启。",
    "> Saved. Challenges are in the game data. The game returns to its title screen to load it.": "> 已保存。挑战已写入游戏数据。游戏将返回标题画面加载。",
    "> Saved. Challenges are in the game data. Close Pod Programs and tap Deploy.": "> 已保存。挑战已写入游戏数据。请关闭 Pod Programs 并点击 Deploy。",
    "> Saved. Challenges are off: the game data is as it was. The game returns to its title screen to load it.": "> 已保存。挑战已关闭：游戏数据恢复原样。游戏将返回标题画面加载。",
    "> Saved. Challenges are off: the game data is as it was. Close Pod Programs and tap Deploy.": "> 已保存。挑战已关闭：游戏数据恢复原样。请关闭 Pod Programs 并点击 Deploy。",
    "> Original preset saved. The mods are in use from the game's next action, with no restart.": "> 已保存原始预设。功能从游戏的下一次操作起生效，无需重启。",
    "> Original preset saved. Challenges are off: the game data is as it was. The game returns to its title screen to load it.": "> 已保存原始预设。挑战已关闭：游戏数据恢复原样。游戏将返回标题画面加载。",
    "> Original preset saved. Challenges are off: the game data is as it was. Close Pod Programs and tap Deploy.": "> 已保存原始预设。挑战已关闭：游戏数据恢复原样。请关闭 Pod Programs 并点击 Deploy。",
    "> Comfort preset saved. The mods are in use from the game's next action, with no restart.": "> 已保存舒适预设。功能从游戏的下一次操作起生效，无需重启。",
    "> Comfort preset saved. Challenges are off: the game data is as it was. The game returns to its title screen to load it.": "> 已保存舒适预设。挑战已关闭：游戏数据恢复原样。游戏将返回标题画面加载。",
    "> Comfort preset saved. Challenges are off: the game data is as it was. Close Pod Programs and tap Deploy.": "> 已保存舒适预设。挑战已关闭：游戏数据恢复原样。请关闭 Pod Programs 并点击 Deploy。",
    "> Everything preset saved. The mods are in use from the game's next action, with no restart.": "> 已保存全部预设。功能从游戏的下一次操作起生效，无需重启。",
    "> Everything preset saved. Challenges are off: the game data is as it was. The game returns to its title screen to load it.": "> 已保存全部预设。挑战已关闭：游戏数据恢复原样。游戏将返回标题画面加载。",
    "> Everything preset saved. Challenges are off: the game data is as it was. Close Pod Programs and tap Deploy.": "> 已保存全部预设。挑战已关闭：游戏数据恢复原样。请关闭 Pod Programs 并点击 Deploy。",
    "> ERROR :: Unknown mod": "> ERROR :: 未知功能",
    "> ERROR :: Unknown preset": "> ERROR :: 未知预设",
    "> ERROR :: The reward multiplier must be 1–10": "> ERROR :: 奖励倍率必须为 1–10",
    "> ERROR :: The EXP multiplier must be 1–10": "> ERROR :: EXP 倍率必须为 1–10",
    "> ERROR :: Hard enemies must be 1.5, 2, 3 or 5": "> ERROR :: 强敌倍率必须为 1.5、2、3 或 5",
    "> A new day has started: everything daily starts over. Close Pod Programs and tap Deploy.": "> 新的一天开始了：所有每日内容立即重置。请关闭 Pod Programs 并点击 Deploy。",
    "> Calendar off. Choose content and tap Apply. Close Pod Programs and tap Deploy.": "> 日历已关闭。请选择内容并点击应用。请关闭 Pod Programs 并点击 Deploy。",
    "> Calendar off. Choose content and tap Apply. The game returns to its title screen to load it.": "> 日历已关闭。请选择内容并点击应用。游戏将返回标题画面加载。",
    "> Saved. Close Pod Programs and tap Deploy.": "> 已保存。请关闭 Pod Programs 并点击 Deploy。",
    "> Saved. The game returns to its title screen to load it.": "> 已保存。游戏将返回标题画面加载。",
    "> Calendar on. Close Pod Programs and tap Deploy.": "> 日历已开启。请关闭 Pod Programs 并点击 Deploy。",
    "> Calendar on. The game returns to its title screen to load it.": "> 日历已开启。游戏将返回标题画面加载。",
    "> Speed saved. Close Pod Programs and tap Deploy.": "> 速度已保存。请关闭 Pod Programs 并点击 Deploy。",
    "> Speed saved. The game returns to its title screen to load it.": "> 速度已保存。游戏将返回标题画面加载。",
    "> ERROR :: The calendar is off": "> ERROR :: 日历未开启",
    "Currency": "货币",
    "Summoning": "召唤",
    "Character growth": "角色养成",
    "Weapon growth": "武器养成",
    "Collection": "收藏",
    "Everyday": "日常",
    "Gems & gold": "宝石与金币",
    "Medals & coins": "勋章与硬币",
    "Summon tickets": "召唤券",
    "Summon shards": "召唤碎片",
    "Enhancement": "强化",
    "Handbooks": "手册",
    "Slabs & antler bits": "石板与鹿角残片",
    "Adamant": "坚韧之石",
    "Gemstones": "宝石原石",
    "Awakening stones": "觉醒之石",
    "Karma stones": "业力之石",
    "Insignias & agents": "徽章与终端",
    "Verses": "诗篇",
    "Wish fragments": "许愿碎片",
    "Pearls & crystals": "珍珠与水晶",
    "Minerals": "矿石",
    "Fish": "鱼",
    "Stamina": "体力",
    "Skip & explorer tickets": "跳过券与探索券",
    "regex:^Moved to week (\\d+)\\. (The game returns to its title screen to load it\\.|Close Pod Programs and tap Deploy\\.)$": "已移动至第 {1} 周。{2}",
  };

  // 变化的文案：{1}/{2}… 是捕获组。
  var PATTERNS = [
    ["^Moved to week (\\d+)\\. (The game returns to its title screen to load it\\.|Close Pod Programs and tap Deploy\\.)$", "已移动至第 {1} 周。{2}"],
    ["^(\\d+) owned / (\\d+) total$", "{1} 已拥有 / 共 {2}"],
    ["^(\\d+) owned / (\\d+) total · (\\d+) missing$", "{1} 已拥有 / 共 {2} · 缺 {3}"],
    ["^(\\d+) missing of (\\d+) total \\((\\d+) entries\\)$", "缺 {1} / 共 {2}（{3} 条）"],
    ["^(\\d+) missing of (\\d+) total(.*)$", "缺 {1} / 共 {2}{3}"],
    ["^(\\d+) of (\\d+) owned companions below max level 50$", "已拥有 {2} 名随从中 {1} 名未到 50 级"],
    ["^(\\d+) of (\\d+) owned chars below max \\(5\\)$", "已拥有 {2} 名角色中 {1} 名未满级（5）"],
    ["^(\\d+) (owned)? ?costumes? — (.*)$", "{1} 套已拥有服装 — {3}"],
    ["^(\\d+) (owned)? ?memoirs? — (.*)$", "{1} 套已拥有回忆 — {3}"],
    ["^(\\d+) (owned)? ?weapons? — (.*)$", "{1} 把已拥有武器 — {3}"],
    ["^(\\d+) panels across (\\d+) owned chars(.*)$", "{1} 个石板，覆盖 {2} 名已拥有角色{3}"],
    ["^(\\d+) \\((\\d+) EXP\\)$", "{1}（{2} 经验）"],
    ["^(\\d+) gems \\(%\\)$", "{1} 宝石（%）"],
    ["^GRANT ALL MISSING \\((\\d+)\\)$", "补齐全部缺少（{1}）"],
    ["^UPDATE ALL KARMA EFFECTS \\((\\d+)\\)$", "更新所有因果效果（{1}）"],
    ["^USER (\\d+) :: COSTUMES$", "用户 {1} :: 服装"],
    ["^USER (\\d+) :: EDIT$", "用户 {1} :: 编辑"],
    ["^USER (\\d+) :: MEMOIRS$", "用户 {1} :: 回忆"],
    ["^USER (\\d+) :: UPGRADES$", "用户 {1} :: 强化"],
    ["^USER (\\d+) :: WEAPONS$", "用户 {1} :: 武器"],
    ["^USERS$", "用户"],
    ["^Item Editor :: User (\\d+) :: Lunar Base$", "物品编辑 :: 用户 {1} :: Lunar Base"],
    ["^Costume Editor :: User (\\d+) :: Lunar Base$", "服装编辑 :: 用户 {1} :: Lunar Base"],
    ["^Weapon Editor :: User (\\d+) :: Lunar Base$", "武器编辑 :: 用户 {1} :: Lunar Base"],
    ["^Memoir Editor :: User (\\d+) :: Lunar Base$", "回忆编辑 :: 用户 {1} :: Lunar Base"],
    ["^Upgrade Manager :: User (\\d+) :: Lunar Base$", "强化管理 :: 用户 {1} :: Lunar Base"],
    ["^USER (\\d+)$", "用户 {1}"],
    ["^(.+) :: User (\\d+) :: Lunar Base$", "{1} :: 用户 {2} :: Lunar Base"],
    ["^User (\\d+) :: Lunar Base$", "用户 {1} :: Lunar Base"],
    ["^Users :: Lunar Base$", "用户 :: Lunar Base"],
    ["^← Back to user (\\d+) \\((.+)\\)$", "← 返回用户 {1}（{2}）"],
    ["^(\\d+) weeks?, until (.*)$", "{1} 周，直到 {2}"],
    ["^(.+) in the original$", "原始时间：{1}"],
  ];

  var KEY = "lb_lang";
  function stored() {
    try { return localStorage.getItem(KEY); } catch (e) { return null; }
  }
  if (stored() === null) {
    try { localStorage.setItem(KEY, "zh"); } catch (e) {}
  }
  function lang() {
    return stored() === "en" ? "en" : "zh";
  }

  var SKIP = {SCRIPT: 1, STYLE: 1, PRE: 1, CODE: 1, TEXTAREA: 1, SELECT: 1, KBD: 1, SAMP: 1};
  var ATTRS = ["placeholder", "title", "aria-label", "alt"];
  var originals = [];
  var attrOriginals = new WeakMap();   // 属性原文（aria-label 这类带 - 的名字不能进 dataset）

  function norm(s) {
    return String(s).replace(/\s+/g, " ").trim();
  }

  var MONTHS = {Jan: "1", Feb: "2", Mar: "3", Apr: "4", May: "5", Jun: "6",
                Jul: "7", Aug: "8", Sep: "9", Oct: "10", Nov: "11", Dec: "12"};
  var DAYS = {Mon: "周一", Tue: "周二", Wed: "周三", Thu: "周四", Fri: "周五", Sat: "周六", Sun: "周日"};

  // 英文日期换成中文写法（"Wed 18 Jul 2029" → "2029年7月18日 周三"）。
  function dates(text) {
    return text
      .replace(/\b(?:Mon|Tue|Wed|Thu|Fri|Sat|Sun)\b/g, function (d) { return DAYS[d]; })
      .replace(/\b(\d{1,2}) (Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec) (\d{4})\b/g,
               function (_, d, m, y) { return y + "年" + MONTHS[m] + "月" + d + "日"; });
  }

  function translateText(text) {
    var exact = ZH[text];
    if (exact !== undefined) return exact;
    for (var i = 0; i < PATTERNS.length; i++) {
      var m = text.match(PATTERNS[i][0]);
      if (!m) continue;
      return dates(PATTERNS[i][1].replace(/\{(\d)\}/g, function (_, n) {
        var part = m[Number(n)] !== undefined ? m[Number(n)] : "";
        // 组合文案里的每一段也查词典（如 "0 owned memoirs — …" 的尾段）。
        var inner = ZH[String(part).replace(/\s+/g, " ").trim()];
        return inner !== undefined ? inner : part;
      }));
    }
    // 只含日期的文本（"Sat 17 Oct 2026"）也换成本地写法。
    var localized = dates(text);
    return localized === text ? null : localized;
  }

  function inScope(el) {
    for (var n = el; n && n.nodeType === 1; n = n.parentElement) {
      if (n.classList && n.classList.contains("no-i18n")) return false;
    }
    return true;
  }

  function visitText(root) {
    var walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT, {
      acceptNode: function (node) {
        var parent = node.parentElement;
        if (!parent || SKIP[parent.tagName] || !inScope(parent)) return NodeFilter.FILTER_REJECT;
        var text = norm(node.nodeValue);
        return text && translateText(text) !== null ? NodeFilter.FILTER_ACCEPT : NodeFilter.FILTER_SKIP;
      }
    });
    var nodes = [];
    while (walker.nextNode()) nodes.push(walker.currentNode);
    nodes.forEach(function (node) {
      var raw = node.nodeValue;
      var zh = translateText(norm(raw));
      if (zh === null) return;
      if (node.__i18nOriginal === undefined) node.__i18nOriginal = raw;
      var lead = raw.match(/^\s*/)[0], trail = raw.match(/\s*$/)[0];
      node.nodeValue = lead + zh + trail;
      originals.push({node: node});
    });
  }

  function translateAttrs(root) {
    Array.prototype.forEach.call(root.querySelectorAll("*"), function (el) {
      if (!inScope(el)) return;
      ATTRS.forEach(function (attr) {
        var value = el.getAttribute(attr);
        if (!value) return;
        var zh = translateText(norm(value));
        if (zh === null) return;
        var saved = attrOriginals.get(el) || {};
        if (saved[attr] === undefined) saved[attr] = value;
        attrOriginals.set(el, saved);
        el.setAttribute(attr, zh);
        originals.push({el: el, attr: attr});
      });
    });
  }

  function restore() {
    originals.forEach(function (item) {
      if (item.node) {
        if (item.node.__i18nOriginal !== undefined) item.node.nodeValue = item.node.__i18nOriginal;
        return;
      }
      var saved = attrOriginals.get(item.el);
      if (saved && saved[item.attr] !== undefined) item.el.setAttribute(item.attr, saved[item.attr]);
    });
    originals = [];
  }

  var titleOriginal = null;

  function applyTitle() {
    if (titleOriginal === null) titleOriginal = document.title;
    var zh = translateText(norm(titleOriginal));
    if (zh !== null) document.title = zh;
  }

  function apply() {
    restore();
    if (lang() !== "zh") { if (titleOriginal !== null) { document.title = titleOriginal; titleOriginal = null; } return; }
    applyTitle();
    var roots = document.querySelectorAll("main, nav.primary, footer, .terminal-bar");
    if (!roots.length) roots = [document.body];
    Array.prototype.forEach.call(roots, function (root) {
      visitText(root);
      translateAttrs(root);
    });
  }

  window.BunkerI18N = {phrases: ZH, patterns: PATTERNS, lang: lang, apply: apply};

  document.addEventListener("DOMContentLoaded", apply);
  window.addEventListener("load", apply);

  // 切换语言：先切自己的词典，再让 i18n.js 处理 data-i18n 元素。
  function wrap() {
    if (!window.I18N || window.I18N.__bunkerWrapped) return;
    var set = window.I18N.set;
    window.I18N.set = function (target) {
      set.call(window.I18N, target);
      apply();
    };
    window.I18N.__bunkerWrapped = true;
  }
  wrap();
  document.addEventListener("DOMContentLoaded", wrap);
})();
