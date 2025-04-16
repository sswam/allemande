"use strict";

// CONFIG

const VERSION = "0.5.49";
const DEBUG = false;

const subdomain = self.location.hostname.split(".")[0];

console.log = DEBUG ? console.log : () => {};

const CACHE_NAME = "allemande-ai-" + VERSION;

const URLS_TO_CACHE = {
  "chat": [
    "/",
    "manifest.json",
    "/allychat.css",
    "/chat.css",
    "/icon.png",
    "/util.js",
    "/config.js",
    "/notify.js",
    "/record.js",
    "/resizer.js",
    "/sw_register.js",
    "/chat.js",
    "/debug.js",
    "https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:ital,wght@0,100..700;1,100..700&display=swap",
  ],
  "rooms": [
    "/sw_register.js",
    "https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:ital,wght@0,100..700;1,100..700&display=swap",
  ],
};

const CORS_URLS_TO_CACHE = {
  "chat": [
    ALLEMANDE_URL + "/auth.js",
  ],
  "rooms": [
    "/allychat.css",
    "/room.css",
    "/util.js",
    "/print.js",
    "/debug.js",
    "/resizer.js",
    "/highlight.js",
    "/process_messages.js",
    "/room.js",
    "/voice.js",
//    "/d3.min.js",
//    "/wasm.min.js",
//    "/d3-graphviz.min.js",
//    "/graphvizlib.wasm",
//    "/mermaid.min.js",
  ].map((url) => ALLYCHAT_CHAT_URL + url),
};

// Install event - cache resources
async function sw_install_3(event) {
  const cache = await caches.open(CACHE_NAME);

  // Cache local resources
  // await cache.addAll(URLS_TO_CACHE);
  await Promise.all(
    URLS_TO_CACHE[subdomain].map(async (url) => {
      const response = await fetch(url, {cache: "no-cache"});
      if (response.redirected) {
        console.log(`Skipped caching redirect for: ${url}`);
      } else {
        await cache.put(url, response);
        console.log(`Cached resource: ${url}`);
      }
    })
  );

  // Cache cross-origin resources with CORS mode
  for (const url of CORS_URLS_TO_CACHE[subdomain]) {
    console.log(`Caching CORS resource: ${url}`);
    const response = await fetch(url, { cache: "no-cache", mode: "cors", credentials: "omit" });
    if (!response.redirected) {
      await cache.put(url, response);
      console.log(`Cached CORS resource: ${url}`);
    } else {
      console.log(`Skipped caching redirect for: ${url}`);
    }
  }

  // Activate the new service worker immediately
  await self.skipWaiting();
}

async function sw_install_2(event) {
  try {
    await sw_install_3(event);
  } catch (err) {
    console.error(`Cache installation failed: ${err.message}`);
  }
  console.log(`Service worker installed, version ${VERSION}`);
}

async function sw_install(event) {
  event.waitUntil(sw_install_2(event));
}

// Activate event - clean old caches
async function sw_activate_3(event) {
  const cacheKeys = await caches.keys();
  for (const key of cacheKeys) {
    if (key !== CACHE_NAME) {
      await caches.delete(key);
    }
  }
  await self.clients.claim();
}

async function sw_activate_2(event) {
  try {
    await sw_activate_3(event);
  } catch (err) {
    console.error(`Cache activation failed: ${err.message}`);
  }
}

async function sw_activate(event) {
  event.waitUntil(sw_activate_2(event));
}

// Fetch resource from network
async function sw_fetch_from_network(req, options) {
  console.log(`Fetching from network: ${req.url}`);
  const response = await fetch(req, options);
  console.log(`Network response: ${req.url}`, response.status);
  return response;
}

// Fetch resource from cache or network
async function sw_fetch_from_cache_or_network(req) {
  const cached = await caches.match(req);
  if (cached) {
    console.log(`Returning cached resource: ${req.url}`);
    return cached;
  }
  const options = {};
  // list of domains to avoid cors mode
  const no_cors_domains = ["https://fonts.googleapis.com", "https://fonts.gstatic.com"];
  const app_domains = [ALLYCHAT_CHAT_URL, ALLYCHAT_ROOMS_URL];
  const is_app_domain = app_domains.some((domain) => req.url.startsWith(domain));
  const is_no_cors_domain = !is_app_domain && no_cors_domains.some((domain) => req.url.startsWith(domain));
  if (!is_no_cors_domain)
    options.mode = "cors";
  if (!is_app_domain)
    options.credentials = "omit";
  return await sw_fetch_from_network(req, options);
}

// Fetch event - serve GET and HEAD requests from cache or network
function sw_fetch(event) {
  console.log(`Fetch event: ${event.request.method} ${event.request.url}`);
  const req = event.request;
  if (!["GET", "HEAD"].includes(req.method)) {
    console.log(`Ignoring non-GET/HEAD request: ${req.method} ${req.url}`);
    return;
  }
  event.respondWith(sw_fetch_from_cache_or_network(req));
}

// Push event - handle incoming notifications
async function sw_push(event) {
  const data = event.data.json();
  const options = {
    body: data.body,
    icon: "https://allemande.ai/icon.png",
    badge: "https://allemande.ai/icon.png",
    data: {
      room: data.room,
      url: data.url, // not needed, just use room?
      // TODO anchor to a specific message
    },
  };

  event.waitUntil(self.registration.showNotification("Allemande AI", options));
}

// Notification click event - handle user interaction
async function sw_notificationclick(event) {
  event.notification.close();
  //	const urlToOpen = event.notification.data.url || "/";
  const urlToOpen = `/#${event.notification.data.room}`;

  const windowClients = await self.clients.matchAll({
    type: "window",
    includeUncontrolled: true,
  });

  for (const client of windowClients) {
    if (client.url === urlToOpen && "focus" in client) {
      await client.focus();
      return;
    }
  }

  event.waitUntil(self.clients.openWindow(urlToOpen));
}

// Check for updates
// TODO possibly debounce this?
async function check_for_updates() {
  try {
    const registration = await self.registration;
    await registration.update();
    return true;
  } catch (err) {
    console.error("Update check failed:", err);
    return false;
  }
}

// Communicate with main app

function sw_port_message(communicationPort, event) {
  const command = event.data;

  if (command === "getAppInfo") {
    communicationPort.postMessage({
      type: "APP_INFO",
      version: VERSION,
      debug: DEBUG,
    });
    return;
  }

  if (command === "checkForUpdates") {
    check_for_updates();
    return;
  }
}

function sw_receive_message(event) {
  if (event.data && event.data.type === "PORT_INITIALIZATION") {
    const communicationPort = event.ports[0];
    communicationPort.onmessage = (event) =>
      sw_port_message(communicationPort, event);
  }
}

// Event listeners

self.addEventListener("install", sw_install);
self.addEventListener("activate", sw_activate);
self.addEventListener("fetch", sw_fetch);
self.addEventListener("push", sw_push);
self.addEventListener("notificationclick", sw_notificationclick);
self.addEventListener("message", sw_receive_message);
