// Keeps the launcher bundle and the Python runtime on disk, so a second build
// on the same device does not download 35 MB again — the difference between a
// 20-second build and a one-minute one on a slow link.
//
// The cache name carries the release version. The page registers
// sw.js?v=<version>, so a release installs a new worker, whose activate step
// drops the previous cache: a stale runtime can never be mixed with a new page.

const VERSION = new URL(self.location.href).searchParams.get("v") || "dev";
const CACHE = `bunker-${VERSION}`;
// app.js and worker.js carry the build stamp in their url, so they are cached
// on first use rather than here.
const SHELL = ["./", "index.html", "regions.json", "mirrors.json"];

self.addEventListener("install", (event) => {
  event.waitUntil((async () => {
    const cache = await caches.open(CACHE);
    // A file that is missing must not block the install.
    await Promise.all(SHELL.map((path) => cache.add(path).catch(() => {})));
    await self.skipWaiting();
  })());
});

self.addEventListener("activate", (event) => {
  event.waitUntil((async () => {
    for (const key of await caches.keys()) if (key !== CACHE) await caches.delete(key);
    await self.clients.claim();
  })());
});

const KEEP = /\/(bundles|py|pyodide)\//;   // the bundles, the sources and Python: fetched once
const CDN = /(^|\.)jsdelivr\.net$/;  // Pyodide's wasm and wheels

// ---- Finished-product delivery -------------------------------------------------
// A large Blob saved through an anchor (URL.createObjectURL) dies halfway on
// phones: the MediaStore item stays "pending" and the installer answers “There
// was a problem parsing the package” although the build itself was fine. The
// page hands the finished APK here instead, and the download runs as a normal
// response with a length, which the download manager can finish and finalise.
const PRODUCTS = new Map();  // token -> { blob, name }

self.addEventListener("message", (event) => {
  const data = event.data;
  if (data && data.type === "bunker-product") {
    for (const key of [...PRODUCTS.keys()]) PRODUCTS.delete(key);
    PRODUCTS.set(data.token, { blob: data.blob, name: data.name || "bunker.apk" });
    if (event.source) event.source.postMessage({ type: "bunker-product-ready", token: data.token });
  }
});

/** Cache first, fill from the network on the first visit. */
async function fromCache(request) {
  const cache = await caches.open(CACHE);
  const hit = await cache.match(request);
  if (hit) return hit;
  const response = await fetch(request);
  // The reader must not wait for the disk write; and a partial body (the tab
  // was closed, the network died) must not be kept as if it were whole.
  const keep = response.ok && response.status === 200
    && (response.type === "basic" || response.type === "cors")
    && !request.headers.has("range");
  if (keep) {
    const copy = response.clone();
    caches.open(CACHE).then((store) => store.put(request, copy)).catch(() => {});
  }
  return response;
}

async function fresh(request, ms) {
  if (!ms) return fetch(request);
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), ms);
  try {
    return await fetch(request, { signal: controller.signal });
  } finally {
    clearTimeout(timer);
  }
}

self.addEventListener("fetch", (event) => {
  const request = event.request;
  if (request.method !== "GET") return;
  const url = new URL(request.url);
  const dl = /(?:^|\/)__dl\/([A-Za-z0-9_-]+)$/.exec(url.pathname);
  if (dl) {
    event.respondWith((async () => {
      const entry = PRODUCTS.get(dl[1]);
      if (!entry) return new Response("expired", { status: 410 });
      return new Response(entry.blob, {
        headers: {
          "Content-Type": "application/vnd.android.package-archive",
          "Content-Length": String(entry.blob.size),
          "Content-Disposition": `attachment; filename="${entry.name.replace(/["\\]/g, "_")}"`,
        },
      });
    })());
    return;
  }
  if (KEEP.test(url.pathname) || CDN.test(url.hostname)) {
    event.respondWith(fromCache(request));
    return;
  }
  if (url.origin !== self.location.origin) return;
  // The page itself: the network first, so a new release appears at once, and
  // what is on disk only when the network is too slow or gone.
  event.respondWith((async () => {
    const cache = await caches.open(CACHE);
    try {
      const response = await fresh(request, 4000);
      if (response.ok) cache.put(request, response.clone());
      return response;
    } catch (error) {
      const hit = await cache.match(request);
      return hit || fetch(request);
    }
  })());
});
