"use strict";

const VERSION = "0.1.138";
const DEBUG = false;

console.log = DEBUG ? console.log : () => {};

const CACHE_NAME = "allemande-ai-" + VERSION;
const URLS_TO_CACHE = [
	"/",
	"/chat.js",
	"/util.js",
	"/mousetrap.min.js",
	"/allychat.css",
	"/chat.css",
	"/icon.png",
];

const CORS_URLS_TO_CACHE = [
	"https://allemande.ai/auth.js"
];

// Install event - cache resources
async function sw_install(event) {
	try {
		const cache = await caches.open(CACHE_NAME);
		
		// Cache local resources
		await cache.addAll(URLS_TO_CACHE);

		// Cache cross-origin resources with CORS mode
		for (const url of CORS_URLS_TO_CACHE) {
			console.log(`Caching CORS resource: ${url}`);
			const response = await fetch(url, { mode: 'cors', credentials: 'omit' });
			await cache.put(url, response);
			console.log(`Cached CORS resource: ${url}`);
		}

		// Activate the new service worker immediately
		await self.skipWaiting();
	} catch (error) {
		console.error(`Cache installation failed: ${error.message}`);
	}
	console.log(`Service worker installed, version ${VERSION}`);
}

// Activate event - clean old caches
async function sw_activate(event) {
	try {
		const cacheKeys = await caches.keys();
		for (const key of cacheKeys) {
			if (key !== CACHE_NAME) {
				await caches.delete(key);
			}
		}
		await self.clients.claim();
	} catch (error) {
		console.error(`Cache activation failed: ${error.message}`);
	}
}

// Fetch resource from cache or network
async function sw_fetch_cached(req) {
	const cached = await caches.match(req);
	if (cached) {
		console.log(`Cached resource: ${req.url}`);
		return cached;
	}
	console.log(`Fetching resource not found in cache: ${req.url}`);
	return await fetch(req, { mode: "cors" });
}

// Fetch event - serve GET and HEAD requests from cache or network
function sw_fetch(event) {
	console.log(`Fetch event: ${event.request.method} ${event.request.url}`);
	const req = event.request;
	if (!["GET", "HEAD"].includes(req.method)) {
		console.log(`Ignoring non-GET/HEAD request: ${req.method} ${req.url}`);
		return;
	}
	event.respondWith(sw_fetch_cached(req));
}

// Push event - handle incoming notifications
async function sw_push(event) {
	try {
		const data = event.data.json();
		const options = {
			body: data.body,
			icon: "/icon.png",
			badge: "/icon.png",
			data: {
				url: data.url
			}
		};

		await self.registration.showNotification("Allemande AI", options);
	} catch (error) {
		console.error(`Push notification failed: ${error.message}`);
	}
}

// Notification click event - handle user interaction
async function sw_notificationclick(event) {
	try {
		event.notification.close();
		const urlToOpen = event.notification.data.url || "/";
		const windowClients = await self.clients.matchAll({
			type: "window",
			includeUncontrolled: true
		});

		for (const client of windowClients) {
			if (client.url === urlToOpen && "focus" in client) {
				await client.focus();
				return;
			}
		}

		await self.clients.openWindow(urlToOpen);
	} catch (error) {
		console.error(`Notification click handling failed: ${error.message}`);
	}
}

// Communicate with main app

function sw_port_message(communicationPort, event) {
	if (event.data === "getAppInfo") {
		communicationPort.postMessage({
			type: "APP_INFO",
			version: VERSION,
			debug: DEBUG,
		});
	}
}

function sw_message(event) {
	if (event.data && event.data.type === 'PORT_INITIALIZATION') {
		const communicationPort = event.ports[0];
		communicationPort.onmessage = (event) => sw_port_message(communicationPort, event);
	}
}

self.addEventListener("install", sw_install);
self.addEventListener("activate", sw_activate);
self.addEventListener("fetch", sw_fetch);
self.addEventListener("push", sw_push);
self.addEventListener("notificationclick", sw_notificationclick);
self.addEventListener("message", sw_message);
