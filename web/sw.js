/* LeSunshine 顧問 service worker
   - 資料（data/*.json）：網路優先，離線時用上次快取（加 X-From-Cache: 1 讓畫面顯示「離線」）
   - index.html / app.js / app.css / manifest：也是網路優先（改版會自動到手機），離線才用快取
   - 圖示：快取優先
   VERSION 只在想強制清掉舊快取時才需要改。 */
const VERSION = 'v2';
const SHELL_CACHE = 'fa-shell-' + VERSION;
const DATA_CACHE = 'fa-data';
const SHELL = [
  './', 'index.html', 'app.css', 'app.js', 'manifest.webmanifest',
  'icons/apple-touch-icon.png', 'icons/icon-192.png', 'icons/icon-512.png', 'icons/favicon-32.png'
];

self.addEventListener('install', (e) => {
  e.waitUntil(caches.open(SHELL_CACHE).then((c) => c.addAll(SHELL)).then(() => self.skipWaiting()));
});

self.addEventListener('activate', (e) => {
  e.waitUntil(
    caches.keys()
      .then((keys) => Promise.all(keys.filter((k) => k.startsWith('fa-shell-') && k !== SHELL_CACHE).map((k) => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

async function dataFirst(req) {
  const cache = await caches.open(DATA_CACHE);
  const key = new URL(req.url);
  key.search = '';
  try {
    const res = await fetch(req, { cache: 'no-store' });
    if (res.ok) await cache.put(key.href, res.clone());
    return res;
  } catch (err) {
    const hit = await cache.match(key.href);
    if (!hit) throw err;
    const headers = new Headers(hit.headers);
    headers.set('X-From-Cache', '1');
    return new Response(await hit.blob(), { status: 200, headers });
  }
}

async function shellFirst(req) {
  const cache = await caches.open(SHELL_CACHE);
  const hit = await cache.match(req, { ignoreSearch: req.mode === 'navigate' });
  if (hit) return hit;
  const res = await fetch(req);
  if (res.ok && res.type === 'basic') cache.put(req, res.clone());
  return res;
}

async function shellNetworkFirst(req) {
  const cache = await caches.open(SHELL_CACHE);
  const navigate = req.mode === 'navigate';
  try {
    const res = await fetch(req, navigate ? undefined : { cache: 'no-cache' });
    if (res.ok && res.type === 'basic') {
      // 首頁不管帶什麼 ?參數，都存成 './'
      await cache.put(navigate ? new URL('./', self.registration.scope).href : req, res.clone());
    }
    return res;
  } catch (err) {
    const hit = navigate
      ? (await cache.match(new URL('./', self.registration.scope).href)) || (await cache.match('index.html'))
      : await cache.match(req, { ignoreSearch: true });
    if (hit) return hit;
    throw err;
  }
}

self.addEventListener('fetch', (e) => {
  const req = e.request;
  if (req.method !== 'GET') return;
  const url = new URL(req.url);
  if (url.origin !== self.location.origin) return; // ESPN 圖片等外部資源交給瀏覽器
  const scope = new URL(self.registration.scope);
  const rel = url.pathname.slice(scope.pathname.length);
  if (rel.startsWith('data/') && rel.endsWith('.json')) {
    e.respondWith(dataFirst(req));
  } else if (req.mode === 'navigate' || rel === '' || /\.(html|js|css|webmanifest)$/.test(rel)) {
    e.respondWith(shellNetworkFirst(req));
  } else {
    e.respondWith(shellFirst(req).catch(() => caches.match('index.html', { ignoreSearch: true })));
  }
});
