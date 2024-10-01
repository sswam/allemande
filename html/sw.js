const CACHE_NAME = 'allemande-ai-v1';
const urlsToCache = [
	'/',
	'/index.html',
	'/hello_css.css',
	'/hello_js.js',
	'/icon.svg',
	'/favicon.ico',
	'/apple-touch-icon.png',
	'/icon-192.png',
	'/icon-512.png'
];

self.addEventListener('install', event => {
	event.waitUntil(
		caches.open(CACHE_NAME)
			.then(cache => cache.addAll(urlsToCache))
	);
});

self.addEventListener('fetch', event => {
	event.respondWith(
		caches.match(event.request)
			.then(response => response || fetch(event.request))
	);
});
