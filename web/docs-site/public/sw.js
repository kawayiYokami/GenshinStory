const CACHE_NAME = 'zhihuigong-v1';
const urlsToCache = [
const urlsToCache = [
  '/',                    // 根路径
  '/nahida-icon.svg'     // 图标文件（如果存在）
];
  '/nahida-icon.svg'     // 图标文件（如果存在）
];

// Install a service worker
self.addEventListener('install', event => {
  console.log('Service Worker: Installing...');
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => {
        console.log('Service Worker: Cache opened, adding files...');

        // 添加文件到缓存，逐个处理以避免单个失败影响整体
        const cachePromises = urlsToCache.map(url => {
          return cache.add(url).catch(error => {
            console.warn(`Service Worker: Failed to cache ${url}:`, error);
            // 继续处理其他文件，不让单个失败中断安装
            return Promise.resolve();
          });
        });

        return Promise.all(cachePromises);
      })
      .then(() => {
        console.log('Service Worker: All files cached successfully');
      })
      .catch(error => {
        console.error('Service Worker: Cache installation failed:', error);
      })
  );
});

// 缓存策略：优先使用缓存，回退到网络
self.addEventListener('fetch', event => {
  event.respondWith(
    caches.match(event.request)
      .then(response => {
        if (response) {
          return response;
        }
        return fetch(event.request).then(fetchResponse => {
          // 只缓存成功的 GET 请求
          if (event.request.method === 'GET' && fetchResponse.ok) {
            // 可选择性地缓存新获取的资源
            // caches.open(CACHE_NAME).then(cache => cache.put(event.request, fetchResponse.clone()));
          }
          return fetchResponse;
        });
      })
      .catch(error => {
        console.error('Service Worker: Fetch failed:', error);
        throw error;
      })
  );
});

// 清理旧缓存
self.addEventListener('activate', event => {
  console.log('Service Worker: Activating...');
  event.waitUntil(
    caches.keys().then(cacheNames => {
      return Promise.all(
        cacheNames.map(cacheName => {
          if (cacheName !== CACHE_NAME) {
            console.log(`Service Worker: Deleting old cache: ${cacheName}`);
            return caches.delete(cacheName);
          }
        })
      );
    }).then(() => {
      console.log('Service Worker: Old caches cleaned up');
    })
  );
});