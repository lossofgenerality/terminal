/* Packing Station service worker — the page opens offline; sub-tasks always come from their own addresses.
   © Computational Classnotes · CC BY-NC-SA 4.0 */
const VERSION = "terminal-packing-station-live";
const SHELL = ['./', './index.html', './manifest.webmanifest', './notes.md', './icons/icon-192.png', './icons/icon-512.png', './icons/icon-maskable-512.png', './icons/apple-touch-icon.png', './icons/favicon-32.png'];
self.addEventListener('install', e => { e.waitUntil(caches.open(VERSION).then(c => c.addAll(SHELL)).then(() => self.skipWaiting())); });
self.addEventListener('activate', e => { e.waitUntil(caches.keys().then(k => Promise.all(k.filter(x => x !== VERSION).map(x => caches.delete(x)))).then(() => self.clients.claim())); });
self.addEventListener('fetch', e => {
  const req = e.request; if (req.method !== 'GET') return; const url = new URL(req.url); if (url.origin !== self.location.origin) return;
  if (url.pathname.endsWith('.json') && !url.pathname.endsWith('manifest.webmanifest')) return;
  if (req.mode === 'navigate') { e.respondWith(fetch(req).then(r => { const c = r.clone(); caches.open(VERSION).then(x => x.put(req, c)); return r; }).catch(() => caches.match(req).then(h => h || caches.match('./index.html')))); return; }
  e.respondWith(caches.match(req).then(h => h || fetch(req)));
});
