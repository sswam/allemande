// Register service worker ---------------------------------------------------

let sw_registration;
let sw_message_channel;
let reloading = false;

function reload_page() {
  if (reloading) return;
  reloading = true;
  location.reload();
}

function handle_sw_message(event) {
  if (event.data.type == "APP_INFO") {
    VERSION = event.data.version;
    const $debug = document.getElementById("debug");
    if ($debug)
      $debug.textContent = VERSION;
  }
}

function sw_updatefound() {
  const newWorker = sw_registration.installing;

  // Listen for state changes on the new service worker
  newWorker.addEventListener("statechange", sw_statechange);
}

function sw_statechange(ev) {
  if (ev.target.state === "activated")
    reload_page();
}

async function register_service_worker() {
//  console.log("Registering service worker");
  if (!navigator.serviceWorker) return;
  try {
    sw_registration = await navigator.serviceWorker.register("/service_worker.js", {"cache": "no-cache"});
  } catch (err) {
    console.error("ServiceWorker registration failed: ", err);
    return;
  }

  await navigator.serviceWorker.ready;

  sw_registration.addEventListener("updatefound", sw_updatefound);
  sw_registration.update();

  // Request the app version from the service worker
  sw_message_channel = new MessageChannel();
  sw_registration.active.postMessage({ type: "PORT_INITIALIZATION" }, [
    sw_message_channel.port2,
  ]);
  sw_message_channel.port1.onmessage = handle_sw_message;
  sw_message_channel.port1.postMessage("getAppInfo");

//  console.log("ServiceWorker registration successful with scope: ", sw_registration.scope);
  check_for_updates();
//  navigator.serviceWorker.addEventListener("controllerchange", reload_page);
}

let last_check_for_updates = 0;

function check_for_updates() {
  if (Date.now() - last_check_for_updates < 1000) {
    return;
  }
  last_check_for_updates = Date.now();
  // console.log("check_for_updates");
  if (sw_message_channel)
    sw_message_channel.port1.postMessage("checkForUpdates");
}
