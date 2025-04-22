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
    else
      module = await import(src);
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

// helper functions ----------------------------------------------------------

function getForegroundColorWithOpacity(opacity) {
  return hexColorWithOpacity(getCssVarColorHex('--text'), opacity);
}

function getCssVarColorHex(varName = '--text') {
    const temp = document.createElement('div');
    temp.style.color = getComputedStyle(document.body).getPropertyValue(varName);
    document.body.appendChild(temp);
    const rgb = getComputedStyle(temp).color;
    document.body.removeChild(temp);
    const match = rgb.match(/^rgb\((\d+),\s*(\d+),\s*(\d+)\)$/);
    if (!match) return '#808080';
    const hex = '#' + match.slice(1).map(x =>
        parseInt(x).toString(16).padStart(2, '0')
    ).join('');
    return hex;
}

function hexColorWithOpacity(color, opacity) {
    const alpha = Math.round(opacity * 255);
    return color + alpha.toString(16).padStart(2, '0');
}

function previous(selector, lookBack = 0) {
	// Get all elements matching the selector
	const elements = Array.from(document.querySelectorAll(selector));

	// Find elements before the script
	const beforeScript = elements.filter(element =>
		!(document.currentScript.compareDocumentPosition(element) & Node.DOCUMENT_POSITION_FOLLOWING)
	);

	// If no elements found before script, return null
	if (!beforeScript.length) return null;

	// Get the element at the specified lookBack position from the end
	const index = beforeScript.length - 1 - lookBack;
	return index >= 0 ? beforeScript[index] : null;
}
