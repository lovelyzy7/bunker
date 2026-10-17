// Page logic: collect the files, run the build in a worker, offer the result.
const $ = (id) => document.getElementById(id);
const worker = new Worker("worker.js");
let url = null;
let building = false;  // One build at a time, however fast the button is pressed.

// The Bunker version this site builds (version.json, written by build_site.py).
fetch("version.json").then((r) => r.ok ? r.json() : null).then((v) => {
  if (v && v.version) $("bunker-version").textContent = "BUILDS BUNKER " + v.version;
}).catch(() => {});

const platform = () => document.querySelector("input[name=platform]:checked").value;

function update() {
  const ios = platform() === "ios";
  $("game-help").textContent = tr(ios ? "Your decrypted 3.7.1 game IPA." : "The original 3.7.1 ARM64 game APK.");
  $("game").accept = ios ? ".ipa" : ".apk";
  $("build").disabled = !($("game").files[0] && $("master").files[0]);
  for (const id of ["game", "master"]) {
    const file = $(id).files[0], chip = $(id + "-name");
    chip.textContent = file ? `${file.name} · ${Math.max(1, Math.round(file.size / 1048576))} MB` : tr("NOT CHOSEN");
    chip.classList.toggle("ok", !!file);
  }
}

function log(line) {
  const box = $("log");
  box.textContent += line + "\n";
  box.scrollTop = box.scrollHeight;
}

document.querySelectorAll("input[name=platform]").forEach((r) => r.addEventListener("change", update));
$("game").addEventListener("change", update);
$("master").addEventListener("change", update);

$("build").addEventListener("click", () => {
  if (building) return;
  const game = $("game").files[0], master = $("master").files[0];
  if (!game || !master) { log(tr("Choose the game file and the master data first.")); return; }
  const expected = platform() === "ios" ? ".ipa" : ".apk";
  if (!game.name.toLowerCase().endsWith(expected)) { log(`Choose the game ${expected} file.`); return; }
  if (game.name === master.name) { log(tr("Choose two different files.")); return; }
  const portOffset = Number($("port-offset").value || 0);
  if (!Number.isInteger(portOffset) || portOffset < 0 || portOffset > 57455) { log(tr("The port offset must be a whole number from 0 to 57455.")); return; }
  building = true;
  $("build").disabled = true;
  $("result").style.display = "none";
  $("log").textContent = "";
  if (url) URL.revokeObjectURL(url);
  worker.postMessage({ platform: platform(), game, master, portOffset });
});

worker.onmessage = ({ data }) => {
  if (data.type === "log") log(data.value);
  if (data.type === "error") { log(tr("Build failed: ") + data.value); building = false; $("build").disabled = false; }
  if (data.type === "done") {
    const { name, bytes } = data.value;
    url = URL.createObjectURL(new Blob([bytes], { type: "application/octet-stream" }));
    $("download").href = url;
    $("download").download = name;
    $("download").textContent = tr(`Download ${name} (${Math.round(bytes.length / 1048576)} MB)`);
    $("sign-android").hidden = name.endsWith(".ipa");
    $("sign-ios").hidden = !name.endsWith(".ipa");
    $("result").style.display = "block";
    building = false;
    $("build").disabled = false;
    log(tr("Done."));
  }
};


// ---- 中文界面（默认中文，右上角切换）-------------------------------------
// 页面以英文撰写；这里按「英文原文 → 中文」替换文本、placeholder 与 aria-label，
// 并把动态文案（日志、下载按钮）包一层。文件名为玩家数据，保持原样。
const ZH = {
  "Bunker · Lunar Tear builder": "Bunker · Lunar Tear 构建器",
  "The original master data,": "原版主数据，",
  "NOT CHOSEN": "未选择",
  "The game talks to its server on this device through ports 8003, 8080 and 3000. If another app already uses one of them, the launcher says so. An offset moves all three, for example 30000 gives 38003, 38080 and 33000. Leave it at 0 unless you need it, and use the same offset for updates.": "游戏在本机通过 8003、8080、3000 三个端口连接服务器。如果其中某个端口已被其他应用占用，启动器会提示。设置偏移可一次性移动这三个端口，例如 30000 会得到 38003、38080、33000。除非确有需要，请保持 0，并在更新时沿用同一偏移。",
  " password and alias ": "，密码与别名 ",
  ") to sign your own builds the same way. The key is public: to keep anyone else's build from installing over yours, sign with a key of your own instead.": "）以便用同样方式签名你自己的构建。该密钥是公开的：若不想让别人构建的包覆盖你的，请改用自己的密钥。",
  "The IPA is unsigned. Install it with Sideloadly or AltStore and your Apple ID, or sign it with your own certificate. Use the same bundle ID for updates to keep your saves. The same IPA runs on a Mac with Apple silicon when signed by your Apple developer team for that Mac; build it with a port offset (for example 30000) and open the launcher with ⌘B. See": "IPA 未签名。请用 Sideloadly 或 AltStore 配合你的 Apple ID 安装，或用自己的证书签名。更新时请使用相同的 bundle ID 以保留存档。用你的 Apple 开发者团队为该 Mac 签名后，同一个 IPA 也可在 Apple 芯片的 Mac 上运行；请使用端口偏移（例如 30000）构建，并用 ⌘B 打开启动器。详见",
  "Play on a Mac": "在 Mac 上运行",
  "Then copy the resource dump's": "然后，将资源包的",
  "to the device and choose it in the Bunker; the app unpacks only the files the game uses. An extracted folder works too, as described in the": "复制到设备，并在「地堡」中选择它；应用只会解出游戏实际使用的文件。已解压的文件夹同样可用，详见",
  "guide": "指南",
  ". The Android build made here leaves out the in-game Facebook account link; offline play, Pod Programs and save backups work.": "。此处构建的 Android 版本不含游戏内的 Facebook 账号绑定；离线游玩、Pod Programs 与存档备份均可使用。",
  "the game server, by Walter-Sparrow": "游戏服务器，作者 Walter-Sparrow",
  "game and master-data patching, by Walter-Sparrow": "游戏与主数据补丁，作者 Walter-Sparrow",
  "the save editors in Pod Programs, by NMeliksah": "Pod Programs 的存档编辑器，作者 NMeliksah",
  "the content patcher, by NavHobbyDev": "内容修补器，作者 NavHobbyDev",
  "ANDROID": "ANDROID",
  "IPHONE / IPAD": "IPHONE / IPAD",
  "IPA": "IPA",
  "APK · arm64": "APK · arm64",
  "BUNKER": "BUNKER",
  "LUNAR TEAR // BUILD TERMINAL": "LUNAR TEAR // 构建终端",
  "BUILD": "构建",
  "GUIDE": "指南",
  "TROUBLESHOOTING": "疑难解答",
  "SOURCE ↗": "源码 ↗",
  "Build the offline game": "构建离线游戏",
  "For Android or iPhone/iPad, from your own files. Everything runs in this browser; your files are never uploaded.":
    "使用你自己的文件，为 Android 或 iPhone/iPad 构建。全部在浏览器内完成，文件不会被上传。",
  "01 Platform": "01 平台",
  "02 Your files": "02 你的文件",
  "03 Build": "03 构建",
  "04 Install": "04 安装",
  "ANDROID": "ANDROID",
  "APK · arm64": "APK · arm64",
  "IPHONE / IPAD": "IPHONE / IPAD",
  "IPA": "IPA",
  "GAME": "游戏",
  "MASTER DATA": "主数据",
  "NOT CHOSEN": "未选择",
  "CHOOSE": "选择",
  "The original 3.7.1 ARM64 game APK.": "原版 3.7.1 ARM64 游戏 APK。",
  "Your decrypted 3.7.1 game IPA.": "已解密的 3.7.1 游戏 IPA。",
  "Takes a few minutes and needs about 2 GB of free memory. A desktop browser works best.":
    "需要几分钟，并占用约 2 GB 内存。建议使用桌面浏览器。",
  "EXPERIMENTAL :: PORT OFFSET": "实验性 :: 端口偏移",
  "Offset": "偏移",
  "BUILD ▶": "开始构建 ▶",
  "Download": "下载",
  "The APK is signed and ready to install. Every APK built on this page is signed with the same public Bunker key, so a newer build installs over an older one and keeps your saves.":
    "APK 已签名，可直接安装。本页构建的每个 APK 都用同一把公开的 Bunker 密钥签名，因此新版本可覆盖旧版本安装并保留存档。",
  "Download the key": "下载密钥",
  "to sign your own builds the same way. The key is public: to keep anyone else's build from installing over yours, sign with a key of your own instead.":
    "以便用同样方式签名你自己的构建。该密钥是公开的：若不想让别人构建的包覆盖你的，请改用自己的密钥。",
  "The IPA is unsigned. Install it with Sideloadly or AltStore and your Apple ID, or sign it with your own certificate.":
    "IPA 未签名。请用 Sideloadly 或 AltStore 配合你的 Apple ID 安装，或用自己的证书签名。",
  "Build failed: ": "构建失败：",
  "Choose the game file and the master data first.": "请先选择游戏文件与主数据。",
  "Choose two different files.": "请选择两个不同的文件。",
  "The port offset must be a whole number from 0 to 57455.": "端口偏移必须是 0 到 57455 之间的整数。",
  "Done.": "完成。",
  "Downloading": "正在下载",
  "Build": "构建",
  "END OF TRANSMISSION // GLORY TO MANKIND": "通信结束 // 愿人类荣光永存",
  "OPERATOR LINK // STANDING BY": "操作员链路 // 待命",
  "Source:": "源码：",
  "Built with": "使用以下项目",
};

const ZH_PATTERNS = [
  [/^BUILDS BUNKER (.+)$/, "Bunker 版本 $1"],
  [/^Download (.+) \((\d+) MB\)$/, "下载 $1（$2 MB）"],
];

const SKIP_IDS = new Set(["game-name", "master-name"]);   // 玩家选择的文件名原样显示
const LANG_KEY = "bunker_lang";
const originals = new WeakMap();

/** 动态文案（日志、下载按钮）也走词典；英文环境原样返回。 */
function tr(text) {
  if (currentLang() !== "zh") return text;
  return zhText(text) ?? text;
}

function zhText(text) {
  const t = text.replace(/\s+/g, " ").trim();
  if (ZH[t] !== undefined) return ZH[t];
  for (const [re, out] of ZH_PATTERNS) {
    const m = t.match(re);
    if (m) return out.replace(/\$(\d)/g, (_, n) => m[Number(n)] ?? "");
  }
  return null;
}

function translatePage(on) {
  const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT, {
    acceptNode(node) {
      const p = node.parentElement;
      if (!p || ["SCRIPT", "STYLE", "CODE"].includes(p.tagName)) return NodeFilter.FILTER_REJECT;
      const chip = p.closest("#game-name, #master-name");
      if (chip && /[·.]/.test(node.nodeValue)) return NodeFilter.FILTER_REJECT;  // 文件名原样
      return on && zhText(node.nodeValue) !== null ? NodeFilter.FILTER_ACCEPT : NodeFilter.FILTER_SKIP;
    }
  });
  const nodes = [];
  while (walker.nextNode()) nodes.push(walker.currentNode);
  for (const node of nodes) {
    if (on) {
      if (!originals.has(node)) originals.set(node, node.nodeValue);
      const raw = node.nodeValue;
      const lead = raw.match(/^\s*/)[0], trail = raw.match(/\s*$/)[0];
      node.nodeValue = lead + zhText(raw) + trail;
    } else if (originals.has(node)) {
      node.nodeValue = originals.get(node);
    }
  }
  document.querySelectorAll("[aria-label],[placeholder],[title]").forEach(el => {
    for (const attr of ["aria-label", "placeholder", "title"]) {
      const value = el.getAttribute(attr);
      if (!value) continue;
      const key = "zh:" + attr;
      if (on) {
        const zh = zhText(value);
        if (zh === null) continue;
        if (!el.dataset[key]) el.dataset[key] = value;
        el.setAttribute(attr, zh);
      } else if (el.dataset[key]) {
        el.setAttribute(attr, el.dataset[key]);
        delete el.dataset[key];
      }
    }
  });
}

function currentLang() {
  try { return localStorage.getItem(LANG_KEY) === "en" ? "en" : "zh"; } catch (e) { return "zh"; }
}

function setLang(lang) {
  try { localStorage.setItem(LANG_KEY, lang); } catch (e) {}
  translatePage(lang === "zh");
  const toggle = document.getElementById("lang");
  if (toggle) toggle.textContent = lang === "zh" ? "EN" : "中文";
  // 动态文案（日志、下载按钮）在下次写入时按当前语言生成
  if (typeof update === "function") update();
}

// app.js 在 body 末尾加载，此时上面的 DOM 已就绪，直接执行即可（不依赖事件）。
(function () {
  const nav = document.querySelector(".top nav");
  if (nav && !document.getElementById("lang")) {
    const toggle = document.createElement("a");
    toggle.id = "lang";
    toggle.href = "#";
    toggle.className = "boxed";
    toggle.addEventListener("click", (event) => {
      event.preventDefault();
      setLang(currentLang() === "zh" ? "en" : "zh");
    });
    nav.appendChild(toggle);
  }
  setLang(currentLang());
})();

// 首次渲染（词典已就绪）。
update();
