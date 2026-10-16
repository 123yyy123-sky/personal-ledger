/* 记账本 Service Worker —— 让应用可离线打开、可安装到主屏
   注意：Service Worker 只在 https 或 localhost 下生效。直接双击打开本地文件（file://）时不会注册，属正常现象，不影响使用。 */
const CACHE = 'ledger-v4';
const ASSETS = [
  './',
  './个人记账本.html',
  './manifest.webmanifest',
  './icon-192.png',
  './icon-512.png'
];

self.addEventListener('install', function (e) {
  e.waitUntil(
    caches.open(CACHE)
      .then(function (c) { return c.addAll(ASSETS); })
      .catch(function () { /* 个别资源缺失时忽略，不阻断安装 */ })
      .then(function () { return self.skipWaiting(); })
  );
});

self.addEventListener('activate', function (e) {
  e.waitUntil(
    caches.keys()
      .then(function (keys) {
        return Promise.all(keys.filter(function (k) { return k !== CACHE; })
                               .map(function (k) { return caches.delete(k); }));
      })
      .then(function () { return self.clients.claim(); })
  );
});

/* 网络优先：拿得到就用最新的，拿不到就回退到缓存（离线可用） */
self.addEventListener('fetch', function (e) {
  if (e.request.method !== 'GET') return;
  e.respondWith(
    fetch(e.request)
      .then(function (res) {
        var copy = res.clone();
        caches.open(CACHE).then(function (c) { c.put(e.request, copy); }).catch(function () {});
        return res;
      })
      .catch(function () {
        return caches.match(e.request).then(function (hit) {
          return hit || caches.match('./个人记账本.html');
        });
      })
  );
});
