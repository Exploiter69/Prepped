/* Prepped Service Worker (Pack B6)
   Privacy-strict cache strategy:
   - Caches ONLY static application shell assets (HTML/CSS/JS/SVG/manifest).
   - NEVER caches /api/* requests, learner transcripts, audio, or personal data. */
const CACHE_NAME = "prepped-shell-v2";
const SHELL_ASSETS = [
  "/",
  "/manifest.webmanifest",
  "/static/style.css?v=sci-curriculum-1",
  "/static/motion.css?v=sci-curriculum-1",
  "/static/enhancements.css?v=sci-curriculum-1",
  "/static/assets/prepped-icon.svg",
  "/static/assets/prepped-owl-welcome.svg",
  "/static/assets/prepped-owl-thinking.svg",
  "/static/assets/prepped-owl-support.svg",
  "/static/assets/prepped-owl-celebration.svg",
];

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => cache.addAll(SHELL_ASSETS)).catch(() => undefined)
  );
  self.skipWaiting();
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.filter((k) => k !== CACHE_NAME).map((k) => caches.delete(k)))
    )
  );
  self.clients.claim();
});

self.addEventListener("fetch", (event) => {
  const req = event.request;
  if (req.method !== "GET") return;
  const url = new URL(req.url);
  if (url.origin !== self.location.origin) return;
  // Strictly never intercept or cache private API endpoints or data
  if (url.pathname.startsWith("/api/")) return;

  const isStaticAsset = url.pathname === "/" || url.pathname === "/manifest.webmanifest" || url.pathname.startsWith("/static/");
  if (!isStaticAsset) return;

  event.respondWith(
    fetch(req)
      .then((response) => {
        if (response && response.ok && response.type === "basic") {
          const clone = response.clone();
          caches.open(CACHE_NAME).then((cache) => cache.put(req, clone)).catch(() => undefined);
        }
        return response;
      })
      .catch(() => caches.match(req))
  );
});
