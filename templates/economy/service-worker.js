const DEFAULT_NOTIFICATION_TITLE = "KinKudos";
const DEFAULT_NOTIFICATION_BODY = "There is an update.";

// Keep document navigation on the network; this worker handles Push and
// lightweight client update signals only.
self.addEventListener("install", () => {
  self.skipWaiting();
});

self.addEventListener("activate", event => {
  event.waitUntil(self.clients.claim());
});

function notifyOpenClients() {
  return self.clients.matchAll({ type: "window", includeUncontrolled: true }).then(windows =>
    Promise.all(
      windows.map(client =>
        Promise.resolve().then(() => client.postMessage({ type: "kinkudos-state-changed" })).catch(() => {})
      )
    )
  );
}

self.addEventListener("push", event => {
  let data = {
    title: DEFAULT_NOTIFICATION_TITLE,
    body: DEFAULT_NOTIFICATION_BODY,
    url: "/tevai/",
  };
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
      notifyOpenClients()
    ])
  );
});

self.addEventListener("notificationclick", event => {
  event.notification.close();
  event.waitUntil(clients.openWindow(event.notification.data.url || "/tevai/"));
});
