const CACHE_NAME = 'school-pos-v1';
const urlsToCache = [
    '/',
    '/static/css/style.css',
    '/static/js/script.js',
    '/static/images/',
    '/student_login',
    '/shop_login'
];

self.addEventListener('install', function(event) {
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then(function(cache) {
                return cache.addAll(urlsToCache);
            })
    );
});

self.addEventListener('fetch', function(event) {
    event.respondWith(
        caches.match(event.request)
            .then(function(response) {
                if (response) {
                    return response;
                }
                return fetch(event.request);
            })
    );
});