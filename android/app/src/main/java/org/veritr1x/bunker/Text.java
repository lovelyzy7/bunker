package org.veritr1x.bunker;

import java.util.HashMap;
import java.util.Map;

/**
 * 界面中文（Bunker 以中文为主）。
 *
 * 启动器全部界面都在代码里构建、文案以英文写在调用处，所以这里按「英文原文 → 中文」
 * 查表：调用处写成 {@code Text.of("Options")}，中文环境显示「选项」，英文环境原样返回。
 * 词典里没有的字符串（物品名、玩家名、路径、版本号等）原样返回。
 */
public final class Text {
    private Text() {}

    private static final Map<String, String> ZH = new HashMap<>();
    /** 语言：默认中文；en 时全部原样返回。 */
    private static String language = "zh";

    public static String language() { return language; }
    public static void language(String value) { language = "en".equals(value) ? "en" : "zh"; }

    /** 中文环境下的译文；没有词条或英文环境时返回原文。 */
    public static String of(String english) {
        if (english == null || "en".equals(language)) return english;
        String zh = ZH.get(english);
        return zh == null ? english : zh;
    }

    /** 带参数的文案：{@code Text.of("%d min left", n)}。 */
    public static String of(String english, Object... args) {
        return String.format(of(english), args);
    }

    private static void put(String en, String zh) { ZH.put(en, zh); }

    static {
        // ---- 主界面 / Bunker ----
        put("BUNKER", "地堡");
        put("GAME FILES", "游戏文件");
        put("PORTS", "端口");
        put("READY", "就绪");
        put("RUNNING", "运行中");
        put("STARTING", "启动中");
        put("STOPPING", "停止中");
        put("STOPPED", "已停止");
        put("Waiting for files", "等待文件");
        put("WAITING FOR FILES", "等待文件");
        put("Importing", "导入中");
        put("IMPORTING", "导入中");
        put("NO FILES", "无文件");
        put("NOT RUNNING", "未运行");
        put("Needs attention", "需要处理");
        put("Options", "选项");
        put("Help", "帮助");
        put("About", "关于");
        put("Support", "支持");
        put("Play", "开始");
        put("Stop", "停止");
        put("Stop Lunar Tear", "停止 Lunar Tear");
        put("Starting", "启动中");
        put("Stopping", "停止中");
        put("Running", "运行中");
        put("Stopped", "已停止");
        put("LUNAR TEAR", "LUNAR TEAR");
        put("LUNAR TEAR // 127.0.0.1", "LUNAR TEAR // 127.0.0.1");
        put("Local game server", "本机游戏服务器");
        put("Server running", "服务器运行中");
        put("Server stopped", "服务器已停止");
        put("Server status and Stop control while you play.", "游戏运行中可查看服务器状态并停止。");
        put("Tap Play to restart.", "点「开始」重新启动。");
        put("DEPLOY  ▶", "部署  ▶");
        put("Deploy: start the game", "部署：启动游戏");
        put("Deploy starts Lunar Tear, then opens the game.", "「部署」会先启动 Lunar Tear，再打开游戏。");
        put("OPEN POD PROGRAMS  ›", "打开 POD PROGRAMS  ›");
        put("OPEN ARCHIVE  ›", "打开档案馆  ›");
        put("POD PROGRAMS OPEN", "POD PROGRAMS 已打开");
        put("Read the story, meet the characters, watch and listen.", "阅读剧情、认识角色、观赏与聆听。");
        put("Edit your save and choose which events and shops appear.", "编辑存档，并选择开放哪些活动与商店。");
        put("Choose game files", "选择游戏文件");
        put("CHOOSE", "选择");
        put("CHANGE", "更改");
        put("Choose the game files", "选择游戏文件");
        put("Choose the game files to begin: the resource dump's .7z or its extracted folder.",
            "先选择游戏文件：资源包的 .7z 或已解压的文件夹。");
        put("Archive (.7z or .zip)", "压缩包（.7z 或 .zip）");
        put("Extracted folder: copy into the app", "已解压文件夹：复制进应用");
        put("Extracted folder: use in place", "已解压文件夹：就地使用");
        put("Use in place", "就地使用");
        put("Use in place works with folders on this phone's storage or SD card. Copy the folder instead.",
            "「就地使用」只支持手机存储或 SD 卡上的文件夹，请改为复制。");
        put("Using a folder in place needs Android 11 or later. Copy it into the app instead.",
            "「就地使用」需要 Android 11 或更高版本，请改为复制进应用。");
        put("Allow All files access", "允许访问所有文件");
        put("Allow All files access for NieR in Settings to read your game files folder, or choose the files again.",
            "请在设置中为 NieR 允许访问所有文件，以读取游戏文件文件夹；或重新选择文件。");
        put("Allow All files access for NieR in Settings to use a folder in place, or copy it instead.",
            "请在设置中为 NieR 允许访问所有文件，以便就地使用文件夹；或改为复制。");
        put("Allow All files access for NieR in Settings.", "请在设置中为 NieR 允许访问所有文件。");
        put("To read the game files where they are, NieR needs All files access. It only reads the folder you choose next.\n\nTurn on the switch in Settings, then come back. Keep the folder where it is afterwards: if it is moved or deleted, choose it again.",
            "要就地读取游戏文件，NieR 需要访问所有文件的权限，且只会读取你接下来选择的文件夹。\n\n请在设置中打开开关后返回。之后请保持文件夹位置不变：若被移动或删除，请重新选择。");
        put("Open Settings", "打开设置");
        put("App settings", "应用设置");
        put("Open Pod Programs", "打开 Pod Programs");
        put("Open the Archive", "打开档案馆");
        put("Close Pod Programs to deploy again.", "请关闭 Pod Programs 后再部署。");
        put("Close Pod Programs to return to the game.", "请关闭 Pod Programs 以返回游戏。");
        put("Import your game files to get started.", "导入游戏文件即可开始。");
        put("Import the remaining game files to continue.", "导入其余游戏文件后即可继续。");
        put("Your files are ready. Start the server when you want to play.", "文件已就绪。想玩时启动服务器即可。");
        put("Your saves are stored on this phone.", "存档保存在本机。");
        put("Keep the app open until unpacking finishes.", "解包完成前请保持应用打开。");
        put("Keep the source files available until this finishes.", "完成前请保持源文件可用。");
        put("Keep your backup somewhere safe.", "请妥善保存备份。");
        put("Loading game data…", "正在读取游戏数据…");
        put("Preparing tools", "正在准备工具");
        put("Tools ready", "工具已就绪");
        put("Tools startup failed", "工具启动失败");
        put("Opening Pod Programs", "正在打开 Pod Programs");
        put("Pod Programs open", "Pod Programs 已打开");
        put("Closing Pod Programs…", "正在关闭 Pod Programs…");
        put("Opening Pod Programs…", "正在打开 Pod Programs…");
        put("Pod Programs closed. Return to the Bunker.", "Pod Programs 已关闭，请返回地堡。");
        put("Pod Programs stopped. Close and reopen to retry.", "Pod Programs 已停止，请关闭后重新打开再试。");
        put("Unable to open Pod Programs. Close and try again.", "无法打开 Pod Programs，请关闭后重试。");
        put("Operation cancelled", "操作已取消");
        put("Start cancelled", "启动已取消");
        put("Import cancelled", "导入已取消");
        put("Import complete", "导入完成");
        put("Importing files", "正在导入文件");
        put("Importing master data", "正在导入主数据");
        put("Importing save", "正在导入存档");
        put("Import save backup", "导入存档备份");
        put("Import a save backup?", "要导入存档备份吗？");
        put("Import master data", "导入主数据");
        put("Import master data from the ⋮ menu.", "请从 ⋮ 菜单导入主数据。");
        put("SAVE", "保存");
        put("CHANGE", "更改");
        put("CLOSE", "关闭");
        put("Close", "关闭");
        put("Cancel", "取消");
        put("CANCEL", "取消");
        put("Accept", "接受");
        put("Cancel operation", "取消操作");
        put("Unpacking", "正在解包");
        put("Opening the archive…", "正在打开压缩包…");
        put("Reading the folder… ", "正在读取文件夹… ");
        put("Checking the folder…", "正在检查文件夹…");
        put("Finishing import…", "正在完成导入…");
        put("Finishing the current operation and saving progress…", "正在结束当前操作并保存进度…");
        put("Stopping the game…", "正在停止游戏…");
        put(" · estimating time left…", " · 正在估算剩余时间…");
        put("under a minute left", "剩余不到一分钟");
        put(" min left", " 分钟剩余");
        put("Downloading…", "正在下载…");
        put("Downloading ", "正在下载 ");

        // ---- 文件错误 ----
        put("Cannot open the chosen file", "无法打开所选文件");
        put("Cannot open the selected archive", "无法打开所选压缩包");
        put("Cannot open the selected file", "无法打开所选文件");
        put("Cannot open source file", "无法打开源文件");
        put("Cannot open backup destination", "无法打开备份目标位置");
        put("Cannot read the archive", "无法读取压缩包");
        put("Cannot read the selected folder", "无法读取所选文件夹");
        put("Cannot read the selected file", "无法读取所选文件");
        put("Cannot prepare save backup", "无法准备存档备份");
        put("Cannot import the save", "无法导入存档");
        put("Cannot write file", "无法写入文件");
        put("The selected file is empty", "所选文件为空");
        put("Folder nesting is too deep", "文件夹层级过深");
        put("Choose the extracted game files: revisions/0 has no list.bin", "请选择已解压的游戏文件：revisions/0 缺少 list.bin");
        put("Choose the extracted game files: the folder that contains revisions/0", "请选择已解压的游戏文件：包含 revisions/0 的那个文件夹");
        put("These game files use other revisions. Prepare them on a computer with scripts/prepare_assets.py",
            "这些游戏文件使用了其他 revision。请在电脑上用 scripts/prepare_assets.py 处理。");
        put(". Put it back or choose the files again.", "。请放回原处，或重新选择文件。");
        put("Your game files folder is missing: ", "找不到游戏文件文件夹：");

        // ---- 存档与日志 ----
        put("Export save backup", "导出存档备份");
        put("Choose backup", "选择备份");
        put("Export Lunar Tear log", "导出 Lunar Tear 日志");
        put("Lunar Tear log", "Lunar Tear 日志");
        put("Lunar Tear log exported", "Lunar Tear 日志已导出");
        put("Export failed", "导出失败");
        put("Export failed: ", "导出失败：");
        put("Exported.", "已导出。");
        put("Exporting saves", "正在导出存档");
        put("Saves exported", "存档已导出");
        put("Backup saved.", "备份已保存。");
        put("Save imported", "存档已导入");
        put("Save imported. Tap Play to continue with it.", "存档已导入。点「开始」继续。");
        put("No server log yet.", "还没有服务器日志。");
        put("> Stop Lunar Tear to import or export saves.", "> 请先停止 Lunar Tear 再导入或导出存档。");
        put("This replaces the save on this phone with the backup you choose: a ZIP from Export save backup, or a game.db file. Your current save is kept as a safety copy.",
            "这会用你选择的备份替换本机存档：可以是「导出存档备份」生成的 ZIP，也可以是 game.db 文件。当前存档会保留一份安全副本。");
        put("Attach the ZIP when you report a problem. It holds the Lunar Tear log and this phone's model and Android version.",
            "反馈问题时可附上该 ZIP，其中包含 Lunar Tear 日志、手机型号与 Android 版本。");

        // ---- 服务器检查 ----
        put("Check Lunar Tear", "检查 Lunar Tear");
        put("Lunar Tear is reachable", "Lunar Tear 可访问");
        put("Lunar Tear is not running.", "Lunar Tear 未运行。");
        put("Lunar Tear check failed", "Lunar Tear 检查失败");
        put("The game could not reach its server:", "游戏无法连接其服务器：");
        put("Native server unavailable", "原生服务器不可用");
        put("Native server did not respond", "原生服务器无响应");
        put("Unable to load native server: ", "无法加载原生服务器：");
        put("Server check failed: ", "服务器检查失败： ");
        put("Unknown operation", "未知操作");
        put("Port offset ", "端口偏移 ");
        put("· port ", "· 端口 ");
        put("Install the patched game", "安装已打补丁的游戏");
        put("Install the APK patched for 127.0.0.1. The original game APK cannot connect to this server.",
            "请安装已针对 127.0.0.1 打过补丁的 APK。原版游戏 APK 无法连接此服务器。");

        // ---- 更新 ----
        put("Check for updates", "检查更新");
        put("Check for updates: ", "检查更新：");
        put("Allow updates", "允许更新");
        put("UPDATE", "更新");
        put("UPDATE TO ", "更新到 ");
        put("UPDATE TO", "更新到");
        put("WHAT'S NEW", "更新内容");
        put("WEB BUILDER", "网页构建器");
        put("Update cancelled.", "更新已取消。");
        put("Opening the installer…", "正在打开安装程序…");
        put("Stopping Lunar Tear and Pod Programs…", "正在停止 Lunar Tear 与 Pod Programs…");
        put("Pod Programs is still saving. Close it, wait a moment and try again.", "Pod Programs 仍在保存，请关闭后稍等再试。");
        put("The update could not be installed", "无法安装更新");
        put("The update files aren't available (HTTP ", "更新文件不可用（HTTP ");
        put("Can't reach the update server. Check the connection and try again.", "无法连接更新服务器，请检查网络后重试。");
        put("The connection timed out. Try again.", "连接超时，请重试。");
        put("The secure connection to the update server failed. Try again.", "与更新服务器的安全连接失败，请重试。");
        put("Updating needs about 350 MB free. Free some space and try again.", "更新需要约 350 MB 可用空间，请清理后重试。");
        put("). Try again later.", "）。请稍后再试。");
        put("To install the update, allow NieR to install apps. Turn on the switch, then come back and tap Update again.",
            "要安装更新，需允许 NieR 安装应用。请打开开关后返回，再点一次「更新」。");
        put("\n> This update needs the web builder.", "\n> 此更新需要网页构建器。");
        put("\n> You can also rebuild with the web builder.", "\n> 你也可以用网页构建器重新构建。");
        put("\n> Signed with your own key: rebuild with the web builder.", "\n> 使用你自己的密钥签名：请用网页构建器重新构建。");
        put(" is available.", " 已可用。");

        // ---- 档案馆 ----
        put("BUNKER // ARCHIVE", "地堡 // 档案馆");
        put("ARCHIVE", "档案馆");
        put("Archive", "档案馆");
        put("Archive startup failed", "档案馆启动失败");
        put("> Opening the Archive…", "> 正在打开档案馆…");
        put("> The Archive could not start: ", "> 档案馆无法启动：");
        put("> Unable to open the Archive. Close and try again.", "> 无法打开档案馆，请关闭后重试。");
        put("Save PNG", "保存 PNG");
        put("Picture saved", "图片已保存");
        put("The picture could not be saved", "无法保存图片");

        // ---- 显示 ----
        put("BUNKER // POD 042", "地堡 // POD 042");
        put("POD PROGRAMS", "POD PROGRAMS");
        put("Pod Programs", "Pod Programs");
        put("Display", "显示");
        put("Display: ", "显示：");
        put("System", "跟随系统");
        put("System (follow the phone)", "跟随系统（与手机一致）");
        put("Light", "浅色");
        put("Dark", "深色");
        put("END OF TRANSMISSION // GLORY TO MANKIND", "通信结束 // 愿人类荣光永存");
        put("OPERATOR LINK // STANDING BY", "操作员链路 // 待命");
        put("STANDING BY", "待命");
        put("Version ", "版本 ");
        put("Bunker ", "Bunker ");
        put("Bunker", "Bunker");

        // ---- 帮助正文 ----
        put("This is the Bunker. Lunar Tear is the game's server, running on this phone.\n\nChoose the game files once: the resource dump's .7z, or an extracted folder to copy or use in place. Master data is already included. When your files are ready, Lunar Tear starts and Deploy opens the game.\n\nTap the Lunar Tear notification to return here. Stop Lunar Tear from ⋮ before changing files or exporting saves. Export a backup before uninstalling or clearing app storage. Import save backup restores one, from this phone or another Android phone. Pod Programs edits your save and chooses events.\n\nIf Samsung pauses Lunar Tear, set Battery usage to Unrestricted in App settings.",
            "这里是地堡。Lunar Tear 是游戏的服务器，运行在这台手机上。\n\n只需选择一次游戏文件：资源包的 .7z，或已解压的文件夹（复制进应用或就地使用）。主数据已内置。文件就绪后，Lunar Tear 会启动，「部署」随即打开游戏。\n\n点 Lunar Tear 通知可回到这里。更换文件或导出存档前，请先从 ⋮ 停止 Lunar Tear。卸载或清除应用数据前请先导出备份。「导入存档备份」可从本机或其他 Android 手机恢复存档。Pod Programs 可编辑存档并选择活动。\n\n如果三星系统暂停了 Lunar Tear，请在应用设置的「电池用量」中选择「不受限制」。");
        put("\nOffline NieR Re[in]carnation, all in one app.\nCreated by veritr1x · github.com/veritr1x/bunker\n\nCREDITS\nLunar Tear by Walter-Sparrow: the offline server.\nMIT License · Copyright 2026 Ilya Groshev.\nLunar Scripts by Walter-Sparrow: APK and master data patches.\nLunar Base by NMeliksah: the save editors.\nMasterdata Patcher by NavHobbyDev: the content patcher.\nthree.js: the Archive's 3D viewer.\nChaquopy: Python on Android.\n\nNieR Re[in]carnation © SQUARE ENIX. Bunker is a fan project, not affiliated with Square Enix.",
            "\n离线版 NieR Re[in]carnation，集成于一个应用。\n作者 veritr1x · github.com/veritr1x/bunker\n\n致谢\nLunar Tear（Walter-Sparrow）：离线服务器。MIT 许可证 · 版权所有 2026 Ilya Groshev。\nLunar Scripts（Walter-Sparrow）：APK 与主数据补丁。\nLunar Base（NMeliksah）：存档编辑器。\nMasterdata Patcher（NavHobbyDev）：内容修补器。\nthree.js：档案馆的 3D 查看器。\nChaquopy：Android 上的 Python。\n\nNieR Re[in]carnation © SQUARE ENIX。Bunker 为同人项目，与 SQUARE ENIX 无关。");
        put("Open GitHub", "打开 GitHub");

        // ---- 单位与格式 ----
        put("Lunar Tear is up. The game connects to it on this device; no network is needed.",
            "Lunar Tear 已就绪。游戏在本机连接它，无需网络。");
        put("%d min left", "%d 分钟剩余");
        put("%.1f MB", "%.1f MB");
        put("%d KB", "%d KB");
        put(" about ", " 约 ");
        put(" about", " 约");
        put("none yet", "暂无");
        put("Data", "数据");
        put("Cookie", "Cookie");
        put("Downloading…", "正在下载…");
    }
}
