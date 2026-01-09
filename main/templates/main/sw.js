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