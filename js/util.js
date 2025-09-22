// Utility functions, by Github Copilot.

const $ = (selector) => document.querySelector(selector);
const $$ = (selector) => document.querySelectorAll(selector);
const $id = (id) => document.getElementById(id);
const $create = (element) => document.createElement(element);
const $text = (text) => document.createTextNode(text);
const $attr = (element, attribute, value) => element.setAttribute(attribute, value);
const $append = (parent, child) => parent.appendChild(child);
const $remove = (element) => element.parentNode.removeChild(element);
const $replace = (oldElement, newElement) => oldElement.parentNode.replaceChild(newElement, oldElement);
const $empty = (element) => element.innerHTML = '';
const $on = (element, event, handler, options) => element.addEventListener(event, handler, options);
const $off = (element, event, handler) => element.removeEventListener(event, handler);
const $dispatch = (element, event) => element.dispatchEvent(new Event(event));
const $animate = (element, animation, callback) => {
  element.classList.add('animated', animation);
  element.addEventListener('animationend', () => {
    element.classList.remove('animated', animation);
    if (callback) callback();
  });
}
const $wait = (time) => new Promise((resolve) => setTimeout(resolve, time||0));
const $waitUntil = (condition, time) => new Promise((resolve) => {
  const interval = setInterval(() => {
    if (condition()) {
      clearInterval(interval);
      resolve();
    }
  }, time);
});
const $waitUntilElement = (selector, time) => $waitUntil(() => $(selector), time);
const $waitUntilElementRemoved = (selector, time) => $waitUntil(() => !$(selector), time);
const $waitUntilElementVisible = (selector, time) => $waitUntil(() => $(selector).offsetWidth > 0 && $(selector).offsetHeight > 0, time);
const $waitUntilElementHidden = (selector, time) => $waitUntil(() => $(selector).offsetWidth === 0 && $(selector).offsetHeight === 0, time);
const $waitUntilElementText = (selector, text, time) => $waitUntil(() => $(selector).innerText === text, time);
const $waitUntilElementAttribute = (selector, attribute, value, time) => $waitUntil(() => $(selector).getAttribute(attribute) === value, time);

async function $get(url, options = {}) {
  const url_with_time = url + (url.includes('?') ? '&' : '?') + 't=' + Date.now();
  const response = await fetch(url_with_time, options);
  if (!response.ok)
    throw new Error(`$get failed: ${response.status} ${response.statusText}`);
  return await response.text();
}

const $script = async (id, src) => {
  if ($id(id))
    return;
  await new Promise((resolve, reject) => {
    const script = document.createElement("script");
    script.id = id;
    script.src = src;
    script.type = "text/javascript";
    script.onload = () => resolve();
    script.onerror = () => reject(new Error(`Failed to load script: ${src}`));
    document.head.appendChild(script);
  });
}

const $style = async (id, href) => {
  if ($id(id))
    return;
  await new Promise((resolve, reject) => {
    const link = document.createElement("link");
    link.id = id;
    link.rel = "stylesheet";
    link.href = href;
    link.type = "text/css";
    link.onload = () => resolve();
    link.onerror = () => reject(new Error(`Failed to load stylesheet: ${href}`));
    document.head.appendChild(link);
  });
}

function encode_entities(txt) {
  return txt.replace(/[&<>"']/g, c => ({
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    '"': '&quot;',
//    "'": '&#39;'
  })[c]);
}

window.modules = {};

/**
* Dynamic module import utility with caching and load state management
* @param {string} id - Module identifier/name
* @param {string} [src] - Optional source path (defaults to id if not provided)
* @returns {Promise<Module>} The imported module
*/
async function $import(id, src) {
  [ id, src ] = _get_module_real_id_and_src(id, src);

  let module = modules[id];

  // I'm not sure if the pending / notification stuff is necessary
  // it might be redundant with the import() function
  // but we need some cross-domain import hack anyway so we'll need it I guess.

  if (!module)
    module = await _import_real(id, src);

  // Check if module is already in loading state
  if (module.import_onload) {
    // Wait for module to finish loading if it's in progress
    await new Promise((resolve) => {
      module.import_onload.push(resolve);
    });
    module = modules[id];
  }

  // Check if module failed to load
  if (module.import_error)
    throw module.import_error;

  // Return module
  return module;
}

function _get_module_real_id_and_src(id, src) {
  // Check for chat: prefix
  if (id.startsWith("chat:")) {
    id = id.substring(5);
    src = ALLYCHAT_CHAT_URL + "/" + id;
  } else {
    src = src || id;
  }

  // Add .js extension if not present
  if (!src.endsWith(".js"))
    src += ".js";

  // Add relative path prefix if no path separator present
  if (!src.includes("/"))
    src = `./${src}`;

  // Chop off numeric mtime from id if present
  id = id.replace(/\.\d+/, "");

  return [ id, src ];
}

async function _import_real(id, src) {
  // Initialize loading state
  modules[id] = { import_onload: [] };

  // Perform the actual module import
  try {
    // check for cross-domain import
    if (src.startsWith("https://") && !src.startsWith(location.origin + "/"))
      module = await _import_cross_domain(src);
    else {
      // console.log("import module: ", src);
      module = await import(src);
    }
  } catch (error) {
    // Handle import error
    module = { "import_error": error };
    console.error(`Failed to import module: ${id} from ${src}`, error);
  }

  // Get the onload callbacks
  const callbacks = modules[id].import_onload;

  // Cache the loaded module
  modules[id] = module;

  // Call the init function if it exists; may be async or not
  if (module.init) 
    await Promise.resolve(module.init());                                      

  // Resolve all pending load promises
  for (const resolve of callbacks)
    resolve(module);

  return module;
}

async function _import_cross_domain(url) {
  // console.log("import module cross-domain: ", url);
  const response = await fetch(url, { credentials: 'include' });

  if (!response.ok)
    throw new Error(`${response.status} ${response.statusText}`);

  const contentType = response.headers.get('content-type');
  if (!contentType || !contentType.includes('javascript'))
     throw new Error(`Invalid content type: ${contentType}`);

  const scriptText = await response.text();

  // Create a Blob URL
  const blob = new Blob([scriptText], { type: 'application/javascript' });
  const blobUrl = URL.createObjectURL(blob);

  // Dynamically import the Blob URL
  const module = await import(blobUrl);

  // Revoke the Blob URL
  URL.revokeObjectURL(blobUrl);

  return module;
}

function show(element, do_show) {
  if (typeof element === "string")
    element = $id(element);
  if (do_show === undefined || do_show)
    element.classList.remove("hidden");
  else
    element.classList.add("hidden");
}

function hide(element) {
  show(element, false);
}

function toggle(element, do_show) {
  if (typeof element === "string")
    element = $id(element);
  if (do_show === undefined)
    do_show = element.classList.contains("hidden");
  show(element, do_show);
}

function is_hidden(element) {
  return window.getComputedStyle(element).display === 'none';
}

function is_showing(element) {
  return !is_hidden(element);
}

function enable_link(element, enabled) {
  if (typeof element === "string")
    element = $id(element);
  element.classList.toggle("disabled", !enabled);
  element.ariaDisabled = !enabled;
}

function isPrecedingNode(node1, node2) {
  return (
    node1.compareDocumentPosition(node2) & Node.DOCUMENT_POSITION_FOLLOWING
  );
}

function reload_page() {
  if (reloading) return;
  reloading = true;
  location.reload();
}

// Hook system ---------------------------------------------------------------

const hooks = {};

function add_hook(name, func) {
  if (!hooks[name])
    hooks[name] = [];
  if (!hooks[name].includes(func))
    hooks[name].push(func);
}

function remove_hook(name, func) {
  if (!hooks[name])
    return;
  hooks[name] = hooks[name].filter((f) => f !== func);
}

function run_hooks(name, ...args) {
  if (!hooks[name])
    return;
  for (const func of hooks[name])
    func(...args);
}

// Mutex system ---------------------------------------------------------------

class Mutex {
  constructor() {
    this.current = Promise.resolve();
  }

  async lock(fn) {
    let old = this.current;
    let unlock;
    this.current = new Promise(resolve => unlock = resolve);
    await old;
    try {
      return await fn();
    } finally {
      unlock();
    }
  }
}

// fullscreen API -------------------------------------------------------------

function is_fullscreen() {
  return document.fullscreenElement;
}

function go_fullscreen(target) {
  if (is_fullscreen())
    return;
  target = target || document.documentElement;
  target.requestFullscreen().catch((err) => console.error(err));
}

function exit_fullscreen() {
  if (!is_fullscreen())
    return;
  document.exitFullscreen().catch((err) => console.error(err));
}

async function waitForMessage(element) {
  const process_messages = await $import("chat:process_messages");
  const message = element.closest('div.message');
  if (!message)
    return;
  await process_messages.processMessage(message);
}

// colours -------------------------------------------------------------------

// TODO consider using my custom RGB <-> HSL functions that might work better

function clamp(v, low, high) {
  return Math.min(Math.max(v, low), high);
}

// Standard HSL to RGB conversion function
function hslToRgb(h, s, l) {
  let r, g, b;

  if (s === 0) {
    r = g = b = l; // achromatic
  } else {
    const hue2rgb = (p, q, t) => {
      if (t < 0) t += 1;
      if (t > 1) t -= 1;
      if (t < 1/6) return p + (q - p) * 6 * t;
      if (t < 1/2) return q;
      if (t < 2/3) return p + (q - p) * (2/3 - t) * 6;
      return p;
    };

    const q = l < 0.5 ? l * (1 + s) : l + s - l * s;
    const p = 2 * l - q;

    r = hue2rgb(p, q, h / 360 + 1/3);
    g = hue2rgb(p, q, h / 360);
    b = hue2rgb(p, q, h / 360 - 1/3);
  }

  return {
    r: clamp(Math.floor(r * 256), 0, 255),
    g: clamp(Math.floor(g * 256), 0, 255),
    b: clamp(Math.floor(b * 256), 0, 255),
  };
}

// service worker trouble ----------------------------------------------------

async function deregister_service_worker() {
  if (!navigator.serviceWorker)
    return;
  const registrations = await navigator.serviceWorker?.getRegistrations() || [];
  for (const registration of registrations) {
    await registration.unregister();
  }
}

// timing patterns -----------------------------------------------------------

// not in use now
const debounce = (fn, delay) => {
  let timeoutId;

  return function(...args) {
    const context = this;
    clearTimeout(timeoutId);
    timeoutId = setTimeout(() => fn.apply(context, args), delay);
  };
};
