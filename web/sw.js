// Keeps the launcher bundle and the Python runtime on disk, so a second build
// on the same device does not download 35 MB again — the difference between a
// 20-second build and a one-minute one on a slow link.
//
// The cache name carries the release version. The page registers
// sw.js?v=<version>, so a release installs a new worker, whose activate step
// drops the previous cache: a stale runtime can never be mixed with a new page.

const VERSION = new URL(self.location.href).searchParams.get("v") || "dev";
const CACHE = `bunker-${VERSION}`;
const SHELL = ["./", "index.html", "app.js", "worker.js", "regions.json", "mirrors.json"];

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

const KEEP = /\/(bundles|py)\//;   // the bundles and the Python sources: fetched once
const CDN = /(^|\.)jsdelivr\.net$/;  // Pyodide's wasm and wheels

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
