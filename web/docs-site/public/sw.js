const CACHE_NAME = 'zhihuigong-v3';
const urlsToCache = [
  '/',
  '/nahida-icon.svg'
];

// Install a service worker
self.addEventListener('install', event => {
  // 强制跳过等待，立即激活，确保新版本 SW 能够迅速接管
  self.skipWaiting();

  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => {
        return Promise.all(
          urlsToCache.map(url => {
            return cache.add(url).catch(error => {
              console.warn(`[SW] Failed to cache ${url}:`, error);
              return Promise.resolve();
            });
          })
        );
      })
  );
});

// 缓存策略
self.addEventListener('fetch', event => {
  // 1. 对于 HTML 页面 (Navigation)：网络优先，失败回退到缓存
  // 这样确保用户总是获取最新的 index.html，避免 404 错误
  if (event.request.mode === 'navigate') {
    event.respondWith(
      fetch(event.request)
        .then(response => {
          // 网络请求成功，更新缓存并返回
          if (response.status === 200) {
            const responseClone = response.clone();
            caches.open(CACHE_NAME).then(cache => {
              cache.put(event.request, responseClone);
            });
          }
          return response;
        })
        .catch(() => {
          // 网络请求失败（离线），使用缓存
          return caches.match(event.request);
        })
    );
    return;
  }

  // 2. 对于其他静态资源 (CSS/JS/Images)：缓存优先，回退到网络
  event.respondWith(
    caches.match(event.request)
      .then(response => {
        if (response) {
          return response;
        }
        return fetch(event.request);
      })
  );
});

// 清理旧缓存并立即接管
self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(cacheNames => {
      return Promise.all(
        cacheNames.map(cacheName => {
          if (cacheName !== CACHE_NAME) {
            return caches.delete(cacheName);
          }
        })
      );
    }).then(() => {
      // 立即接管所有客户端页面，让更新立即生效
      return self.clients.claim();
    })
  );
});