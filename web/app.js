// Page logic: collect the files, run the build in a worker, offer the result.
const $ = (id) => document.getElementById(id);
let worker = new Worker("worker.js");
let url = null;
let expected = null;   // { name, size } of the finished product, for the download self-check
let building = false;  // One build at a time, however fast the button is pressed.

// The Bunker version this site builds (version.json, written by build_site.py).
fetch("version.json").then((r) => r.ok ? r.json() : null).then((v) => {
  if (v && v.version) {
    $("bunker-version").textContent = tr("BUILDS BUNKER " + v.version);
    keepOffline(v.build ? `${v.version}-${v.build}` : v.version);
  }
}).catch(() => {});

/** Cache the 35 MB of runtime and launcher, so a second build is a local read. */
function keepOffline(version) {
  if (!("serviceWorker" in navigator)) return;
  // A new release links a different sw.js, which installs a new cache and
  // drops the old one; outside https/localhost the browser just refuses.
  navigator.serviceWorker.register(`sw.js?v=${encodeURIComponent(version)}`).catch(() => {});
}

// The releases this page builds, keyed by SHA-256 (regions.json, same table as
// android/tools/region.py). Only used to name the picked file; the build still
// checks it in Python.
let RELEASES = null;
fetch("regions.json").then((r) => r.ok ? r.json() : null).then((v) => {
  RELEASES = v && typeof v === "object" ? v : null;
  update();
}).catch(() => {});

// Where the launcher may come from (mirrors.json, written by build_site.py).
let MIRRORS = null;
fetch("mirrors.json").then((r) => r.ok ? r.json() : null).then((v) => {
  MIRRORS = v && typeof v === "object" ? v : null;
  syncSource();
}).catch(() => {});

// A phone has to read the whole APK to hash it, so this runs once per file.
const checksums = new Map();  // name/size/mtime -> {state, region}

function fileKey(file) {
  return `${file.name}/${file.size}/${file.lastModified}`;
}

async function releaseOf(file) {
  if (!RELEASES) return {state: "unavailable"};
  if (!crypto.subtle || !crypto.subtle.digest) return {state: "unavailable"};
  // Always hash the file: matching by size alone flagged legitimate dumps of a
  // different build as “not the original” without ever looking at their bytes,
  // and it never told the user what was expected. A size hit is only a hint.
  let hex = null;
  try {
    const digest = await crypto.subtle.digest("SHA-256", await file.arrayBuffer());
    hex = [...new Uint8Array(digest)].map((b) => b.toString(16).padStart(2, "0")).join("");
  } catch (error) {
    return {state: "unavailable"};  // Out of memory, or a file we cannot read.
  }
  const entry = Object.entries(RELEASES).find(([, known]) => known.sha256 === hex);
  const shown = {size: file.size, sha: hex};
  if (entry) return {state: "ok", region: entry[0], shown};
  // Not any known release: report both sides so the difference is visible.
  const near = Object.entries(RELEASES).find(([, known]) => known.size === file.size);
  return {
    state: "bad",
    region: near ? near[0] : null,
    shown,
    expected: Object.fromEntries(Object.entries(RELEASES).map(([k, v]) => [k, {size: v.size, sha: v.sha256}])),
  };
}

// The one line under the game description: which release this APK is.
function showRelease(result) {
  const box = $("game-region");
  box.className = "region";
  if (result.state === "ok") {
    box.hidden = false;
    box.classList.add("ok");
    box.textContent = `\u2713 ${tr(result.region === "jp" ? "Japan" : "Global")} \u00b7 ${result.region.toUpperCase()}`;
  } else if (result.state === "bad") {
    box.hidden = false;
    box.classList.add("bad");
    const shown = result.shown ? ` \u00b7 ${result.shown.size} B / ${result.shown.sha.slice(0, 12)}\u2026` : "";
    box.textContent = `\u2717 ${tr("Not the original 3.7.1 release")}${shown}`;
    if (result.expected) {
      const exp = Object.entries(result.expected)
        .map(([k, v]) => `${k.toUpperCase()} ${v.size} B / ${v.sha.slice(0, 12)}\u2026`).join(" \u00b7 ");
      box.title = `${tr("The file differs from the original 3.7.1 releases")} \u00b7 ${exp}`;
    }
  } else if (result.state === "checking") {
    box.hidden = false;
    box.textContent = tr("Checking the checksum\u2026");
  } else {
    box.hidden = true;
    box.textContent = "";
  }
}

let releasing = 0;  // Picks can overlap; only the last one may paint.

async function describeGame() {
  const file = $("game").files[0];
  if (!file) { showRelease({state: "none"}); return; }
  const key = fileKey(file), known = checksums.get(key);
  if (known) { showRelease(known); return; }
  const ticket = ++releasing;
  showRelease({state: "checking"});
  const result = await releaseOf(file);
  if (result.state === "ok" || result.state === "bad") checksums.set(key, result);
  const picked = $("game").files[0];
  if (ticket === releasing && picked && fileKey(picked) === key) showRelease(result);
}

// ---- 00 the launcher source -------------------------------------------------
// Proxies that answer a GitHub release download with a CORS header (checked).
// The page offers them as suggestions and the build can fall back to the other.
const PROXIES = ["https://gh-proxy.com/", "https://gh-proxy.org/"];

const SOURCE_KEY = "bunker_source";
const PROXY_KEY = "bunker_proxy";

function sourceMode() {
  const picked = document.querySelector('input[name="launcher-source"]:checked');
  return picked ? picked.value : "site";
}

/** A proxy base (https://gh-proxy.com/), a full url, or a template with {url}. */
function resolveVia(text, target) {
  if (!text) return null;
  if (text.includes("{url}")) return target ? text.replace("{url}", target) : null;
  if (text.endsWith("/") || /^https?:\/\/[^/]+$/i.test(text)) return target ? text + target : null;
  return /^https?:\/\/\S+$/i.test(text) ? text : null;
}

function proxyText() {
  return ($("proxy-url").value || "").trim();
}

/** Proxy prefix/templates for every prebuilt file — in proxy mode only. */
function proxyTemplates() {
  if (sourceMode() !== "proxy") return [];
  return [proxyText(), ...PROXIES].filter(Boolean);
}

function launcherUrl() {
  return resolveVia(proxyText(), (MIRRORS && MIRRORS.github) || "");
}

/** The Mod Menu only makes sense as a prefix/template; a launcher url says nothing about it. */
function modmenuUrl() {
  const target = (MIRRORS && MIRRORS.modmenuGithub) || "";
  const text = proxyText();
  if (!target || !text) return null;
  if (text.includes("{url}")) return text.replace("{url}", target);
  if (text.endsWith("/") || /^https?:\/\/[^/]+$/i.test(text)) return text + target;
  return null;
}

/** Mainland China on the first visit: the GitHub proxy is the default there. */
function mainlandChina() {
  try {
    const zone = Intl.DateTimeFormat().resolvedOptions().timeZone || "";
    return ["Asia/Shanghai", "Asia/Chongqing", "Asia/Harbin", "Asia/Urumqi", "Asia/Kashgar", "PRC"].includes(zone);
  } catch (error) {
    return false;
  }
}

function updateBuildEnabled() {
  const mode = sourceMode();
  const ready = !!($("game").files[0] && $("master").files[0])
    && (mode !== "proxy" || !!launcherUrl());
  $("build").disabled = building || !ready;
}

/** Two exclusive sources: the proxy line is greyed out until picked. */
function syncSource() {
  const mode = sourceMode();
  $("proxy-line").classList.toggle("off", mode !== "proxy");
  $("proxy-url").disabled = mode !== "proxy";

  const hint = $("proxy-hint");
  hint.classList.remove("bad");
  const url = mode === "proxy" ? launcherUrl() : null;
  if (mode !== "proxy") hint.textContent = "";
  else if (!$("proxy-url").value.trim()) hint.textContent = tr("Paste a proxy address, such as https://gh-proxy.com/");
  else if (!url) { hint.textContent = tr("That is not an http(s) address."); hint.classList.add("bad"); }
  else hint.textContent = `${tr("The launcher will come from")} ${url}`;

  try {
    localStorage.setItem(SOURCE_KEY, mode);
    localStorage.setItem(PROXY_KEY, $("proxy-url").value || "");
  } catch (error) { /* private mode */ }
  updateBuildEnabled();
}

function resetStages() {
  for (const li of document.querySelectorAll("#steps li")) li.className = "";
  $("meter").style.width = "0%";
}

function cancelBuild() {
  if (!building) return;
  building = false;
  $("cancel").hidden = true;
  // Terminating the worker is the only way to stop Python mid-step: its long
  // calls do not yield to JavaScript. The runtime comes back from the cache
  // (or the service worker) on the next build.
  restartWorker();
  resetStages();
  $("progress").hidden = true;
  $("cancel").hidden = true;
  log(tr("Build cancelled."));
  updateBuildEnabled();
}

$("cancel").addEventListener("click", cancelBuild);

$("copy-log").addEventListener("click", async () => {
  const text = logLines.map((line) => line.text).join("\n");
  try {
    await navigator.clipboard.writeText(text);
    $("copy-log").textContent = tr("COPIED");
    setTimeout(() => { $("copy-log").textContent = tr("COPY LOG"); }, 1500);
  } catch (error) {
    // No clipboard permission: select the log so a long-press can copy it.
    const range = document.createRange();
    range.selectNodeContents($("log"));
    const selection = getSelection();
    selection.removeAllRanges();
    selection.addRange(range);
  }
});

$("only-errors").addEventListener("change", () => {
  try { localStorage.setItem(CHECKS_KEY, JSON.stringify(checks())); } catch (error) { /* private mode */ }
  renderLog();
});

// The three switches survive a reload.
const CHECKS_KEY = "bunker_checks";

function checks() {
  return { skip: $("skip-check").checked, menu: $("mod-menu").checked, offset: $("port-offset").value || "0",
           errors: $("only-errors").checked };
}

function restoreChecks() {
  try {
    const saved = JSON.parse(localStorage.getItem(CHECKS_KEY) || "null");
    if (!saved) return;   // No save yet: the page's checked defaults stay.
    // skip / menu default to true: a save that predates the key (or omits it)
    // leaves the box checked instead of silently clearing it.
    $("skip-check").checked = saved.skip ?? true;
    $("mod-menu").checked = saved.menu ?? true;
    $("port-offset").value = saved.offset || "0";
    $("only-errors").checked = !!saved.errors;
  } catch (error) { /* private mode */ }
}

function saveChecks() {
  try { localStorage.setItem(CHECKS_KEY, JSON.stringify(checks())); } catch (error) { /* private mode */ }
}

for (const id of ["skip-check", "mod-menu", "port-offset"]) {
  $(id).addEventListener("change", () => { saveChecks(); markSkipped(); });
}

function update() {
  $("game-help").textContent = tr("The original 3.7.1 ARM64 game APK (JP or global).");
  $("game").accept = ".apk";
  // Without an accept, Chrome on Android opens the photo picker and a .bin.e
  // cannot be chosen at all; a non-media type gets the file browser instead.
  $("master").accept = "application/octet-stream";
  updateBuildEnabled();
  for (const id of ["game", "master"]) {
    const file = $(id).files[0], chip = $(id + "-name");
    chip.textContent = file ? `${file.name} · ${Math.max(1, Math.round(file.size / 1048576))} MB` : tr("NOT CHOSEN");
    chip.classList.toggle("ok", !!file);
    // A second pick is a replacement, so say so once a file is there.
    const label = $(id).closest(".pick");
    if (label && label.firstChild && label.firstChild.nodeType === Node.TEXT_NODE) {
      label.firstChild.nodeValue = file ? tr("CHANGE") : tr("CHOOSE");
    }
  }
  describeGame();
  syncSource();
  if ($("game").files[0] || $("master").files[0]) warmUp();
}

// ---- progress ---------------------------------------------------------------
// The worker logs the build steps as it reaches them; each line that starts a
// step moves the chips and the bar. Percentages are what each step costs.
const STAGES = [
  [/^Loading Python|^Python runtime from|^Downloading the/, 0, 3],
  [/^Checking the game APK/, 1, 10],
  [/^Patching the game library/, 2, 36],
  [/^Updating the manifest|^Patching master data|^Mod Menu payload/, 3, 48],
  [/^Writing the APK/, 4, 62],
  [/^Writing the Mod Menu/, 5, 78],
  [/^Signing with the public Bunker key|^Computing the checksum/, 6, 94],
];

/** Mark the steps this build will not do: the skipped check, an unused menu. */
function markSkipped() {
  const unused = { 1: $("skip-check").checked, 5: !$("mod-menu").checked };
  for (const li of document.querySelectorAll("#steps li")) {
    const own = Number(li.dataset.stage);
    if (own in unused) li.classList.toggle("skipped", !!unused[own]);
  }
}

function setStage(stage, percent) {
  const unused = { 1: $("skip-check").checked, 5: !$("mod-menu").checked };
  for (const li of document.querySelectorAll("#steps li")) {
    const own = Number(li.dataset.stage);
    const skipped = !!unused[own];
    li.classList.toggle("skipped", skipped);
    li.classList.toggle("done", own < stage && !skipped);
    li.classList.toggle("on", own === stage && !skipped);
  }
  if (percent !== undefined) $("meter").style.width = percent + "%";
}

/** The build's own log lines, in Chinese when the page is Chinese. */
const LOG_PATTERNS = [
  [/^Downloading the launcher… (\d+)%$/, "正在下载启动器…… $1%"],
  [/^Downloading the Python runtime… (\d+)%$/, "正在下载 Python 运行时…… $1%"],
  [/^Downloading the Python standard library… (\d+)%$/, "正在下载 Python 标准库…… $1%"],
  [/^Downloading the Mod Menu… (\d+)%$/, "正在下载 MOD 菜单…… $1%"],
  [/^Downloading (.+)… (\d+) MB$/, "正在下载 $1…… $2 MB"],
  [/^Loading Python…$/, "正在加载 Python……"],
  [/^Python runtime from (.+)$/, "Python 运行时来自 $1"],
  [/^Checking the game APK and master data…$/, "正在校验游戏 APK 与主数据……"],
  [/^Patching the game library and metadata…$/, "正在改写游戏库与元数据……"],
  [/^Updating the manifest…$/, "正在更新清单……"],
  [/^Patching master data…$/, "正在改写主数据……"],
  [/^Mod Menu payload: (.+)$/, "MOD 菜单内容：$1"],
  [/^Writing the Mod Menu…$/, "正在写入 MOD 菜单……"],
  [/^Finalizing the archive…$/, "正在写入压缩包目录……"],
  [/^  signing (\d+)%…$/, "  正在签名 $1%……"],
  [/^  dex (\d+)\/(\d+) \((\d+) KB\)…$/, "  dex $1/$2（$3 KB）……"],
  [/^  libniermenu\.so \((\d+) MB\)…$/, "  libniermenu.so（$1 MB）……"],
  [/^Downloading Python packages…$/, "正在下载 Python 组件……"],
  [/^Loading the builder sources \((\d+) files\)…$/, "正在加载构建脚本（$1 个文件）……"],
  [/^Python ready\.$/, "Python 已就绪。"],
  [/^Downloading the Python runtime…$/, "正在下载 Python 运行时……"],
  [/^the Python runtime \((\d+) MB\) in ([\d.]+) s \(cached\)$/, "Python 运行时（$1 MB）来自本地缓存"],
  [/^the Python runtime \((\d+) MB\) in ([\d.]+) s$/, "Python 运行时（$1 MB）用时 $2 秒"],
  [/^the Python standard library \((\d+) MB\) in ([\d.]+) s \(cached\)$/, "Python 标准库（$1 MB）来自本地缓存"],
  [/^the Python standard library \((\d+) MB\) in ([\d.]+) s$/, "Python 标准库（$1 MB）用时 $2 秒"],
  [/^Writing the APK…$/, "正在打包 APK……"],
  [/^Signing with the public Bunker key…$/, "正在用公开的 Bunker 密钥签名……"],
  [/^Signed APK ready to install\.$/, "APK 已签名，可以安装。"],
  [/^\s*(\d+)%…$/, "  $1%……"],
  [/^  (.+) \((\d+) MB\)…$/, "  $1（$2 MB）……"],
  [/^the launcher \((\d+) MB\) in ([\d.]+) s \(cached\)$/, "启动器（$1 MB）来自本地缓存"],
  [/^the launcher \((\d+) MB\) in ([\d.]+) s$/, "启动器（$1 MB）用时 $2 秒"],
  [/^the launcher came from (.+)$/, "启动器来自 $1"],
  [/^the Mod Menu came from (.+)$/, "MOD 菜单来自 $1"],
  [/^The proxy did not work; trying this site…$/, "代理不可用，改为从本站下载……"],
  [/^Speed: site (.+)$/, "测速：本站 $1"],
  [/^Speed: proxy (.+)$/, "测速：代理 $1"],
  [/^the Mod Menu \((\d+) MB\) in ([\d.]+) s \(cached\)$/, "MOD 菜单（$1 MB）来自本地缓存"],
  [/^the Mod Menu \((\d+) MB\) in ([\d.]+) s$/, "MOD 菜单（$1 MB）用时 $2 秒"],
  [/^Cannot download the launcher from (.+): (.+)$/, "无法从 $1 下载启动器：$2"],
  [/^Cannot download the Mod Menu from (.+): (.+)$/, "无法从 $1 下载 MOD 菜单：$2"],
  [/^Trying (.+) again…$/, "正在重试 $1……"],
  [/^the (.+) from (.+) does not match the site's checksum$/, "$2 的校验值不一致"],
];

// The reason at the end of a download failure, translated after the line itself.
const LOG_REASONS = [
  [/no data for ([\d.]+) s after (\d+) MB/, "$1 秒没有收到数据（已收 $2 MB）"],
  [/no data for ([\d.]+) s/, "$1 秒没有收到数据"],
  [/no response for ([\d.]+) s/, "$1 秒没有响应"],
  [/Cannot download (.+) \(HTTP (\d+)\)/, "下载失败（HTTP $2：$1）"],
];

// Words that appear inside those lines, after the line itself has been translated.
const LOG_WORDS = [["the launcher", "启动器"], ["the Mod Menu", "MOD 菜单"],
                   ["the Python runtime", "Python 运行时"], ["the Python standard library", "Python 标准库"]];

function logLine(line) {
  if (currentLang() !== "zh") return line;
  const fill = (out, m) => out.replace(/\$(\d)/g, (_, n) => m[Number(n)] ?? "");
  let text = line;
  for (const [re, out] of LOG_PATTERNS) {
    const m = text.match(re);
    if (m) { text = fill(out, m); break; }
  }
  for (const [re, out] of LOG_REASONS) {
    const m = text.match(re);
    if (m) { text = text.replace(re, fill(out, m)); break; }
  }
  for (const [en, zh] of LOG_WORDS) text = text.split(en).join(zh);
  return text;
}

// The log keeps its lines so the error filter and COPY LOG can work on them.
const logLines = [];
const BAD_LINE = /error|failed|cannot|refus|失败|无法|错误/i;

function renderLog() {
  const box = $("log");
  const onlyErrors = $("only-errors").checked;
  box.textContent = logLines.filter((item) => !onlyErrors || item.bad).map((item) => item.text).join("\n")
    + (logLines.length ? "\n" : "");
  box.scrollTop = box.scrollHeight;
}

function log(line) {
  logLines.push({ text: logLine(line), bad: BAD_LINE.test(line) });
  renderLog();
  if (!building) return;   // the warm-up logs too, and it is not a build yet
  for (const [re, stage, percent] of STAGES) {
    if (re.test(line)) { setStage(stage, percent); break; }
  }
}

// ---- failures ---------------------------------------------------------------
// Every known failure says what went wrong and what to do about it; anything
// else is shown raw, because a precise error is better than a vague apology.
const FAILURES = [
  [/SHA-256 does not match.*game|The game APK is not the original/,
    ["这不是原版 3.7.1 游戏包", "请使用官方 3.7.1 的日服或全球服 APK。若你确信文件正确（例如从已安装应用导出的拆分包），可在「进阶选项」里勾选「忽略文件校验」。注意：用不同构建的字节强建会把补丁偏移写到错误位置，成品 APK 可能已损坏、无法安装。"],
    ["This is not the original 3.7.1 game", "Use the official 3.7.1 JP or global APK. If you are sure the file is right (a split APK exported from an installed app, for example), tick \"Build even if the files do not match\" under advanced options. Building with bytes from a different build applies its patch offsets to the wrong places, and the finished APK may be corrupt and refuse to install."]],
  [/The master data is not the original/,
    ["主数据不是原版文件", "请使用 20240404193219.bin.e 原文件（约 7.4 MB），未被内容修补器改过的那个。"],
    ["The master data is not the original", "Use the untouched 20240404193219.bin.e (about 7.4 MB), not one a content patcher has rewritten."]],
  [/Not the ARM64 game APK/,
    ["这个 APK 不是游戏本体", "请选择 64 位（arm64-v8a）的游戏原始 APK，而不是启动器、补丁包或存档。"],
    ["This APK is not the game itself", "Choose the original arm64-v8a game APK, not a launcher, patch or save file."]],
  [/Not a game this build accepts/,
    ["不是本页支持的版本", "只支持 3.7.1 的日服或全球服。"],
    ["Not a release this page builds", "Only the 3.7.1 JP and global releases are supported."]],
  [/Not the 日服 \(JP\) game APK/,
    ["日服 APK 不完整", "文件里缺少日服专用的网络配置，请换一个未修改的原版 APK。"],
    ["The JP APK is incomplete", "Its JP network configuration is missing; use an untouched original APK."]],
  [/BadZipFile|not a ZIP|Bad magic number|File is not a zip/,
    ["文件已损坏或不完整", "重新下载或重新复制文件后再试。"],
    ["The file is damaged or incomplete", "Download or copy it again and retry."]],
  [/FileReaderSync|readAsArrayBuffer/,
    ["浏览器读不到这个文件", "请用页面上的「选择」按钮重新挑选文件。手机上通过其他方式塞进文件框的文件，浏览器无权读取。"],
    ["The browser cannot read that file", "Pick it again with the page's CHOOSE button; a file put into the input by script is not readable on Android."]],
  [/does not match the site's checksum/,
    ["站点文件校验失败", "下载到的启动器与站点公布的校验值不一致，已停止构建。请刷新页面重试；若反复出现，说明这个下载来源的内容可能被替换了，请不要继续。"],
    ["A site file did not match its checksum", "The launcher that was downloaded does not match the checksum this site publishes, so the build stopped. Reload and retry; if it keeps happening, that source may be serving altered bytes, so do not continue."]],
  [/stopped responding|suspended the page|The build worker stopped/,
    ["构建卡住了", "浏览器在三分钟内没有收到任何进度，已停止这次构建。请重试；若反复出现，可能是网络卡住或手机内存不足（关掉其他标签页，或改用桌面浏览器）。"],
    ["The build got stuck", "Nothing came back for three minutes, so this build was stopped. Try again; if it keeps happening the network may be stalled or the phone may be out of memory (close other tabs, or use a desktop browser)."]],
  [/Cannot download/,
    ["站点文件下载失败", "刷新页面重试；如果一直失败，可能是网络拦截了 cdn.jsdelivr.net。"],
    ["A site file could not be downloaded", "Reload the page. If it keeps failing, your network may block cdn.jsdelivr.net."]],
  [/memory|MemoryError|Cannot enlarge|RangeError|out of memory/i,
    ["浏览器内存不足", "关闭其他标签页，或改用桌面浏览器。手机上构建 300 MB 的 APK 容易超出浏览器的内存上限。"],
    ["The browser ran out of memory", "Close other tabs, or use a desktop browser; a phone often cannot hold a 300 MB APK build."]],
  [/Port offset/,
    ["端口偏移无效", "把端口偏移改回 0。"],
    ["The port offset is invalid", "Set the port offset back to 0."]],
];

function fail(raw) {
  const [zh, en] = (FAILURES.find(([re]) => re.test(raw)) || [null,
    ["构建失败", "请把下面的原始错误发到项目的 issue。"],
    ["The build failed", "Please report the raw error below in the project's issues."]]).slice(1);
  const [title, hint] = currentLang() === "zh" ? zh : en;
  $("fail-title").textContent = title;
  $("fail-hint").textContent = hint;
  $("fail-raw").textContent = raw;
  $("failure").hidden = false;
  $("failure").scrollIntoView({ block: "center", behavior: "smooth" });
}

const SOURCE_LABEL = { site: "this site", proxy: "the GitHub proxy" };

function regionName(info) {
  if (info.region === "jp") return `${tr("Japan")} (JP)`;
  if (info.region === "en") return `${tr("Global")} (EN)`;
  return info.name || "—";
}

function fillResult(value) {
  const info = value.info || {};
  $("built-version").textContent = info.version || "—";
  $("built-region").textContent = regionName(info);
  $("built-menu").textContent = info.modMenu ? tr("included") : tr("not included");
  $("built-size").textContent = `${(value.blob.size / 1048576).toFixed(0)} MB`;
  $("built-sha").textContent = info.sha256 || "—";
  $("built-source").textContent = tr(SOURCE_LABEL[info.source] || "site");
}

let runtimeReady = false;
let warmTimer = null, warmed = false;

/** Start Pyodide and the 25 MB launcher while the reader is still choosing files. */
function warmTarget() {
  const mode = sourceMode();
  if (mode === "proxy") return launcherUrl() || "proxy";
  return "site";
}

function warmUp() {
  const target = warmTarget();
  if (warmed === target) return;
  clearTimeout(warmTimer);
  warmTimer = setTimeout(() => {
    warmed = target;
    log(tr("Loading the runtime and the launcher in the background…"));
    worker.postMessage({
      type: "preload",
      launcherUrl: target === "site" ? null : target,
      proxyTemplates: proxyTemplates(),
    });
  }, 600);
}

$("game").addEventListener("change", update);
$("master").addEventListener("change", update);

// The download self-check: a download that died halfway leaves a "pending"
// MediaStore item, and the installer answers “There was a problem parsing the
// package” for it. Picking the saved file back compares its size with the
// product's, so “corrupt” becomes “incomplete — download again” in one step.
const verifyFile = $("verify-file");
if (verifyFile) verifyFile.addEventListener("change", async () => {
  const file = verifyFile.files[0], out = $("verify-result");
  if (!file || !expected) return;
  if (file.size !== expected.size) {
    out.textContent = `\u2717 ${tr("Incomplete download")} (${file.size} / ${expected.size} B) \u00b7 ${tr("Please download again.")}`;
    return;
  }
  out.textContent = `\u2713 ${tr("Size matches")} (${file.size} B)`;
  try {
    const digest = await crypto.subtle.digest("SHA-256", await file.arrayBuffer());
    const hex = [...new Uint8Array(digest)].map((b) => b.toString(16).padStart(2, "0")).join("");
    out.textContent += ` \u00b7 ${hex.slice(0, 16)}\u2026`;
  } catch (error) { /* out of memory on a phone: the size check already passed */ }
});
$("proxy-url").addEventListener("input", () => { syncSource(); warmUp(); });
for (const radio of document.querySelectorAll('input[name="launcher-source"]')) {
  radio.addEventListener("change", () => { syncSource(); warmUp(); });
}

$("build").addEventListener("click", () => {
  if (building) return;
  const game = $("game").files[0], master = $("master").files[0];
  if (!game || !master) { log(tr("Choose the game file and the master data first.")); return; }
  if (!game.name.toLowerCase().endsWith(".apk")) { log(tr("Choose the game .apk file.")); return; }
  if (game.name === master.name) { log(tr("Choose two different files.")); return; }
  const mode = sourceMode();
  const launcherURL = mode === "proxy" ? launcherUrl() : null;
  const modmenuURL = mode === "proxy" ? modmenuUrl() : null;
  const portOffset = Number($("port-offset").value || 0);
  if (!Number.isInteger(portOffset) || portOffset < 0 || portOffset > 57455) { log(tr("The port offset must be a whole number from 0 to 57455.")); return; }
  building = true;
  $("build").disabled = true;
  $("cancel").hidden = false;
  setStage(0, 1);
  if (runtimeReady) setStage(1, 10);   // the warm-up already loaded it
  if ($("skip-check").checked) log(tr("Skipping the file check."));
  $("result").style.display = "none";
  $("failure").hidden = true;
  $("progress").hidden = false;
  logLines.length = 0;
  renderLog();
  setStage(0, 2);
  if (url) { URL.revokeObjectURL(url); url = null; }
  worker.postMessage({ game, master, portOffset, modMenu: !!document.getElementById("mod-menu").checked,
                       verify: !$("skip-check").checked, launcherUrl: launcherURL,
                       modmenuUrl: modmenuURL, proxies: PROXIES, proxyTemplates: proxyTemplates() });
});

let lastSignal = Date.now();

function listen() {
worker.onmessage = ({ data }) => {
  lastSignal = Date.now();
  if (data.type === "log") log(data.value);
  if (data.type === "runtime") runtimeReady = true;
  if (data.type === "error") {
    log(tr("Build failed: ") + data.value);
    fail(data.value);
    building = false;
    $("cancel").hidden = true;
    updateBuildEnabled();
    // A Pyodide that failed once stays failed, so the next build gets a new
    // worker instead of "Pyodide already fatally failed".
    restartWorker();
  }
  if (data.type === "done") {
    const { name, blob, info } = data.value;
    expected = { name, size: blob.size };
    // Deliver through the service worker: a plain Blob anchor download dies
    // halfway on phones and leaves a "pending" MediaStore item that the
    // installer then calls a corrupt package. A worker-served response carries
    // a length, so the download manager can finish and finalise it. The Blob
    // URL stays as the fallback until the worker acknowledges.
    url = URL.createObjectURL(blob);
    $("download").href = url;
    $("download").download = name;
    $("download").textContent = tr(`Download ${name} (${Math.round(blob.size / 1048576)} MB)`);
    const token = `${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 10)}`;
    if (navigator.serviceWorker && navigator.serviceWorker.controller) {
      const onReady = (event) => {
        if (event.data && event.data.type === "bunker-product-ready" && event.data.token === token) {
          navigator.serviceWorker.removeEventListener("message", onReady);
          $("download").href = `__dl/${token}?n=${encodeURIComponent(name)}`;
          $("download").removeAttribute("download");  // the response names the file
        }
      };
      navigator.serviceWorker.addEventListener("message", onReady);
      navigator.serviceWorker.controller.postMessage({ type: "bunker-product", token, name, blob });
    }
    // Second channel: the share sheet. The download manager is the weakest link
    // on phones (and in Incognito it is weaker still — a stalled download leaves
    // a "pending" item the installer calls a corrupt package). Handing the file
    // to the share sheet reaches "save to files" or the installer directly.
    const share = $("share");
    if (share) {
      const file = new File([blob], name, { type: "application/vnd.android.package-archive" });
      const usable = !!(navigator.share && navigator.canShare && navigator.canShare({ files: [file] }));
      share.hidden = !usable;
      share.onclick = usable ? () => {
        navigator.share({ files: [file], title: name }).catch(() => {});
      } : null;
    }
    fillResult(data.value);
    const verifyBox = $("verify-box");
    if (verifyBox) verifyBox.hidden = false;

    $("result").style.display = "block";
    building = false;
    $("cancel").hidden = true;
    updateBuildEnabled();
    setStage(7, 100);   // one past the last chip: every step is done, none is "on"
    log(tr("Done."));
  }
};
worker.onerror = (event) => {
  lastSignal = Date.now();
  building = false;
  $("cancel").hidden = true;
  updateBuildEnabled();
  fail(String(event.message || "The build worker stopped."));
  restartWorker();
};
}

listen();

// The chosen source survives a reload.
(function restoreSource() {
  try {
    const saved = localStorage.getItem(SOURCE_KEY);
    let proxy = localStorage.getItem(PROXY_KEY) || "";
    if (!saved && !proxy && mainlandChina()) proxy = PROXIES[0];
    if (proxy) $("proxy-url").value = proxy;
    const mode = saved || (mainlandChina() ? "proxy" : "site");
    const list = $("proxy-list");
    if (list) list.innerHTML = PROXIES.map((url) => `<option value="${url}">`).join("");
    const radio = document.querySelector(`input[name="launcher-source"][value="${mode}"]`);
    if (radio) radio.checked = true;
    restoreChecks();
    renderLog();
    syncSource();
  } catch (error) {
    // Private mode: keep the defaults.
  }
})();

// A worker that dies (the phone ended it for memory, or the page was frozen)
// sends nothing at all, and the page used to sit on a disabled button forever.
setInterval(() => {
  // 180 s: a slow phone can spend a minute in one patch step, and a false
  // "stuck" is worse than a late one.
  if (!building || Date.now() - lastSignal < 180000) return;
  building = false;
  $("cancel").hidden = true;
  updateBuildEnabled();
  fail("The build stopped responding for 3 minutes.");
  restartWorker();
}, 5000);

// The browser can freeze a tab (back/forward cache) with a build in progress;
// the worker is gone when it comes back, so say so instead of waiting.
window.addEventListener("pageshow", (event) => {
  if (!event.persisted || !building) return;
  building = false;
  $("cancel").hidden = true;
  updateBuildEnabled();
  fail("The browser suspended the page while it was building.");
  restartWorker();
});

/** A worker whose Python died cannot be reused: start a clean one. */
function restartWorker() {
  worker.terminate();
  worker = new Worker("worker.js");
  runtimeReady = false;
  warmed = false;
  listen();
}

// ---- 中文界面（默认中文，右上角切换）-------------------------------------
// 页面以英文撰写；这里按「英文原文 → 中文」替换文本、placeholder 与 aria-label，
// 并把动态文案（日志、下载按钮）包一层。文件名为玩家数据，保持原样。
const ZH = {
  "The optional memory menu (damage and defense multipliers, no skill cooldown, God mode, forced hit, BigHunt cap lift) is added by pointing the game's launcher at a prebuilt class that starts the menu and then the game.": "可选的内存菜单（伤害与防御倍率、技能无 CD、God 免伤、强制命中、讨伐战上限解除）通过把游戏的启动入口指向一个预编译类实现：它先拉起菜单，再进入游戏。",
  "Experimental: the first launch asks to allow drawing over other apps, and a menu that fails to start leaves the game untouched.": "实验性：首次启动会请求「显示在其他应用上层」权限；菜单启动失败也不会影响游戏本身。",
  "The optional memory menu (damage and defense multipliers, no skill cooldown, God mode, forced hit, BigHunt cap lift) is built on the command line: it rewrites the game's launcher activity and installs a native library, which this browser cannot do.": "可选的内存菜单（伤害与防御倍率、技能无 CD、God 免伤、强制命中、讨伐战上限解除）需要在命令行构建：它会改写游戏的启动 Activity 并放入原生库，浏览器内做不到。",
  "Build it with": "构建命令：",
  ", password and alias": "，密码与别名",
  "ADVANCED :: MOD MENU": "进阶选项 :: MOD 菜单",
  "The optional memory menu (damage and defense multipliers, no skill cooldown, God mode, forced hit, BigHunt cap lift) is built on the command line: it rewrites the game's launcher activity and installs a native library, which this browser cannot do. Build with scripts/build.py --mod-menu instead. See the Mod Menu section.": "可选的内存菜单（伤害与防御倍率、技能无 CD、God 免伤、强制命中、讨伐战上限解除）需要在命令行构建：它会改写游戏的启动 Activity 并放入原生库，浏览器内做不到。请改用 scripts/build.py --mod-menu 构建，详见「Mod 菜单」一节。",
  "Include the Mod Menu (experimental)": "包含 Mod 菜单（实验性）",
  "ADVANCED": "进阶选项",
  "Bunker · Lunar Tear builder": "Bunker · Lunar Tear 构建器",
  "The original master data,": "原版主数据，",
  "NOT CHOSEN": "未选择",
  "The game talks to its server on this device through ports 8003, 8080 and 3000. If another app already uses one of them, the launcher tells you. An offset moves all three. For example, 30000 gives 38003, 38080 and 33000. Leave it at 0 unless you need it, and use the same offset for updates.": "游戏在本机通过 8003、8080、3000 三个端口连接服务器。如果其中某个端口已被其他应用占用，启动器会提示。设置偏移可一次性移动这三个端口，例如 30000 会得到 38003、38080、33000。除非确有需要，请保持 0，并在更新时沿用同一偏移。",
  " password and alias ": "，密码与别名 ",
  ") to sign your own builds the same way. The key is public, so anyone's build can install over yours. To prevent this, sign with a key of your own instead.": "）以便用同样方式签名你自己的构建。该密钥是公开的，所以任何人都可以构建覆盖你的包。若要防止这一点，请改用自己的密钥。",
  "Play on a Mac": "在 Mac 上运行",
  "Then copy the resource dump's": "然后，将资源包的",
  "to the device and choose it in the Bunker. The app unpacks only the files the game uses. An extracted folder works too, as described in the": "复制到设备，并在「地堡」中选择它；应用只会解出游戏实际使用的文件。已解压的文件夹同样可用，详见",
  "guide": "指南",
  ". The Android build made here has no in-game Facebook account link. Offline play, Pod Programs and save backups work.": "。此处构建的 Android 版本没有游戏内的 Facebook 账号绑定。离线游玩、Pod Programs 与存档备份均可使用。",
  "the game server, by Walter-Sparrow": "游戏服务器，作者 Walter-Sparrow",
  "game and master-data patching, by Walter-Sparrow": "游戏与主数据补丁，作者 Walter-Sparrow",
  "the save editors in Pod Programs, by NMeliksah": "Pod Programs 的存档编辑器，作者 NMeliksah",
  "the content patcher, by NavHobbyDev": "内容修补器，作者 NavHobbyDev",
  "ANDROID": "ANDROID",
  "APK · arm64": "APK · arm64",
  "BUNKER": "BUNKER",
  "LUNAR TEAR // BUILD TERMINAL": "LUNAR TEAR // 构建终端",
  "BUILD": "构建",
  "GUIDE": "指南",
  "TROUBLESHOOTING": "疑难解答",
  "SOURCE ↗": "源码 ↗",
  "Build the offline game": "构建离线游戏",
  "For Android, from your own files. Everything runs in this browser; your files are never uploaded. There is no iPhone or iPad build.":
    "为 Android 构建，使用你自己的文件。全部在浏览器内完成，文件不会被上传。没有 iPhone 或 iPad 版本。",
  "00 Prepare the runtime": "00 准备运行时",
  "The launcher is the 25 MB app around your game APK. Choose where it comes from. In mainland China the GitHub proxy is picked on the first visit; anywhere else the site is used directly.": "启动器是包裹游戏 APK 的 25 MB 应用。选择它的来源。中国大陆首次打开默认走 GitHub 代理，其他地区直接连本站。",
  "0 · Download from this site": "0 · 直接从本站下载",
  "It comes from this page once and stays on the device, so later builds do not download it again.": "只从本站下载一次，之后留在设备上，后续构建不再下载。",
  "1 · Through a GitHub download proxy": "1 · 通过 GitHub 下载代理",
  "For a network where GitHub is slow or blocked. Give a proxy that takes a full GitHub URL, such as https://gh-proxy.com/; the download is still checked against this site's SHA-256.": "适用于 GitHub 慢或被阻断的网络。填写能接收完整 GitHub 地址的代理，例如 https://gh-proxy.com/；下载后仍会按本站公布的 SHA-256 核对。",
  "Paste a proxy address, such as https://gh-proxy.com/": "填写代理地址，例如 https://gh-proxy.com/",
  "That is not an http(s) address.": "这不是 http(s) 地址。",
  "The launcher will come from": "启动器将从这里下载：",
  "01 Your files": "01 你的文件",
  "02 Build": "02 构建",
  "03 Install": "03 安装",
  "ANDROID": "ANDROID",
  "APK · arm64": "APK · arm64",
  "GAME": "游戏",
  "MASTER DATA": "主数据",
  "NOT CHOSEN": "未选择",
  "CHOOSE": "选择",
  "CHANGE": "更换",
  "The original 3.7.1 ARM64 game APK.": "原版 3.7.1 ARM64 游戏 APK。",
  "The original 3.7.1 ARM64 game APK (JP or global).": "原版 3.7.1 ARM64 游戏 APK（日服或全球服）。",
  "Japan": "日服",
  "Global": "全球服",
  "Checking the checksum…": "正在校验 SHA-256……",
  "Not the original 3.7.1 release": "不是原版 3.7.1（SHA-256 不匹配）",
  "The file differs from the original 3.7.1 releases": "此文件与原版 3.7.1 不同；下方为本文件与原版的尺寸/摘要对照",
  "Verify the downloaded file:": "校验已下载的成品：",
  "Share / send to\u2026": "分享 / 发送到\u2026",
  "Incomplete download": "下载不完整",
  "Please download again.": "请重新下载。",
  "Size matches": "尺寸一致",
  "Choose the game .apk file.": "请选择游戏的 .apk 文件。",
  "Takes a few minutes and needs about 2 GB of free memory. A desktop browser works best.":
    "需要几分钟，并占用约 2 GB 内存。建议使用桌面浏览器。",
  "Takes a few minutes and needs about 2 GB of free memory. A desktop browser works best; a phone may run out of memory for a 300 MB APK.":
    "需要几分钟，并占用约 2 GB 内存。建议使用桌面浏览器；手机上构建 300 MB 的 APK 容易内存不足。",
  "ADVANCED :: SKIP THE FILE CHECK": "进阶选项 :: 跳过文件校验",
  "The build checks that your APK is the original 3.7.1 release and that the master data is the untouched 20240404193219.bin.e, because the patch offsets were read from those files. A split APK exported from an installed app has the same library and metadata, so it can still build, but a different game version will not.":
    "构建前会校验你的 APK 是原版 3.7.1、主数据是未被改动的 20240404193219.bin.e，因为补丁偏移量就是从这些文件里读出来的。从已安装应用导出的拆分包，其游戏库与元数据相同，仍可构建；但其他游戏版本不行。",
  "Build even if the files do not match": "即使文件不匹配也继续构建",
  "LOAD RUNTIME": "准备运行时",
  "CHECK FILES": "校验文件",
  "WRITE MOD MENU": "写入 MOD 菜单",
  "PATCH LIBRARY": "改写游戏库",
  "MANIFEST + MASTER": "清单与主数据",
  "WRITE APK": "打包 APK",
  "SIGN + VERIFY": "签名与校验",
  "VERSION": "版本",
  "REGION": "区域",
  "MOD MENU": "MOD 菜单",
  "SIZE": "大小",
  "RAW ERROR": "原始错误",
  "included": "已包含",
  "not included": "未包含",
  "Computing the checksum…": "正在计算校验值……",
  "EXPERIMENTAL :: PORT OFFSET": "实验性 :: 端口偏移",
  "Offset": "偏移",
  "BUILD ▶": "开始构建 ▶",
  "Download": "下载",
  "The APK is signed and ready to install. Every APK built on this page is signed with the same public Bunker key, so a newer build installs over an older one and keeps your saves.":
    "APK 已签名，可直接安装。本页构建的每个 APK 都用同一把公开的 Bunker 密钥签名，因此新版本可覆盖旧版本安装并保留存档。",
  "Download the key": "下载密钥",
  "to sign your own builds the same way. The key is public, so anyone's build can install over yours. To prevent this, sign with a key of your own instead.":
    "以便用同样方式签名你自己的构建。该密钥是公开的，所以任何人都可以构建覆盖你的包。若要防止这一点，请改用自己的密钥。",
  // 0764eb1 的 Windows 段落（剔 iOS/Mac 句子；链接已改 lovelyzy7 仓库）
  "The same APK runs on a Windows PC with an Intel or AMD processor, in Google's Android Emulator. Download":
    "同一 APK 也能在使用 Intel 或 AMD 处理器的 Windows 电脑上运行，使用 Google 的 Android 模拟器。下载",
  "from the": "（来自",
  "latest release": "最新发布",
  "and put it in one folder with the APK, named": "）；把它与名为",
  ", and": " 的 APK 以及",
  ". Turn on": " 放进同一个文件夹。接着在「Windows 功能」中启用",
  "in Windows features, then double-click": "，然后双击",
  ". The first start downloads about 2.3 GB from Google and copies the game files in. Open the launcher with Ctrl+B and move with WASD. See":
    "。首次启动会从 Google 下载约 2.3 GB，并把游戏文件拷入。按 Ctrl+B 打开启动器，用 WASD 移动。详见",
  "Play on Windows": "在 Windows 上运行",
  ".": "。",
  "Build failed: ": "构建失败：",
  "Choose the game file and the master data first.": "请先选择游戏文件与主数据。",
  "Choose two different files.": "请选择两个不同的文件。",
  "The port offset must be a whole number from 0 to 57455.": "端口偏移必须是 0 到 57455 之间的整数。",
  "Done.": "完成。",
  "STOP ■": "停止 ■",
  "COPY LOG": "复制日志",
  "COPIED": "已复制",
  "ONLY ERRORS": "只看错误",
  "Build cancelled.": "已取消构建。",
  "SOURCE": "来源",
  "this site": "本站",
  "the GitHub proxy": "GitHub 代理",
  "Loading the runtime and the launcher in the background…": "正在后台准备运行时与启动器……",
  "Skipping the file check.": "已跳过文件校验。",
  "Downloading": "正在下载",
  "Build": "构建",
  "END OF TRANSMISSION // GLORY TO MANKIND": "通信结束 // 愿人类荣光永存",
  "OPERATOR LINK // STANDING BY": "操作员链路 // 待命",
  "Source:": "源码：",
  "Built with": "使用以下项目",
};

const ZH_PATTERNS = [
  [/^Download (.+) \((\d+) MB\)$/, "下载 $1（$2 MB）"],
  [/^BUILDS BUNKER (.+)$/, "构建 Bunker $1"],
];

const LANG_KEY = "bunker_lang";
const translatedNodes = [];   // {node, original}
const translatedAttrs = [];   // {el, attr, original}

function zhText(text) {
  const t = text.replace(/\s+/g, " ").trim();
  if (ZH[t] !== undefined) return ZH[t];
  for (const [re, out] of ZH_PATTERNS) {
    const m = t.match(re);
    if (m) return out.replace(/\$(\d)/g, (_, n) => m[Number(n)] ?? "");
  }
  return null;
}

/** 动态文案（日志、下载按钮）也走词典；英文环境原样返回。 */
function tr(text) {
  if (currentLang() !== "zh") return text;
  return zhText(text) ?? text;
}

function restore() {
  for (const item of translatedNodes) item.node.nodeValue = item.original;
  for (const item of translatedAttrs) item.el.setAttribute(item.attr, item.original);
  translatedNodes.length = 0;
  translatedAttrs.length = 0;
}

function translatePage(on) {
  restore();
  if (!on) return;

  const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT, {
    acceptNode(node) {
      const p = node.parentElement;
      if (!p || ["SCRIPT", "STYLE", "CODE"].includes(p.tagName)) return NodeFilter.FILTER_REJECT;
      const chip = p.closest("#game-name, #master-name");
      if (chip && /[·.]/.test(node.nodeValue)) return NodeFilter.FILTER_REJECT;  // 文件名原样
      return zhText(node.nodeValue) !== null ? NodeFilter.FILTER_ACCEPT : NodeFilter.FILTER_SKIP;
    }
  });
  const nodes = [];
  while (walker.nextNode()) nodes.push(walker.currentNode);
  for (const node of nodes) {
    const raw = node.nodeValue, zh = zhText(raw);
    if (zh === null) continue;
    translatedNodes.push({node, original: raw});
    const lead = raw.match(/^\s*/)[0], trail = raw.match(/\s*$/)[0];
    node.nodeValue = lead + zh + trail;
  }

  document.querySelectorAll("[aria-label],[placeholder],[title]").forEach(el => {
    for (const attr of ["aria-label", "placeholder", "title"]) {
      const value = el.getAttribute(attr);
      if (!value) continue;
      const zh = zhText(value);
      if (zh === null) continue;
      translatedAttrs.push({el, attr, original: value});
      el.setAttribute(attr, zh);
    }
  });
}

function currentLang() {
  try { return localStorage.getItem(LANG_KEY) === "en" ? "en" : "zh"; } catch (e) { return "zh"; }
}

function setLang(lang) {
  try { localStorage.setItem(LANG_KEY, lang); } catch (e) {}
  // lang="en" on a page that shows Chinese makes Chrome offer to translate it,
  // and its own translation mangles the text; say which language is on screen.
  document.documentElement.lang = lang === "zh" ? "zh-Hans" : "en";
  const toggle = document.getElementById("lang");
  if (toggle) toggle.textContent = lang === "zh" ? "EN" : "中文";
  translatePage(lang === "zh");
  // 动态文案（日志、下载按钮）在下次写入时按当前语言生成
  if (typeof update === "function") update();
}

// app.js 在 body 末尾加载，此时上面的 DOM 已就绪，直接执行即可（不依赖事件）。
(function () {
  const nav = document.querySelector(".top .tools") || document.querySelector(".top nav");
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
