// Deliberately no data cache: Core/auth/Registry responses always use network.
// Offline fallback has no account, synthetic entity, identity or funding data.
const OFFLINE = new URL('./offline.html', self.location.href).href;
self.addEventListener('install', event => {
  event.waitUntil(fetch(OFFLINE, {cache: 'reload', credentials: 'omit'}).then(response => {
    if (!response.ok) throw new Error('Offline fallback unavailable');
    return caches.open('hub69-offline-v2').then(cache => cache.put(OFFLINE, response));
  }));
});
self.addEventListener('activate', event => {
  event.waitUntil(caches.delete('hub69-offline-v1'));
});
self.addEventListener('fetch', event => {
  const url = new URL(event.request.url);
  const scope = new URL('./', self.location.href);
  // Never intercept API, auth, cross-origin or non-GET traffic, even navigation.
  if (event.request.method !== 'GET' || event.request.mode !== 'navigate' ||
      url.origin !== scope.origin || ![scope.pathname, scope.pathname + 'index.html'].includes(url.pathname)) return;
  event.respondWith(fetch(event.request).catch(async () => {
    const cache = await caches.open('hub69-offline-v2');
    return await cache.match(OFFLINE) || Response.error();
  }));
});
