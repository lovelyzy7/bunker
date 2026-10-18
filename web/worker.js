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
let sources = null;    // mirrors.json: {bundle: {urls, sha256}, modmenu: {...}}
let ready = null;      // promise of the loaded Pyodide instance
const post = (type, value) => self.postMessage({ type, value });

const CHUNK = 8 << 20;   // Read the finished APK in 8 MB pieces; a 300 MB Uint8Array is a lot to hold twice.

/** fetch with a deadline, for hosts that accept the connection and then hang. */
function timed(url, options, ms) {
  if (!ms) return fetch(url, options);
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), ms);
  return fetch(url, { ...options, signal: controller.signal }).finally(() => clearTimeout(timer));
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

async function fetchBytes(url, label) {
  const controller = new AbortController();
  let timer = setTimeout(() => controller.abort(), 30000);  // no headers, or no progress, for 30 s
  try {
    const response = await fetch(url, { signal: controller.signal });
    if (!response.ok) throw new Error(`Cannot download ${label} (${response.status})`);
    const total = Number(response.headers.get("Content-Length")) || 0;
    const reader = response.body.getReader();
    const parts = [];
    let received = 0, shown = 0;
    for (;;) {
      const { done, value } = await reader.read();
      clearTimeout(timer);
      timer = setTimeout(() => controller.abort(), 30000);
      if (done) break;
      parts.push(value);
      received += value.length;
      if (total && received - shown > total / 20) {
        shown = received;
        post("log", `Downloading ${label}… ${Math.round((received / total) * 100)}%`);
      }
    }
    const bytes = new Uint8Array(received);
    let offset = 0;
    for (const part of parts) { bytes.set(part, offset); offset += part.length; }
    return bytes;
  } finally {
    clearTimeout(timer);
  }
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

/** One of the site's bundles, from the quickest source that returns the right bytes. */
async function bundleBytes(kind, label) {
  const known = (await loadSources())[kind] || {};
  const urls = known.urls && known.urls.length ? known.urls : [`bundles/${kind}.zip`];
  let lastError = null;
  for (const url of await byPing(urls)) {
    try {
      const started = performance.now();
      const bytes = await fetchBytes(url, label);
      const seconds = (performance.now() - started) / 1000;
      post("log", `${label} (${Math.round(bytes.length / 1048576)} MB) in ${seconds.toFixed(1)} s`
        + (seconds < 0.25 ? " (cached)" : ""));
      if (known.sha256 && (await sha256(bytes)) !== known.sha256) {
        post("log", `${label} from ${url} does not match the site's checksum`);
        lastError = new Error(`${label.replace(/^./, (c) => c.toUpperCase())} does not match the site's checksum`);
        continue;   // a mirror that returns other bytes is not used
      }
      if (url !== urls[0]) post("log", `${label} came from ${url}`);
      return bytes;
    } catch (error) {
      lastError = error;
      post("log", `Cannot download ${label} from ${url}: ${error.message || error}`);
    }
  }
  throw lastError || new Error(`Cannot download ${label}`);
}

/** A Blob for the finished APK, built piece by piece so the page never sees a second copy. */
function readBlob(FS, path, size) {
  const parts = [];
  const fd = FS.open(path, "r");
  try {
    for (let position = 0; position < size; position += CHUNK) {
      const part = new Uint8Array(Math.min(CHUNK, size - position));
      FS.read(fd, part, 0, part.length, position);
      parts.push(part);
    }
  } finally {
    FS.close(fd);
  }
  return new Blob(parts, { type: "application/vnd.android.package-archive" });
}

function writeFile(pyodide, path, bytes) {
  pyodide.FS.mkdirTree(path.slice(0, path.lastIndexOf("/")));
  pyodide.FS.writeFile(path, bytes);
}

/**
 * The Pyodide directories to try: the host a previous visit already stored
 * first (so the wasm comes off the disk), then the quickest, then the rest.
 */
async function pyodideBases() {
  if (pyodideBasesList) return pyodideBasesList;
  const bases = PYODIDE_HOSTS.map((host) => `https://${host}/pyodide/${PYODIDE_VERSION}/full/`);
  for (const base of bases) {
    try {
      if (await caches.match(base + "pyodide.asm.wasm")) {
        pyodideBasesList = [base, ...bases.filter((other) => other !== base)];
        return pyodideBasesList;
      }
    } catch (error) {
      break;   // no CacheStorage: order by latency only
    }
  }
  const files = await byPing(bases.map((base) => base + "pyodide.js"), 2500);
  pyodideBasesList = files.map((url) => url.slice(0, url.lastIndexOf("/") + 1));
  return pyodideBasesList;
}

async function setup() {
  post("log", "Loading Python…");
  let lastError = null;
  for (const base of await pyodideBases()) {
    try {
      if (typeof loadPyodide === "undefined") importScripts(base + "pyodide.js");
      post("log", `Python runtime from ${new URL(base).host}`);
      const pyodide = await loadPyodide({ indexURL: base });
      await pyodide.loadPackage(["pycryptodome", "msgpack", "lz4"]);
      pyodide.setStdout({ batched: (line) => post("log", line) });
      pyodide.setStderr({ batched: (line) => post("log", line) });
      const manifest = await (await fetch("py/manifest.json")).json();
      for (const file of manifest) {
        writeFile(pyodide, "/repo/" + file, new Uint8Array(await (await fetch("py/" + file)).arrayBuffer()));
      }
      pyodide.runPython("import sys; sys.path.insert(0, '/repo/web'); import webbuild");
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

/** Pull the launcher into the service worker's cache while the reader is still choosing files. */
function warmLauncher() {
  if (warming) return warming;
  warming = (async () => {
    try {
      const known = (await loadSources()).bundle || {};
      const url = (known.urls && known.urls[0]) || "bundles/android.zip";
      const response = await fetch(url);
      if (!response.ok || !response.body) return;
      const reader = response.body.getReader();
      while (!(await reader.read()).done) {}   // drained, not buffered: the service worker keeps it
    } catch (error) {
      // The build reports the failure properly; a warm-up that fails is silent.
    }
  })();
  return warming;
}

async function build(data) {
  const { game, master, portOffset = 0, modMenu = false, verify = true } = data;
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
    writeFile(pyodide, "/bundles/android.zip", await bundleBytes("bundle", "the launcher"));
    let payload = null;
    if (modMenu) {
      writeFile(pyodide, "/bundles/modmenu.zip", await bundleBytes("modmenu", "the Mod Menu"));
      payload = "/bundles/modmenu.zip";
    }
    const output = "/output/bunker.apk";
    FS.mkdirTree("/output");
    const built = builder.build_android(gamePath, masterPath, "/bundles/android.zip", output, log,
                                        portOffset, payload, verify);
    const info = built && built.toJs ? built.toJs({ dict_converter: Object.fromEntries }) : {};
    if (built && built.destroy) built.destroy();
    const blob = readBlob(FS, output, FS.stat(output).size);
    // The file is handed over first: the checksum is for the record, and the
    // page can offer the download while it is still being computed.
    post("done", { name: "bunker.apk", blob, info });
    log("Computing the checksum…");
    let checksum = "";
    try {
      checksum = pyodide.runPython(
        `import hashlib\nhashlib.file_digest(open(${JSON.stringify(output)}, "rb"), "sha256").hexdigest()`);
    } catch (error) {
      checksum = "";
    }
    post("sha256", checksum);
    FS.unlink(output);
    for (const name of FS.readdir("/bundles")) if (name !== "." && name !== "..") FS.unlink("/bundles/" + name);
  } catch (error) {
    post("error", String(error.message || error).split("\n").filter(Boolean).slice(-3).join("\n"));
  }
}

self.onmessage = ({ data }) => {
  if (data.type === "preload") {
    // Start the slow parts now; failures stay quiet and the build reports them.
    runtime().catch(() => {});
    warmLauncher();
    return;
  }
  build(data);
};
