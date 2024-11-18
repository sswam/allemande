"use strict";

const CACHE_NAME = "allemande-ai-v1";
const URLS_TO_CACHE = [
	"/",
	"/index.html",
	"/chat.js",
	"/util.js",
	"/mousetrap.min.js",
	"https://allemande.ai/allychat.css",
	"https://allemande.ai/chat.css",
	"/icon.png"
];

// Install event - cache resources
self.addEventListener("install", async (event) => {
	try {
		const cache = await caches.open(CACHE_NAME);
		await cache.addAll(URLS_TO_CACHE);
		await self.skipWaiting();
	} catch (error) {
		console.error(`Cache installation failed: ${error.message}`);
	}
});

// Activate event - clean old caches
self.addEventListener("activate", async (event) => {
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
});

// Fetch event - serve cached content when offline
self.addEventListener("fetch", async (event) => {
	try {
		const response = await fetch(event.request);
		return response;
	} catch (error) {
		const cachedResponse = await caches.match(event.request);
		if (cachedResponse) {
			return cachedResponse;
		}
		console.error(`Fetch failed: ${error.message}`);
	}
});

// Push event - handle incoming notifications
self.addEventListener("push", async (event) => {
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
});

// Notification click event - handle user interaction
self.addEventListener("notificationclick", async (event) => {
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
});
