const CACHE_NAME = 'financeiro-v1';

// Instala o Service Worker
self.addEventListener('install', (event) => {
  self.skipWaiting();
});

// Ativa e limpa caches antigos
self.addEventListener('activate', (event) => {
  event.waitUntil(clients.claim());
});

// Intercepta as requisições (Básico: busca na rede, se falhar, tenta cache)
self.addEventListener('fetch', (event) => {
  event.respondWith(
    fetch(event.request).catch(() => {
      return caches.match(event.request);
    })
  );
});

// Evento de Recebimento de Push
self.addEventListener('push', function (event) {
    const eventInfo = event.data.text();
    const data = event.data.json();
    const head = data.head || 'Lembrete Financeiro';
    const body = data.body || 'Hora de registrar seus gastos!';
    const icon = '/static/img/icon.png'; // Certifique-se que o caminho está certo

    event.waitUntil(
        self.registration.showNotification(head, {
            body: body,
            icon: icon,
            badge: icon,
            data: data.url || '/'
        })
    );
});

// Evento de Clique na Notificação
self.addEventListener('notificationclick', function (event) {
    event.notification.close();
    event.waitUntil(
        clients.openWindow(event.notification.data)
    );
});