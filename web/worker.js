// Runs the build in a background thread so the page stays responsive.
importScripts("https://cdn.jsdelivr.net/pyodide/v0.28.3/full/pyodide.js");

let ready = null;
const post = (type, value) => self.postMessage({ type, value });

async function fetchBytes(url, label) {
  const response = await fetch(url);
  if (!response.ok) throw new Error(`Cannot download ${label} (${response.status})`);
  const total = Number(response.headers.get("Content-Length")) || 0;
  const reader = response.body.getReader();
  const parts = [];
  let received = 0, shown = 0;
  for (;;) {
    const { done, value } = await reader.read();
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
}

const CHUNK = 8 << 20;   // Read the finished APK in 8 MB pieces; a 300 MB Uint8Array is a lot to hold twice.

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

async function setup() {
  post("log", "Loading Python…");
  const pyodide = await loadPyodide();
  await pyodide.loadPackage(["pycryptodome", "msgpack", "lz4"]);
  pyodide.setStdout({ batched: (line) => post("log", line) });
  pyodide.setStderr({ batched: (line) => post("log", line) });
  const manifest = await (await fetch("py/manifest.json")).json();
  for (const file of manifest) {
    writeFile(pyodide, "/repo/" + file, new Uint8Array(await (await fetch("py/" + file)).arrayBuffer()));
  }
  pyodide.runPython("import sys; sys.path.insert(0, '/repo/web'); import webbuild");
  return pyodide;
}

self.onmessage = async ({ data }) => {
  const { game, master, portOffset = 0, modMenu = false, verify = true } = data;
  try {
    ready = ready || setup();
    const pyodide = await ready;
    const FS = pyodide.FS;
    // Your files are read where they are, without copying them into memory.
    try { FS.unmount("/input"); } catch (_) {}
    FS.mkdirTree("/input");
    FS.mount(FS.filesystems.WORKERFS, { files: [game, master] }, "/input");
    const gamePath = "/input/" + game.name, masterPath = "/input/" + master.name;
    const log = (line) => post("log", line);
    const builder = pyodide.globals.get("webbuild");
    writeFile(pyodide, "/bundles/android.zip", await fetchBytes("bundles/android.zip", "the launcher"));
    let payload = null;
    if (modMenu) {
      writeFile(pyodide, "/bundles/modmenu.zip", await fetchBytes("bundles/modmenu.zip", "the Mod Menu"));
      payload = "/bundles/modmenu.zip";
    }
    const output = "/output/bunker.apk";
    FS.mkdirTree("/output");
    const built = builder.build_android(gamePath, masterPath, "/bundles/android.zip", output, log,
                                        portOffset, payload, verify);
    const info = built && built.toJs ? built.toJs({ dict_converter: Object.fromEntries }) : {};
    if (built && built.destroy) built.destroy();
    log("Computing the checksum…");
    const sha256 = pyodide.runPython(
      `import hashlib\nhashlib.file_digest(open(${JSON.stringify(output)}, "rb"), "sha256").hexdigest()`);
    const blob = readBlob(FS, output, FS.stat(output).size);
    FS.unlink(output);
    for (const name of FS.readdir("/bundles")) if (name !== "." && name !== "..") FS.unlink("/bundles/" + name);
    self.postMessage({ type: "done", value: { name: "bunker.apk", blob, sha256, info } });
  } catch (error) {
    post("error", String(error.message || error).split("\n").filter(Boolean).slice(-3).join("\n"));
  }
};
