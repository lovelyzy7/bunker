// Runs the build in a background thread so the page stays responsive.
// The Python runtime and the launcher bundle each have more than one source:
// whichever answers first is used, and the bytes are checked against the
// checksum in mirrors.json before they reach the build. The service worker
// keeps both, so a second build on the same device does not download them again.

const PYODIDE_VERSION = "v0.28.3";
// jsDelivr's own endpoints; cdn.jsdelivr.net is the one that is often slow or
// blocked from mainland China, the other two serve the same files.
const PYODIDE_HOSTS = ["cdn.jsdelivr.net", "fastly.jsdelivr.net", "gcore.jsdelivr.net"];

let pyodideBasesList = null;
let BUILD = null;      // the site's build stamp: its files change whenever the site is rebuilt
let usedSource = "site";  // where the launcher came from, for the result card
let sources = null;    // mirrors.json: {bundle: {urls, sha256}, modmenu: {...}}
let ready = null;      // promise of the loaded Pyodide instance
const post = (type, value) => self.postMessage({ type, value });

/** fetch with a deadline, for hosts that accept the connection and then hang. */
function timed(url, options, ms) {
  if (!ms) return fetch(url, options);
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), ms);
  return fetch(url, { ...options, signal: controller.signal }).finally(() => clearTimeout(timer));
}

/** How long 64 KB takes to arrive, or Infinity when it does not. */
async function timeRange(url, ms = 5000) {
  const started = performance.now();
  try {
    const response = await timed(url, { headers: { Range: "bytes=0-65535" }, cache: "no-store" }, ms);
    if (!response.ok && response.status !== 206) return Infinity;
    await response.arrayBuffer();   // the body is what takes the time
    return performance.now() - started;
  } catch (error) {
    return Infinity;
  }
}

/** How long a source takes to answer, or Infinity when it does not. */
async function ping(url, ms) {
  const start = performance.now();
  try {
    const response = await timed(url, { method: "HEAD", cache: "no-store" }, ms);
    return response.ok ? performance.now() - start : Infinity;
  } catch (error) {
    return Infinity;
  }
}

/**
 * The same urls, quickest first; a url that has not answered by the deadline
 * keeps its place at the end. Waits for the deadline at most, so one dead host
 * does not hold up a download from a working one.
 */
async function byPing(urls, ms = 5000) {
  const known = new Map();
  const all = Promise.all(urls.map(async (url) => {
    const took = await ping(url, ms);
    known.set(url, took);
    return took;
  }));
  await Promise.race([all, new Promise((resolve) => setTimeout(resolve, ms + 250))]);
  const timed = urls.map((url, index) => ({ url, index, ms: known.has(url) ? known.get(url) : Infinity }));
  timed.sort((a, b) => (a.ms - b.ms) || (a.index - b.index));
  return timed.map((item) => item.url);
}

async function sha256(bytes) {
  const digest = await crypto.subtle.digest("SHA-256", bytes);
  return [...new Uint8Array(digest)].map((b) => b.toString(16).padStart(2, "0")).join("");
}

const STALLED = { stalled: true };

/**
 * The promise, or STALLED after ms. Aborting a fetch does not always settle a
 * pending read() — on a stalled connection the build then waited forever — so
 * the wait is raced against a timer instead of relying on the abort.
 */
function within(promise, ms) {
  let timer;
  const wait = new Promise((resolve) => { timer = setTimeout(() => resolve(STALLED), ms); });
  return Promise.race([promise.finally(() => clearTimeout(timer)), wait]);
}

async function fetchBytes(url, label, stallMs = 20000) {
  const controller = new AbortController();
  try {
    const response = await within(fetch(url, { signal: controller.signal }), stallMs);
    if (response === STALLED) {
      controller.abort();
      throw new Error(`no response for ${stallMs / 1000} s`);
    }
    if (!response.ok) throw new Error(`Cannot download ${label} (HTTP ${response.status})`);
    // A compressed body (jsDelivr sends the wasm as Brotli) makes Content-Length
    // the compressed size while fetch hands over decompressed bytes: a
    // percentage then passes 100%. Report bytes instead when that is the case.
    const encoded = !!response.headers.get("content-encoding");
    const total = Number(response.headers.get("Content-Length")) || 0;
    const reader = response.body.getReader();
    const parts = [];
    let received = 0, shown = 0;
    for (;;) {
      const next = await within(reader.read(), stallMs);
      if (next === STALLED) {
        controller.abort();
        reader.cancel().catch(() => {});
        throw new Error(`no data for ${stallMs / 1000} s after ${Math.round(received / 1048576)} MB`);
      }
      const { done, value } = next;
      if (done) break;
      parts.push(value);
      received += value.length;
      if (encoded) {
        if (received - shown > 4 << 20) {
          shown = received;
          post("log", `Downloading ${label}… ${Math.round(received / 1048576)} MB`);
        }
      } else if (total && received - shown > total / 20) {
        shown = received;
        post("log", `Downloading ${label}… ${Math.min(100, Math.round((received / total) * 100))}%`);
      }
    }
    const bytes = new Uint8Array(received);
    let offset = 0;
    for (const part of parts) { bytes.set(part, offset); offset += part.length; }
    return bytes;
  } finally {
    controller.abort();   // release a body that was left half-read
  }
}

/** The stamp from version.json; every same-origin download carries it, so a
 *  cached file from an older build of the site can never be used. */
async function buildStamp() {
  if (BUILD === null) {
    try {
      const version = await (await fetch("version.json")).json();
      BUILD = String(version.build || version.version || "");
    } catch (error) {
      BUILD = "";
    }
  }
  return BUILD;
}

/** A same-origin url with the build stamp; a mirror's own url is left alone. */
async function versioned(url) {
  if (url.includes("://")) return url;
  const stamp = await buildStamp();
  return url + (url.includes("?") ? "&" : "?") + "b=" + encodeURIComponent(stamp);
}

async function loadSources() {
  if (sources) return sources;
  try {
    sources = await (await fetch("mirrors.json")).json();
  } catch (error) {
    sources = {};   // no mirrors: the same-origin bundle is still tried below
  }
  return sources;
}

/** A bundle from a proxy: two tries, then the same digest check as everything else. */
async function proxyBytes(url, label, expected) {
  let lastError = null;
  for (let attempt = 1; attempt <= 2; attempt++) {
    try {
      const started = performance.now();
      const bytes = await fetchBytes(url, label);
      const seconds = (performance.now() - started) / 1000;
      post("log", `${label} (${Math.round(bytes.length / 1048576)} MB) in ${seconds.toFixed(1)} s`);
      if (expected && (await sha256(bytes)) !== expected) {
        lastError = new Error(`${label.replace(/^./, (c) => c.toUpperCase())} does not match the site's checksum`);
        post("log", lastError.message);
        break;   // a wrong copy will not fix itself
      }
      return bytes;
    } catch (error) {
      lastError = error;
      post("log", `Cannot download ${label} from ${url}: ${error.message || error}`);
      if (attempt === 1) post("log", `Trying ${url} again…`);
    }
  }
  throw lastError;
}

/** Proxy prefix/templates for every prebuilt file (entered one first). Non-empty
 *  only in proxy mode; a full launcher URL is left out — it says nothing about
 *  other files. */
let proxyTemplates = [];

/** The same prefix/template rules the page uses (app.js resolveVia, modmenu case). */
function viaProxy(template, target) {
  if (!template || !target) return null;
  if (template.includes("{url}")) return template.replace("{url}", target);
  if (template.endsWith("/") || /^https?:\/\/[^/]+$/i.test(template)) return template + target;
  return null;
}

/**
 * One prebuilt payload file (a builder source, the fix3 tables, the font
 * payloads). In proxy mode every file with a declared GitHub home in
 * mirrors.json goes through the proxy first (two tries, digest-checked);
 * the site always covers for a dead, stale or wrong proxy, and digests the
 * copy either way.
 */
async function prebuiltBytes(path, label) {
  const info = ((await loadSources()).files || {})[path] || {};
  for (const template of proxyTemplates) {
    const url = viaProxy(template, info.github);
    if (!url) continue;
    try {
      const bytes = await proxyBytes(url, label, info.sha256);
      post("log", `${label} came from ${url}`);
      return bytes;
    } catch (error) {
      post("log", "The proxy did not work; trying this site…");
    }
  }
  const fetchUrl = await versioned("py/" + path);
  const bytes = new Uint8Array(await (await fetch(fetchUrl)).arrayBuffer());
  if (info.sha256 && (await sha256(bytes)) !== info.sha256) {
    throw new Error(`${label.replace(/^./, (c) => c.toUpperCase())} does not match the site's checksum`);
  }
  return bytes;
}

function describeMs(ms) {
  return Number.isFinite(ms) ? `${Math.round(ms)} ms` : "no answer";
}

/**
 * The launcher: the site, or the proxy. With a proxy the two downloads are
 * timed first (64 KB each) so a slow proxy does not win just because it was
 * chosen, and either one can cover for the other.
 */
async function launcherBytes(launcherUrl, proxies) {
  if (!launcherUrl) {
    usedSource = "site";
    return bundleBytes("bundle", "the launcher");
  }
  const sources = await loadSources();
  const known = (sources.bundle || {}).sha256;
  const siteUrl = await versioned("bundles/android.zip");
  // The entered proxy, plus the other known ones, so one dead proxy is not the
  // end of it. Everything is timed first: a slow proxy must not win because it
  // happened to be the one chosen.
  const endpoints = [["site", siteUrl]];
  for (const url of [launcherUrl, ...(proxies || []).map((base) => base + (sources.github || ""))]) {
    if (url && !endpoints.some(([, seen]) => seen === url)) endpoints.push(["proxy", url]);
  }
  const timed = await Promise.all(endpoints.map(async ([kind, url]) => ({ kind, url, ms: await timeRange(url) })));
  timed.sort((a, b) => a.ms - b.ms);
  for (const item of timed) post("log", `Speed: ${item.kind} ${describeMs(item.ms)}`);
  let lastError = null;
  for (const { kind, url } of timed) {
    try {
      const bytes = kind === "site"
        ? await bundleBytes("bundle", "the launcher")
        : await proxyBytes(url, "the launcher", known);
      usedSource = kind;
      post("log", `the launcher came from ${url}`);
      return bytes;
    } catch (error) {
      lastError = error;
      post("log", `Cannot download the launcher from ${url}: ${error.message || error}`);
    }
  }
  throw lastError || new Error("Cannot download the launcher");
}

async function modmenuFrom(url) {
  const known = ((await loadSources()).modmenu || {}).sha256;
  const bytes = await proxyBytes(url, "the Mod Menu", known);
  post("log", `the Mod Menu came from ${url}`);
  return bytes;
}

/** One of the site's bundles, from the quickest source that returns the right bytes. */
async function bundleBytes(kind, label) {
  const known = (await loadSources())[kind] || {};
  const urls = known.urls && known.urls.length ? known.urls : [`bundles/${kind}.zip`];
  let lastError = null;
  for (const url of await byPing(urls)) {
    for (let attempt = 1; attempt <= 2; attempt++) {
      try {
        const fetchUrl = await versioned(url);
        const started = performance.now();
        const bytes = await fetchBytes(fetchUrl, label);
        const seconds = (performance.now() - started) / 1000;
        post("log", `${label} (${Math.round(bytes.length / 1048576)} MB) in ${seconds.toFixed(1)} s`
          + (seconds < 0.25 ? " (cached)" : ""));
        if (known.sha256 && (await sha256(bytes)) !== known.sha256) {
          post("log", `${label} from ${url} does not match the site's checksum; the saved copy was dropped`);
          await forget(fetchUrl);
          lastError = new Error(`${label.replace(/^./, (c) => c.toUpperCase())} does not match the site's checksum`);
          break;   // a wrong copy will not fix itself: try the next source
        }
        if (url !== urls[0]) post("log", `${label} came from ${url}`);
        return bytes;
      } catch (error) {
        lastError = error;
        post("log", `Cannot download ${label} from ${url}: ${error.message || error}`);
        if (attempt === 1) post("log", `Trying ${url} again…`);
      }
    }
  }
  throw lastError || new Error(`Cannot download ${label}`);
}

/** Drop a saved bundle that did not match its digest, so the next try downloads it. */
async function forget(url) {
  try {
    for (const name of await caches.keys()) {
      const cache = await caches.open(name);
      if (await cache.match(url)) await cache.delete(url);
    }
  } catch (error) {
    // No CacheStorage: nothing was saved.
  }
}

// The finished file goes to the page as a Blob built from pieces, so it is never
// held whole twice: browsers can keep a large Blob out of the page's memory.
class Pieces {
  constructor() { this.blob = new Blob([]); this.pending = []; this.size = 0; }
  add(bytes) {
    this.pending.push(bytes);
    this.size += bytes.length;
    if (this.pending.length >= 8) this.fold();
  }
  fold() { this.blob = new Blob([this.blob, ...this.pending], { type: "application/octet-stream" }); this.pending = []; }
  done() { this.fold(); return this.blob; }
}

function writeFile(pyodide, path, bytes) {
  pyodide.FS.mkdirTree(path.slice(0, path.lastIndexOf("/")));
  pyodide.FS.writeFile(path, bytes);
}

/**
 * The Pyodide directories to try: this site's own copy first (it cannot be
 * blocked when the page itself loads), then the jsDelivr endpoints ordered by
 * how fast 64 KB of the wasm actually arrives.
 */
async function pyodideBases() {
  if (pyodideBasesList) return pyodideBasesList;
  const local = new URL("pyodide/", self.location).href;
  const remote = PYODIDE_HOSTS.map((host) => `https://${host}/pyodide/${PYODIDE_VERSION}/full/`);
  const bases = [local, ...remote];
  try {
    for (const base of bases) {
      if (await caches.match(base + "pyodide.asm.wasm")) {
        pyodideBasesList = [base, ...bases.filter((other) => other !== base)];
        return pyodideBasesList;
      }
    }
  } catch (error) {
    // No CacheStorage: order by the probe below.
  }
  const measured = await Promise.all(remote.map(async (base) => ({ base, ms: await timeRange(base + "pyodide.asm.wasm") })));
  measured.sort((a, b) => a.ms - b.ms);
  pyodideBasesList = [local, ...measured.map((item) => item.base)];
  return pyodideBasesList;
}

/** Fetch a file the runtime is about to need anyway, so the log shows progress. */
async function warm(url, label) {
  try {
    await fetchBytes(url, label);
  } catch (error) {
    // loadPyodide reports a missing file itself; a warm-up that fails is silent.
  }
}

async function setup() {
  post("log", "Loading Python…");
  let lastError = null;
  for (const base of await pyodideBases()) {
    try {
      if (typeof loadPyodide === "undefined") importScripts(base + "pyodide.js");
      post("log", `Python runtime from ${new URL(base).host}`);
      // These are the two big downloads; fetching them here puts real progress
      // in the log instead of a silent pause while loadPyodide works.
      post("log", "Downloading the Python runtime…");
      await Promise.all([
        warm(base + "pyodide.asm.wasm", "the Python runtime"),
        warm(base + "python_stdlib.zip", "the Python standard library"),
      ]);
      const pyodide = await loadPyodide({ indexURL: base });
      post("log", "Downloading Python packages…");
      await pyodide.loadPackage(["pycryptodome", "msgpack", "lz4"]);
      pyodide.setStdout({ batched: (line) => post("log", line) });
      pyodide.setStderr({ batched: (line) => post("log", line) });
      const stamp = await buildStamp();
      const manifest = await (await fetch(`py/manifest.json?b=${encodeURIComponent(stamp)}`)).json();
      post("log", `Loading the builder sources (${manifest.length} files)…`);
      for (const file of manifest) {
        writeFile(pyodide, "/repo/" + file, await prebuiltBytes(file, file));
      }
      pyodide.runPython("import sys; sys.path.insert(0, '/repo/web'); import webbuild");
      post("log", "Python ready.");
      post("runtime", true);
      return pyodide;
    } catch (error) {
      lastError = error;
      post("log", `Python from ${new URL(base).host} failed: ${error.message || error}`);
    }
  }
  throw lastError || new Error("The Python runtime could not be loaded");
}

/** The runtime loads once; a preload that failed is retried by the build. */
function runtime() {
  if (!ready) {
    ready = setup();
    ready.catch(() => { ready = null; });
  }
  return ready;
}

let warming = null;
let warmedUrl = null;

/** Pull the launcher into the service worker's cache while the reader is still choosing files. */
function warmLauncher(url) {
  const target = url || null;
  if (warming && warmedUrl === target) return warming;
  warmedUrl = target;
  warming = (async () => {
    try {
      const known = (await loadSources()).bundle || {};
      const wanted = target || (known.urls && known.urls[0]) || "bundles/android.zip";
      const response = await within(fetch(await versioned(wanted)), 20000);
      if (response === STALLED || !response.ok || !response.body) return;
      const reader = response.body.getReader();
      for (;;) {   // drained, not buffered: the service worker keeps it
        const next = await within(reader.read(), 20000);
        if (next === STALLED) { reader.cancel().catch(() => {}); return; }
        if (next.done) return;
      }
    } catch (error) {
      // The build reports the failure properly; a warm-up that fails is silent.
    }
  })();
  return warming;
}

async function build(data) {
  const { game, master, portOffset = 0, modMenu = false, verify = true,
          launcherUrl = null } = data;
  try {
    const pyodide = await runtime();
    const FS = pyodide.FS;
    // Your files are read where they are, without copying them into memory.
    try { FS.unmount("/input"); } catch (_) {}
    FS.mkdirTree("/input");
    FS.mount(FS.filesystems.WORKERFS, { files: [game, master] }, "/input");
    const gamePath = "/input/" + game.name, masterPath = "/input/" + master.name;
    const log = (line) => post("log", line);
    const builder = pyodide.globals.get("webbuild");
    writeFile(pyodide, "/bundles/android.zip", await launcherBytes(launcherUrl, data.proxies));
    // JS null becomes a truthy JsNull proxy in Pyodide 0.28.3 and defeats the
    // Python None guards; undefined converts to None properly (L5 §7.2).
    let payload = undefined;
    if (modMenu) {
      let bytes = null;
      if (data.modmenuUrl) {
        try {
          bytes = await modmenuFrom(data.modmenuUrl);
        } catch (error) {
          post("log", "The proxy did not work; trying this site…");
        }
      }
      if (!bytes) bytes = await bundleBytes("modmenu", "the Mod Menu");
      writeFile(pyodide, "/bundles/modmenu.zip", bytes);
      payload = "/bundles/modmenu.zip";
    }
    // Product naming contract (§9.1): the Python side names the product from
    // the client detection (nier-jp.apk / nier-en.apk) and returns its name.
    // The APK comes out in pieces as it is written; it is never held whole here.
    const pieces = new Pieces();
    const handOver = (piece) => {
      const buffer = piece.getBuffer("u8");
      pieces.add(buffer.data.slice());
      buffer.release();
      piece.destroy();
    };
    const built = builder.build_android(gamePath, masterPath, "/bundles/android.zip", undefined, log,
                                        portOffset, payload, verify, handOver);
    const info = built && built.toJs ? built.toJs({ dict_converter: Object.fromEntries }) : {};
    if (built && built.destroy) built.destroy();
    const blob = pieces.done();
    // info.sha256 comes from the signing pass; the finished APK is not hashed again.
    post("done", { name: info.product_name || "bunker.apk", blob, info: { ...info, source: usedSource } });
    for (const name of FS.readdir("/bundles")) if (name !== "." && name !== "..") FS.unlink("/bundles/" + name);
  } catch (error) {
    post("error", String(error.message || error).split("\n").filter(Boolean).slice(-3).join("\n"));
  }
}

self.onmessage = ({ data }) => {
  if (data.proxyTemplates) proxyTemplates = data.proxyTemplates;
  if (data.type === "preload") {
    // Start the slow parts now; failures stay quiet and the build reports them.
    runtime().catch(() => {});
    warmLauncher(data.launcherUrl);
    return;
  }
  build(data);
};
