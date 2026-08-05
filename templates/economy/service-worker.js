{% load i18n %}const CACHE = "kinkudos-app-shell-{{ app_version }}";
const OFFLINE_URL = "/offline/";
const SENSITIVE_PATHS = [
  "/setup/",
  "/prisijungti/",
  "/atsijungti/",
  "/slaptazodis/",
  "/susieti-irengini/",
  "/vaikas/",
];

function isSensitiveNavigation(url) {
  return SENSITIVE_PATHS.some(path => url.pathname.startsWith(path));
}

self.addEventListener("install", event => {
  event.waitUntil(caches.open(CACHE).then(cache => cache.addAll([OFFLINE_URL])));
  self.skipWaiting();
});

self.addEventListener("activate", event => {
  event.waitUntil(
    caches.keys().then(keys => Promise.all(keys.filter(key => key !== CACHE).map(key => caches.delete(key))))
  );
  self.clients.claim();
});

self.addEventListener("fetch", event => {
  if (event.request.method !== "GET" || event.request.mode !== "navigate") return;
  const url = new URL(event.request.url);
  if (url.origin !== self.location.origin || isSensitiveNavigation(url)) return;
  event.respondWith(fetch(event.request).catch(() => caches.match(OFFLINE_URL)));
});

self.addEventListener("push", event => {
  let data = { title: "{{ family_settings.display_name|escapejs }}", body: "{% translate "There is an update." %}", url: "/tevai/" };
  if (event.data) {
    try { data = { ...data, ...event.data.json() }; } catch (_) {}
  }
  event.waitUntil(
    Promise.all([
      self.registration.showNotification(data.title, {
        body: data.body,
        icon: "/static/icons/icon-192.png?v={{ app_version }}",
        badge: "/static/icons/badge-96.png?v={{ app_version }}",
        tag: data.tag || "family-app",
        data: { url: data.url }
      }),
      self.clients.matchAll({ type: "window", includeUncontrolled: true }).then(windows =>
        Promise.all(windows.map(client => client.postMessage({ type: "kinkudos-state-changed" })))
      )
    ])
  );
});

self.addEventListener("notificationclick", event => {
  event.notification.close();
  event.waitUntil(clients.openWindow(event.notification.data.url || "/tevai/"));
});
