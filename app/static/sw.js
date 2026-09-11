const CACHE = 'balance-v15';
const ASSETS = ['/static/styles.css', '/static/app.js', '/static/icon.svg', '/static/manifest.json'];

self.addEventListener('install', (e) => {
  e.waitUntil(caches.open(CACHE).then((c) => c.addAll(ASSETS)).catch(() => {}));
  self.skipWaiting();
});
self.addEventListener('activate', (e) => {
  e.waitUntil(caches.keys().then((keys) =>
    Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k)))));
  self.clients.claim();
});
self.addEventListener('fetch', (e) => {
  const url = new URL(e.request.url);
  // Solo cachea estáticos; las páginas siempre van a la red (datos frescos)
  if (e.request.method === 'GET' && url.pathname.startsWith('/static/')) {
    e.respondWith(caches.match(e.request).then((r) => r || fetch(e.request)));
  }
});
