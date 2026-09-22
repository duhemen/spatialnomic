const CACHE = 'spatianomics-v2';
const URLS = ['/', '/dashboard', '/peta', '/prediksi', '/laporan',
              '/static/css/app.css', '/static/js/common.js',
              '/static/js/map.js', '/static/js/charts.js'];

self.addEventListener('install', e => {
  e.waitUntil(caches.open(CACHE).then(c => c.addAll(URLS)));
});
self.addEventListener('fetch', e => {
  e.respondWith(
    caches.match(e.request).then(r => r || fetch(e.request).catch(() => caches.match('/dashboard')))
  );
});