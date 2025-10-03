const offline_timeout_seconds = 10;

const isMobile = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
// const isFirefox = /Firefox/i.test(navigator.userAgent);
const inIframe = window.parent !== window.self;

let file_type;
let room;

let $body, $messages, $overlay, $messages_wrap, $canvas_div;

let offline_timeout;

let overlay_mode = false;
let $currentImg;
let currentImgIndex;
let allImages;
// let overlay_fullscreen = isMobile;
let overlay_fullscreen = false;

let suppressInitialScroll = true;

let simple = true;

export let view_options = {
  images: 1,
  image_size: 8,
  font_size: 4,
  items: 10,
  advanced: -1,
};

let mode_options = {
  select: 0,
};

let snapshot = false;

let filter = '';

// status indicator ----------------------------------------------------------

function get_status_element() {
  let status = $id("allemande_status");
  if (!status) {
    status = $create("div");
    status.id = "allemande_status";
    $append(document.lastChild, status);
    hide(status);
    $on(status, "click", reload);
  }
  return status;
}

function reload() {
  window.location.reload();
}

function clean_up_server_events() {
  for (const $e of $$("script.event"))
    $e.remove();
}

export function online() {
  // console.log("online");
  if (snapshot)
    return;
  clearTimeout(offline_timeout);
  offline_timeout = setTimeout(offline, 1000 * offline_timeout_seconds);
  const status = get_status_element();
  //	status.innerText = '🔵';
  status.innerText = "";
  hide(status);
  clean_up_server_events();
}

function offline() {
  // console.log("offline!");
  if (snapshot)
    return;
  const status = get_status_element();
  status.innerText = "🔴";
  if (view_options.advanced <= 0)
    status.innerText += " disconnected; reload!";
  show(status);
  for (const evname of ["mouseenter", "mousemove", "click", "touchstart"]) 
    document.body.addEventListener(evname, reload);
}

export function clear() {
  $("div.messages").innerHTML = "";
  clean_up_server_events();
}

function ready_state_change() {
  /* This does not work now, who knows why */
  // console.log("ready state change", document.readyState);
  if (document.readyState !== "loading") {
    offline();
  }
}

function load_error() {
  // console.log("load error");
  /* Never seen this work */
  offline();
}

// scrolling to the bottom ---------------------------------------------------

let messages_at_bottom = false;
let messages_width_last;
let messages_height_last;
let top_message;

function is_at_bottom($e) {
  if (view_options.columns) {
    return Math.abs($e.scrollWidth - $e.scrollLeft - $e.clientWidth) < 8;
  } else {
    return Math.abs($e.scrollHeight - $e.scrollTop - $e.clientHeight) < 8;
  }
  return bot;
}

function scroll_to_bottom($e) {
  if (view_options.columns) {
    // console.log("scroll to right");
    $e.scrollLeft = $e.scrollWidth;
  } else {
    $e.scrollTop = $e.scrollHeight;
  }
}

const INSTANT_SCROLL_THRESHOLD = 1000; // 1 second
const DEBOUNCE_DELAY = 100; // 100ms
const DEBOUNCE_MESSAGE_COUNT = 2;
const SCROLL_BACK_PIXELS = 200; // pixels to scroll up to disable auto-scroll
const SCROLL_BACK_COUNT = 2; // number of scroll up events to disable auto-scroll

let lastMessageTime = 0;
let messageCount = 0;
let scrollUpEventCount = 0;
let isDebouncing = false;

const debounce = (fn, delay) => {
  let timeoutId;
  return () => {
    clearTimeout(timeoutId);
    timeoutId = setTimeout(() => fn(), delay);
  };
};

// Create both debounced and non-debounced versions
const messages_scrolled_debounced = debounce(messages_scrolled_2, DEBOUNCE_DELAY);

let prev_scrollTop = 0;
let prev_scrollLeft = 0;

// Wrapper function to handle adaptive scrolling behavior
async function messages_scrolled() {
  const currentTime = Date.now();
  const timeSinceLastMessage = currentTime - lastMessageTime;

  await wait_for_load();
  var $e = $messages_wrap;
  if (!$e) return;

  // Get current dimensions
  const currentHeight = $e.scrollHeight;
  const currentWidth = $e.scrollWidth;

  // Check if dimensions grew (new message)
  const newMessages = view_options.columns ?
    (currentWidth > messages_width_last) :
    (currentHeight > messages_height_last);

  if (newMessages) {
    lastMessageTime = currentTime;
    messageCount++;

    // If it's been more than 1 second since last message, reset to instant mode
    if (timeSinceLastMessage > INSTANT_SCROLL_THRESHOLD) {
      messageCount = 1;
      isDebouncing = false;
    }

    // Switch to debounced mode if we get several messages quickly
    if (messageCount >= DEBOUNCE_MESSAGE_COUNT && timeSinceLastMessage < DEBOUNCE_DELAY) {
      isDebouncing = true;
    }
  }

  // Call either debounced or instant version
  if (isDebouncing) {
    // if (newMessages) {
    //   // scroll on just 1px to indicate that we will be scrolling
    //   if (view_options.columns)
    //     $e.scrollLeft += 1;
    //   } else {
    //     $e.scrollTop += 1;
    //   }
    // }
    messages_scrolled_debounced();
  } else {
    messages_scrolled_2();
  }

  // If scrolling up, set messages_at_bottom to false
  if (!newMessages) {
    const scrollDeltaX = prev_scrollLeft - $e.scrollLeft;
    const scrollDeltaY = prev_scrollTop - $e.scrollTop;
    const didScrollLeft = view_options.columns && scrollDeltaX < 0;
    const didScrollUp = !view_options.columns && scrollDeltaY < 0;

    if (didScrollLeft || didScrollUp)
      scrollUpEventCount++;
    else
      scrollUpEventCount = 0;

    if (scrollUpEventCount >= SCROLL_BACK_COUNT || (view_options.columns ? scrollDeltaX : scrollDeltaY) > SCROLL_BACK_PIXELS) {
      set_messages_at_bottom(false);
      scrollUpEventCount = SCROLL_BACK_COUNT; // cap it
    }
  }
  prev_scrollLeft = $e.scrollLeft;
  prev_scrollTop = $e.scrollTop;
}

// Original scroll handling function
async function messages_scrolled_2() {
  await wait_for_load();
  var $e = $messages_wrap;
  if (!$e) return;

  // Check if we need to auto-scroll when in column view mode
  if (messages_at_bottom && view_options.columns) {
    var messages_width = $e.scrollWidth;
    if (messages_width != messages_width_last) {
      messages_width_last = messages_width;
      if (!suppressInitialScroll) {
        scroll_to_bottom($e);
      }
    }
  // Check if we need to auto-scroll in regular view mode
  } else if (messages_at_bottom) {
    var messages_height = $e.scrollHeight;
    if (messages_height != messages_height_last) {
      messages_height_last = messages_height;
      if (!suppressInitialScroll) {
        scroll_to_bottom($e);
      }
    }
  } else {
    set_messages_at_bottom(is_at_bottom($e));
  }
  //console.log(messages_at_bottom);

  // Track the first visible message based on view mode
  if (view_options.columns) {
    top_message = getLeftmostVisibleElement();
  } else {
    top_message = getTopmostVisibleElement();
  }
}

function set_messages_at_bottom(at_bottom) {
  // console.log("set_messages_at_bottom", messages_at_bottom);
  if (at_bottom != messages_at_bottom) {
    messages_at_bottom = at_bottom;
    window.parent.postMessage({type: "status", messages_at_bottom: messages_at_bottom}, ALLYCHAT_CHAT_URL);
  }
}

function getTopmostVisibleElement() {
  // If half visible, round to nearest element
  const container = $messages_wrap;
  const elements = container.querySelectorAll('.message');

  // Get container's top boundary
  const containerTop = container.scrollTop;

  // Find first element that's visible
  for (const element of elements) {
    const rect = element.getBoundingClientRect();
    const elementTop = element.offsetTop - container.offsetTop;
    const elementMiddle = elementTop + rect.height / 2;

    if (elementMiddle >= containerTop) {
      return element;
    }
  }

  return null;
}

function getLeftmostVisibleElement() {
  // If half visible, round to nearest element
  const container = $messages_wrap;
  const elements = container.querySelectorAll('.message');

  // Get container's left boundary
  const containerLeft = container.scrollLeft;

  // Find first element that's visible
  for (const element of elements) {
    const rect = element.getBoundingClientRect();
    const elementLeft = element.offsetLeft - container.offsetLeft;
    const elementMiddle = elementLeft + rect.width / 2;

    if (elementMiddle >= containerLeft) {
      return element;
    }
  }
}

// wait for ------------------------------------------------------------------

// TODO move to util.js

async function wait_for(predicate, timeout) {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeout);
  let count = 0;

  try {
    while (!predicate()) {
      if (controller.signal.aborted) {
        throw new Error("timeout");
      }
      count++;
      await new Promise(resolve => requestAnimationFrame(resolve));
    }
  } finally {
    clearTimeout(timeoutId);
  }

  // console.log("wait_for", count);
}

function node_has_next_sibling(node) {
  return node.nextSibling;
}

async function wait_for_whole_message(node) {
  try {
    await wait_for(() => node_has_next_sibling(node), 5000);   // newline works
  } catch (e) {
    console.error("timeout waiting for next sibling (newline)", node, e);
    return false;
  }
  return true;
}

function check_for_new_messages(mutations) {
  const new_content = [];
  for (const mutation of mutations) {
    if (mutation.type != "childList") {
      continue;
    }
    for (const node of mutation.addedNodes) {
      if (
        node.nodeType == Node.ELEMENT_NODE &&
        node.tagName == "DIV" && node.classList.contains("message")
      ) {
        new_content.push(node);
      }
    }
  }
  return new_content;
}

async function wait_for_messages_to_load(elements) {
  for (const element of elements) {
    await wait_for_whole_message(element);
  }
}

// mutation observer ---------------------------------------------------------

const mutationMutex = new Mutex();

async function call_process_messages(messages) {
  await wait_for_load();
  if (messages === undefined)
    messages = $messages.querySelectorAll(".message");
  await wait_for_messages_to_load(messages);
  online();
  messages_resized();
  const process_messages = await $import("chat:process_messages");
  await process_messages.process_messages(messages);
}

async function mutated(mutations) {
  const messages = check_for_new_messages(mutations);
  if (messages.length)
    await mutationMutex.lock(() => call_process_messages(messages));
}

function setup_mutation_observer() {
  new MutationObserver(mutated).observe($("html"), {
    childList: true,
    subtree: true,
  });
}

async function process_current_messages() {
  await mutationMutex.lock(call_process_messages);
}

// keyboard shortcuts --------------------------------------------------------

const keysToKeep = [
  "Control",
  "Shift",
//  "Alt",
  "Meta",
  "ArrowUp",
  "ArrowDown",
  "ArrowLeft",
  "ArrowRight",
  "Home",
  "End",
  "PageUp",
  "PageDown",
  "F3", // find
  "F5", // refresh
  "F6", // focus address bar
  "F7", // caret browsing
  "F10", // menu bar
  "F11", // full screen
  "F12", // developer tools
];
const ctrlKeysToKeep = [
  "c", // copy
  "v", // paste
  "x", // cut
  "z", // undo
  "y", // redo
  "a", // select all
  "f", // find
  "h", // history
  "0" // reset zoom
];

let grab_mode = false;

function toggle_grab() {
  grab_mode = !grab_mode;
  $body.classList.toggle("grab", grab_mode);
}

function key_event(ev) {
  const target = ev.target;

  // Don't handle keys if target or its parents are form elements, canvas, svg, or have class 'keys'
  if (target.closest('input, button, textarea, select, canvas, svg, .keys')) {
    return;
  }

  // console.log("key_event", ev);
  if (overlay_mode) {
    return key_event_overlay(ev);
  }
  if (!simple && ev.altKey && ev.key == "g") {
    ev.preventDefault();
    toggle_grab();
    return;
  }
  if (grab_mode) {
    return;
  }
  if (ev.altKey && ev.key == "f") {
    ev.preventDefault();
    toggle_fullscreen(ev.target);
    return;
  }
  if (ev.key == "Home") {
    ev.preventDefault();
    return scroll_home_end(0);
  }
  if (ev.key == "End") {
    ev.preventDefault();
    return scroll_home_end(1);
  }
  if (ev.key == "PageUp") {
    ev.preventDefault();
    return scroll_pages(-1);
  }
  if (ev.key == "PageDown") {
    ev.preventDefault();
    return scroll_pages(1);
  }
  if (
    keysToKeep.includes(ev.key) ||
    (ev.ctrlKey && ctrlKeysToKeep.includes(ev.key))
  ) {
    return;
  }
  if (!inIframe) {
    return;
  }

  // relay the event to the parent window
  const copy = {
    type: ev.type,
    key: ev.key,
    code: ev.code,
    keyCode: ev.keyCode,
    ctrlKey: ev.ctrlKey,
    altKey: ev.altKey,
    shiftKey: ev.shiftKey,
    metaKey: ev.metaKey,
  };
  if (inIframe)
    window.parent.postMessage(copy, ALLYCHAT_CHAT_URL);
  ev.preventDefault();
}

/*
function go_home() {
  // tell the parent window to GTFO of here
  if (inIframe)
    window.parent.postMessage({ type: "go_home" }, ALLYCHAT_CHAT_URL);
}
*/

function key_event_overlay(ev) {
  // ignore if any modifier is pressed
  if (ev.altKey || ev.ctrlKey || ev.metaKey || ev.shiftKey)
    return;
  if (ev.key == "Escape" || ev.key == "q" || ev.key == "Enter") {
    overlay_close(ev);
  } else if (ev.key == "f") {
    toggle_fullscreen();
  } else if (ev.key == "m") {
    cycle_zoom();
  // look for key in "lrhv"
  } else if ("lrhv".includes(ev.key)) {
    transform_overlay(ev.key);
  } else if (ev.key == "ArrowLeft" || ev.key == "Backspace") {
    image_go(-1);
  } else if (ev.key == "ArrowRight" || ev.key == " ") {
    image_go(1);
  } else if (ev.key == "PageUp") {
    image_go(-10);
  } else if (ev.key == "PageDown") {
    image_go(10);
  } else if (ev.key == "Home") {
    image_go_first();
  } else if (ev.key == "End") {
    image_go_last();
  } else {
    return;
  }
  ev.preventDefault();
}

let matrix = null;

function transform_overlay(key) {
  // use CSS transforms to rotate or flip the image
  const $img = $overlay.querySelector("img");
  if (!$img)
    return;
  if (!$img.style.transform || !matrix)
    matrix = [1, 0, 0, 1, 0, 0];
  if (key == "v") {
    // flip y
    matrix[1] *= -1;
    matrix[3] *= -1;
  } else if (key == "h") {
    // flip x
    matrix[0] *= -1;
    matrix[2] *= -1;
  } else if (key == "r") {
    // rotate 90 degrees clockwise
    matrix = [matrix[2], matrix[3], -matrix[0], -matrix[1], 0, 0];
  } else if (key == "l") {
    // rotate 90 degrees counter-clockwise
    matrix = [-matrix[2], -matrix[3], matrix[0], matrix[1], 0, 0];
  }
  const matrix_str = matrix.join(",");
  if (matrix_str == "1,0,0,1,0,0")
    $img.style.transform = "";
  else
    $img.style.transform = `matrix(${matrix.join(",")})`;
}

function setup_keyboard_shortcuts() {
  $on(document, "keypress", key_event);
  $on(document, "keydown", key_event);
}

// embeds --------------------------------------------------------------------

// when we click an image of class thumb, we convert it to an embed

function embed_click(ev, $thumb) {
  const $embed = $thumb.parentNode;
  const href = $embed.querySelector("a").href;
  // if middle click or ctrl-click, open in new tab
  // if shift-click, open in new window
  // if alt-click, open in parent window
  if (ev.button == 1 || ev.ctrlKey) {
    window.open(href, "_blank");
    return;
  } else if (ev.shiftKey) {
    window.open(href, "_blank").focus();
    return;
  } else if (ev.altKey) {
    window.top.location.href = href;
    return;
  }

  // otherwise, replace the thumb with the embed

  let iframe_html;
  if ($embed.dataset.site == "youtube") {
    iframe_html = `<iframe width="280" height="157" src="https://www.youtube.com/embed/${$embed.dataset.videoid}?autoplay=1" title="${$thumb.alt}" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share; fullscreen" referrerpolicy="strict-origin-when-cross-origin" allowfullscreen></iframe>`;
  } else if ($embed.dataset.site == "pornhub") {
    iframe_html = `<iframe src="https://www.pornhub.com/embed/${$embed.dataset.videoid}" frameborder="0" width="280" height="157" scrolling="no" allowfullscreen></iframe>`;
  } else {
    throw new Error("unknown embed site");
  }

  // replace $thumb element with iframe_html
  if (iframe_html == undefined) {
    return;
  }
  const $node = document.createElement("div");
  $node.innerHTML = iframe_html;
  $embed.replaceChild($node.firstChild, $thumb);
  $node.remove();
}

// fullscreen ----------------------------------------------------------------

let fullscreen_exit_requested = false;

function toggle_fullscreen(target) {
  if (is_fullscreen()) {
    fullscreen_exit_requested = true;
    exit_fullscreen();
    signal_overlay(false);
    overlay_fullscreen = false;
  } else {
    go_fullscreen(target);
    signal_overlay(true);
    overlay_fullscreen = true;
  }
}

function fullscreenchange(ev) {
  if (!is_fullscreen() && !fullscreen_exit_requested)
    overlay_close();
  fullscreen_exit_requested = false;
}

// image zoom ----------------------------------------------------------------

function cycle_zoom() {
  // fit -> cover -> maxpect
  if ($overlay.classList.contains("maxpect")) {
    $overlay.classList.remove("maxpect");
    $overlay.classList.add("cover");
    setup_overlay_image_cover();
  } else if ($overlay.classList.contains("cover")) {
    clear_overlay_image_cover();
    $overlay.classList.remove("cover");
  } else {
    $overlay.classList.add("maxpect");
  }
}

function setup_overlay_image_cover() {
  if (!$currentImg) {
    return;
  }
  if (!$overlay.classList.contains("cover")) {
    return;
  }
  const container = $overlay.getBoundingClientRect();
  const image_aspect = $currentImg.naturalWidth / $currentImg.naturalHeight;
  const container_aspect = container.width / container.height;
  if (image_aspect > container_aspect) {
    $overlay.classList.add("fit_height");
    $overlay.classList.remove("fit_width");
  } else {
    $overlay.classList.add("fit_width");
    $overlay.classList.remove("fit_height");
  }
}

function clear_overlay_image_cover() {
  if (!$currentImg) {
    return;
  }
  $overlay.classList.remove("fit_width");
  $overlay.classList.remove("fit_height");
}

// image overlay -------------------------------------------------------------

function image_overlay($el) {
  show($id("overlay_help"), view_options.advanced == 0);

  // console.log("image_overlay", $el);
  // check if it's an A
  let $img;
  if ($el.tagName === "A") {
    $currentImg = $el.querySelector("img");
  } else {
    $currentImg = $el;
  }

  // Get all images and links containing images in document order
  allImages = Array.from($messages.querySelectorAll('img:not(.hidden):not(.nobrowse)')).filter(img => !img.closest('.hidden'));
  if ($currentImg.matches(".nobrowse")) {
    const src_path = new URL($currentImg.src, ALLYCHAT_ROOMS_URL).pathname;
    $currentImg = $("img:not(.nobrowse):not(.hidden)[src='" + src_path + "']");
    if (!$currentImg) {
      console.warn("Pair image not found in messages", src_path);
      return;
    }
  }

  currentImgIndex = allImages.indexOf($currentImg);
  if (currentImgIndex === -1) {
    console.warn("Image not found in allImages", $currentImg);
    return
  }

  $overlay.innerHTML = "";
  $img = $create("img");
  $overlay.appendChild($img);
  $body.classList.add("overlay");
  overlay_mode = true;
  signal_overlay(true);

//  console.log("currentImgIndex", currentImgIndex);
  allImages = allImages.map(element => {
      // If this is an image in a link
      if (element.parentElement.tagName === "A") {
        const clonedImg = element.cloneNode();
        const thumbSrc = element.src;
        clonedImg.removeAttribute("width");
        clonedImg.removeAttribute("height");
        clonedImg.src = element.parentElement.href;

        const preloadImg = new Image();
        preloadImg.onerror = function() {
            console.warn("Preloading large image failed.");
            clonedImg.src = thumbSrc; // Revert back to thumbnail
        };
        preloadImg.src = clonedImg.src;
        return clonedImg;
      }
      // For regular images, return as is
      return element;
    });

  image_go_to(currentImgIndex);

  // focus the overlay, for keyboard scrolling
  $overlay.focus();

  if (overlay_fullscreen)
    go_fullscreen();

  add_hook("window_resize", setup_overlay_image_cover);
  setup_overlay_image_cover();

  // handle back button to close overlay
  history.pushState({}, "");
  $on(window, "popstate", image_overlay_back);
}

function image_overlay_back(ev) {
  overlay_close(null, true);
}

function hide_overlay_help(ev) {
  ev.preventDefault();
  hide($id("overlay_help"));
}

function overlay_close(ev, back_pressed) {
  if (ev)
    ev.preventDefault();

  if (!overlay_mode)
    return;

  remove_hook("resize", setup_overlay_image_cover);

  overlay_mode = false;
  $body.classList.remove("overlay");

  // Reset current image index
  allImages = null;
  $currentImg = null;
  currentImgIndex = null;

  // clean up the "back button to close overlay" state
  $off(window, "popstate", image_overlay_back);
  if (!back_pressed)
    history.back();

  signal_overlay(false);

  // for blur: allow remove body.overlay to apply before removing the overlay
  // setTimeout(overlay_close_2, 0);
  // }

  // function overlay_close_2() {

  clear_overlay_image_cover();
  $overlay.innerHTML = "";
  exit_fullscreen();
}

function signal_overlay(overlay) {
  if (inIframe)
    window.parent.postMessage({ type: "overlay", overlay: overlay }, ALLYCHAT_CHAT_URL);
}

function is_hidden($el) {
  return window.getComputedStyle($el).display === 'none';
}

function image_go(delta) {
  const i0 = currentImgIndex;
  do {
    image_go_to(currentImgIndex + delta);
  } while (currentImgIndex != i0 && is_hidden($currentImg));
}

function image_go_first() {
  image_go_to(0);
  if (is_hidden($currentImg))
    image_go(1);
}

function image_go_last() {
  image_go_to(-1);
  if (is_hidden($currentImg))
    image_go(-1);
}

function image_go_to(index) {
  currentImgIndex = index;
  while (currentImgIndex < 0) {
    currentImgIndex += allImages.length;
  }
  if (currentImgIndex >= allImages.length) {
    currentImgIndex = currentImgIndex % allImages.length;
  }
  $currentImg = allImages[currentImgIndex];
  const $img = $overlay.querySelector("img");
  $img.src = $currentImg.src;
  $img.alt = $currentImg.alt;
  $img.title = $currentImg.title;
}

function get_current_img() {
  while (currentImgIndex < 0) {
    currentImgIndex += allImages.length;
  }
  if (currentImgIndex >= allImages.length) {
    currentImgIndex = currentImgIndex % allImages.length;
  }
  $currentImg = allImages[currentImgIndex];
  return $currentImg.src;
}

function overlay_click(ev) {
  let src
  src = get_current_img();
  if (lastSwipeDistance > maxClickDistance) {
    lastSwipeDistance = 0;
    return;
  }
  if (ev.shiftKey) {
    window.open(src, "_blank");
    return
  } else if (ev.ctrlKey || ev.metaKey || ev.button === 1) {
    window.open(src, "_blank").focus();
    return
  } else if (ev.altKey) {
    const a = document.createElement("a");
    a.href = src;
    a.download = src.split("/").pop(); // Use the file name from the URL
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    return
  }
  // detect left 25% and right 25% to go prev and next
  // and top 25% and bottom 25% to toggle fullscreen and cycle zoom
  const container = $overlay.getBoundingClientRect();
  if (simple) {
    // no fancy clicking in simple mode, just close it
    overlay_close();
    return;
  }
  const x = ev.clientX - container.left;
  const y = ev.clientY - container.top;
  if (x < container.width / 3) {
    image_go(-1);
  } else if (x > container.width * 2 / 3) {
    image_go(1);
  } else if (y < container.height / 3) {
    toggle_fullscreen();
  } else if (y > container.height * 2 / 3) {
    cycle_zoom();
  } else {
    overlay_close(ev);
  }
}

// Swipe gesture handling ----------------------------------------------------

let touchStartX = null;
let touchEndX = null;
let touchStartY = null;
let touchEndY = null;
let lastSwipeDistance = 0;
let maxClickDistance = 10;

// Minimum distance for a swipe (in pixels)
const minSwipeDistance = 50;

function handleSwipe() {
  lastSwipeDistance = Math.hypot(touchEndX - touchStartX, touchEndY - touchStartY);
	const swipeDistanceX = touchEndX - touchStartX;
  const swipeDistanceY = touchEndY - touchStartY;

	// Check if the swipe distance is significant enough
  if (Math.abs(swipeDistanceX) > Math.abs(swipeDistanceY)) {
  	if (Math.abs(swipeDistanceX) >= minSwipeDistance) {
  		if (swipeDistanceX > 0) {
  			// Right swipe
  			image_go(-1);
  		} else {
  			// Left swipe
  			image_go(1);
  		}
  	}
  } else {
    if (Math.abs(swipeDistanceY) >= minSwipeDistance && !simple) {
      if (swipeDistanceY > 0) {
        // Down swipe
        cycle_zoom();
      } else {
        // Up swipe
        toggle_fullscreen();
      }
    }
  }

  const $img_clone = $overlay.querySelector("img");
  $img_clone.style.transform = "";
}

function overlay_touch_start(e) {
  // swipe with mouse is diabled, it was trouble
  // For mouse events, only process left clicks (button 0)
  // if (!e.touches && e.button !== 0) {
  //   return;
  // }

  if (e.touches && e.touches.length == 1) {
    touchStartX = touchStartY = null;
    return;
  }

  if (e.touches) {
    touchStartX = e.touches[0].clientX;
    touchStartY = e.touches[0].clientY;
  }
  /*
  else {
    touchStartX = e.clientX;
    touchStartY = e.clientY;
  }
  */
}

function overlay_touch_end(e) {
  if (touchStartX === null) {
    touchStartX = touchStartY = null;
    return;
  }
  e.preventDefault();
  if (e.changedTouches) {
    touchEndX = e.changedTouches[0].clientX;
    touchEndY = e.changedTouches[0].clientY;
  } else {
    touchEndX = e.clientX;
    touchEndY = e.clientY;
  }
  handleSwipe();
  touchStartX = touchStartY = null;
  touchEndX = touchEndY = null;
}

function overlay_touch_move(e) {
  if (touchStartX === null) {
    touchStartX = touchStartY = null;
    return;
  }
  e.preventDefault();
  if (touchStartX === null) {
    return;
  }
	let currentX, currentY;
  if (e.touches) {
    currentX = e.touches[0].clientX;
    currentY = e.touches[0].clientY;
  } else {
    currentX = e.clientX;
    currentY = e.clientY;
  }
	const differenceX = currentX - touchStartX;
  const differenceY = currentY - touchStartY;

  // offset the image by the swipe distance
  const $img_clone = $overlay.querySelector("img");
  $img_clone.style.transform = `translate(${differenceX}px, ${differenceY}px)`;
}

function setup_swipe() {
  // Add touch event listeners
  $overlay.addEventListener('touchstart', overlay_touch_start, { passive: true });
  $overlay.addEventListener('touchmove', overlay_touch_move, { passive: false });
  $overlay.addEventListener('touchend', overlay_touch_end);
  // For desktop dragging also; disabled
  // $overlay.addEventListener('mousedown', overlay_touch_start);
  // $overlay.addEventListener('mousemove', overlay_touch_move);
  // $overlay.addEventListener('mouseup', overlay_touch_end);
  // $overlay.addEventListener('mouseleave', overlay_touch_end);
}

// ---------------------------------------------------------------------------

function image_click($el, ev) {
  let src
  if ($el.tagName === "IMG" && $el.parentNode.tagName === "A") {
    src = $el.parentNode.href;
  } else if ($el.tagName === "IMG") {
    src = $el.src;
  } else if ($el.tagName === "A") {
    src = $el.href;
  } else {
    return;
  }
  if (ev.shiftKey) {
    window.open(src, "_blank");
  } else if (ev.altKey) {
    const a = document.createElement("a");
    a.href = src;
    a.download = src.split("/").pop(); // Use the file name from the URL
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
  } else if (ev.ctrlKey || ev.metaKey || ev.button === 1) {
    window.open(src, "_blank").focus();
  } else if (view_options["embed"]) {
    // don't do anything for normal click / tap in embed mode, it can be confusing for new users
  } else if (!overlay_mode) {
    image_overlay($el);
  }
}

async function click(ev) {
  if (!$messages.contains(ev.target))
    return;

  // focus on message if clicked, can show IDs
  // TODO, only in "select mode", keyboard control / accessibility...
  /*
  const $message = ev.target.closest(".message");
  if ($message) {
    ev.preventDefault();
    select_message($message, ev.shiftKey, ev.ctrlKey);
  }
  */

  // copy username from label?
  if (ev.target.matches(".message .label")) {
    ev.preventDefault();
    ev.stopPropagation();
    // TODO factor with similar code in process_messages.js
    const username = ev.target.closest(".message").getAttribute("user");
    const text = username + ",";
    if (inIframe) {
      // send text to parent window
      window.parent.postMessage({ type: "copy", text: text }, ALLYCHAT_CHAT_URL);
    } else {
      // copy text to clipboard
      await navigator.clipboard.writeText(text);
    }
  }

  if (ev.target.classList.contains("thumb") && ev.target.parentNode.classList.contains("embed")) {
    ev.preventDefault();
    ev.stopPropagation();
    return embed_click(ev, ev.target);
  }
  // check for img tag, and view or browse to the src
  if (ev.target.tagName === "IMG" && !ev.target.closest('a[href]')) {
    //  || ev.shiftKey || ev.ctrlKey || ev.metaKey || ev.altKey || ev.button == 1)) {
    ev.preventDefault();
    ev.stopPropagation();
    return image_click(ev.target, ev);
  }
  // check for A tag containing an image
  if (ev.target.tagName === "A" && ev.target.querySelector("img")) {
    ev.preventDefault();
    ev.stopPropagation();
    return image_click(ev.target, ev);
  }
}

let $select_message_prev;

function select_message($message, shift, ctrl) {
  // if ctrl not held, clear previous selections
  if (!ctrl) {
    for (const $m of $$(".message.select")) {
      $m.classList.remove("select");
    }
  }
  // range select
  if (shift && $message !== $select_message_prev) {
    // put them in order, also exclude the previous message
    let $from = $select_message_prev;
    let $to = $message;
    if (isPrecedingNode($from, $to)) {
      if (ctrl) {
        $from = $from.nextElementSibling;
      }
    } else {
      [$from, $to] = [$to, $from];
      if (ctrl) {
        $to = $to.previousElementSibling;
      }
    }
    let $m = $from;
    while ($m) {
      $m.classList.toggle("select");
      if ($m === $to)
        break;
      $m = $m.nextElementSibling;
    }
  } else {
    // toggle .select class
    $message.classList.toggle("select");
  }
  $select_message_prev = $message;
}

export function notify_new_message(newMessage) {
  // send a message to the parent window
  if (inIframe)
    window.parent.postMessage({ type: "new_message", message: newMessage }, ALLYCHAT_CHAT_URL);
}

// view options --------------------------------------------------------------

function setup_view_options() {
  // persist from local storage JSON
  // if not present, set to default
  let view_options_str = localStorage.getItem("view_options");
  if (view_options_str) {
    const view_options_loaded = JSON.parse(view_options_str);
    for (const key in view_options_loaded) {
      view_options[key] = view_options_loaded[key];
    }
  }
  view_options.details_changed = true;
  set_view_options(view_options);
}

async function theme_loaded() {
  await wait_for_load();
  const theme_mode = getComputedStyle(document.documentElement).getPropertyValue("--theme-mode");
  // console.log("theme_mode", theme_mode);
  if (theme_mode == "dark") {
    $body.classList.add("dark");
    $body.classList.remove("light");
  } else {
    $body.classList.add("light");
    $body.classList.remove("dark");
  }
  await highlight_set_stylesheet_for_theme();
}

async function highlight_set_stylesheet_for_theme() {
  if (!view_options.highlight)
    return;
  const theme_mode = getComputedStyle(document.documentElement).getPropertyValue("--theme-mode");
  // console.log("theme_mode", theme_mode);
  let highlight_theme;
  if (theme_mode == "dark") {
    highlight_theme = view_options.highlight_theme_dark;
  } else {
    highlight_theme = view_options.highlight_theme_light;
  }
  if (typeof highlight_set_stylesheet === "function")
    highlight_set_stylesheet(highlight_theme);
}

function set_theme(theme) {
  // console.log("theme changed", theme);
  const $old_link = $id("theme");
  const $new_link = $old_link.cloneNode();
  $new_link.href = ALLYCHAT_CHAT_URL + "/themes/" + theme + ".css";
  $new_link.id = "theme";
  $on($new_link, "load", theme_loaded);
  $old_link.replaceWith($new_link);
}

async function handle_message(ev) {
  // console.log("room handle_message", ev);
  if (ev.origin !== ALLYCHAT_CHAT_URL) {
    console.error("ignoring message from", ev.origin);
    return;
  }
  if (ev.data.type === "set_view_options") {
    delete ev.data.type;
    await set_view_options(ev.data);
  } else if (ev.data.type === "set_mode_options") {
    delete ev.data.type;
    await set_mode_options(ev.data);
  } else if (ev.data.type === "theme_changed") {
    set_theme(ev.data.theme);
  } else if (ev.data.type === "scroll_home_end") {
    scroll_home_end(ev.data.p);
  } else if (ev.data.type === "scroll_pages") {
    scroll_pages(ev.data.d);
  }
  messages_resized();
}

async function set_view_options(new_view_options) {
//  console.log("set_view_options", new_view_options);
  const old_view_options = view_options;
  view_options = new_view_options;
  localStorage.setItem("view_options", JSON.stringify(view_options));
  await wait_for_load();
//  console.log("applying view options");
  const cl = document.body.classList;
  if (file_type === "room") {
    cl.toggle("images", view_options.images > 0);
    cl.toggle("blur", view_options.images == 2);
    cl.toggle("alt", view_options.alt == 1);
    cl.toggle("code_source", view_options.source >= 1);
    cl.toggle("script_source", view_options.source >= 2);
    cl.toggle("rendered_source", view_options.source >= 3);
    cl.toggle("canvas", view_options.canvas >= 1);
    cl.toggle("messages", view_options.canvas <= 1);
    cl.toggle("clean", view_options.clean == 1);
    cl.toggle("columns", view_options.columns == 1);
    cl.toggle("history", view_options.history == 1);
    cl.toggle("ids-hover", view_options.ids == 1);
    cl.toggle("ids", view_options.ids == 2);
  }

  simple = view_options.advanced < 0;
  cl.toggle("simple", simple);
  cl.toggle("compact", view_options.compact >= 1);
  cl.toggle("compact2", view_options.compact == 2);

  const image_size = view_options.image_size * 10;
  const image_size_small = view_options.image_size*5;
  // const image_size_large = view_options.image_size == 10 ? 100 : Math.min(view_options.image_size*10, 90);
  document.documentElement.style.setProperty("--image-width", image_size + "vw");
  document.documentElement.style.setProperty("--image-height", image_size + "vh");
  document.documentElement.style.setProperty("--image-width-small", image_size_small + "vw");
  document.documentElement.style.setProperty("--image-height-small", image_size_small + "vh");
  // document.documentElement.style.setProperty("--image-width-large", image_size_large + "vw");
  // document.documentElement.style.setProperty("--image-height-large", image_size_large + "vh");

  const zoom = 1.15**(view_options.font_size-4);
  const font_size = Math.round(16*zoom);
  document.documentElement.style.setProperty("--font-size", font_size + "px");
  const font_size_code = 12 * Math.round(zoom);
  document.documentElement.style.setProperty("--font-size-code", font_size_code + "px");

  if (view_options.details_changed) {
    set_view_details();
    view_options.details_changed = false;
  }

  if (old_view_options.items >= 0 && old_view_options.items < 10) {
    $body.classList.remove("items_" + Math.round(old_view_options.items));
  }
  if (view_options.items !== "" && view_options.items >= 0 && view_options.items < 10) {
    $body.classList.add("items_" + Math.round(view_options.items));
//  document.documentElement.style.setProperty("--visible-items", view_options.items);
  }

  if (view_options.highlight != old_view_options.highlight) {
    await highlight_set_stylesheet_for_theme();
    await highlight_code($messages, view_options);
  }

  if (file_type === "dir") {
    set_dir_sort(view_options.dir_sort);
  }

  if (filter !== view_options.filter) {
    filter = view_options.filter ?? "";
    update_image_filter(filter);
  }
}

async function set_mode_options(new_mode_options) {
  const old_mode_options = mode_options;
  mode_options = new_mode_options;
  await wait_for_load();
  const cl = document.body.classList;
  cl.toggle("select", mode_options.select);
}

function set_view_details() {
  if (!$messages)
    return;
  for (const $details of $messages.querySelectorAll("details"))
    open_or_close_details($details);
}

export function open_or_close_details($details) {
  const view_details = view_options.details;
  const show_thinking = view_details & 1;
  const show_other_details = view_details & 2;
  if ($details.classList.contains("think")) {
    $details.open = show_thinking;
  } else {
    $details.open = show_other_details;
  }
}

function set_dir_sort(dir_sort) {
  const $dir = $("ul.directory-listing");
  const items = [...$dir.children];

  if (dir_sort === "alpha") {
    for (const $item of items) {
      const $a = $item.querySelector("a");
      $item.style.removeProperty('order');
      $a.removeAttribute('tabindex');
    }
  } else {
    const sorted = items.sort((a, b) => a.dataset.typeSort - b.dataset.typeSort || b.dataset.mtime - a.dataset.mtime);
    let i = 1;
    for (const $item of sorted) {
      const $a = $item.querySelector("a");
      $item.style.order = i;
      $a.tabIndex = i;
      i++;
    }
  }
}

// scroll to home or end, page up, page down ---------------------------------

function scroll_home_end(p) {
  if (p == 2)
    p = messages_at_bottom ? 0 : 1;
  if (view_options.columns) {
    $messages_wrap.scrollLeft = p * $messages_wrap.scrollWidth;
  } else {
    $messages_wrap.scrollTop = p * $messages_wrap.scrollHeight;
  }
}

function scroll_pages(d) {
  if (view_options.columns) {
    $messages_wrap.scrollLeft += d * $messages_wrap.clientWidth;
  } else {
    $messages_wrap.scrollTop += d * $messages_wrap.clientHeight;
  }
}

// wait for the page to load the main elements -------------------------------

function setup_ids() {
    $body = $("body");
    $messages = $("div.messages");
    $messages_wrap = $("div.messages_wrap");
    $overlay = $("div.overlay");
    $canvas_div = $("div.canvas");
}

function wait_for_load() {
  return new Promise(resolve => {
    function check_ready() {
//      console.log("check_ready");
//      console.log($("div.messages"), $("div.canvas canvas"));
      if ($("div.messages") && $("div.canvas canvas") || $("ul.directory-listing")) {
        observer.disconnect();
        setup_ids();
        resolve();
        return true;
      }
      return false;
    }
    const observer = new MutationObserver(check_ready);

    if (check_ready())
      return;

    observer.observe(document.documentElement, { childList: true, subtree: true });
  });
}

// wait for the document to be fully loaded: for folder view -----------------

async function wait_for_document_load(fail_ok = false) {
  if (document.readyState === 'complete') {
    return;
  }

  return new Promise((resolve, reject) => {
    document.addEventListener('readystatechange', () => {
      if (document.readyState === 'complete') {
        resolve();
      }
    });

    window.addEventListener('error', () => {
      if (fail_ok) {
        resolve();
      } else {
        reject(new Error('Page failed to load'));
      }
    });
  });
}

// resize handler ------------------------------------------------------------

let canvas_at_bottom = true;
let orientation;

async function window_resized() {
  // check width vs height for orientation
  orientation = window.innerWidth > window.innerHeight ? "landscape" : "portrait";
  // add orientation class to body
  $body.classList.remove("landscape", "portrait");
  $body.classList.add(orientation);
  // console.log("orientation", orientation);
}

function messages_resized() {
//  console.log("messages resized");
  if (!messages_at_bottom && top_message) {
    // top_message.scrollIntoView({ behavior: 'instant', block: 'start' });
  }
  /*
  if (inIframe)
    window.parent.postMessage({ type: "size_change", width: $messages_wrap.scrollWidth, height: $messages_wrap.scrollHeight }, ALLYCHAT_CHAT_URL);
  */
  messages_scrolled();
}

/*
function canvas_resized() {
  if (canvas_at_bottom) {
    scroll_to_bottom($canvas_div);
  }
}

function canvas_scrolled() {
  canvas_at_bottom = is_at_bottom($canvas_div);
}
*/

// Wrapper function to initialize drag controls for the resizer --------------

function dragResizer(ev) {
  const resizer = new DragResizer({
    element: $canvas_div,
    direction: orientation == "landscape" ? "left" : "down",
//    overlay: $messages_overlay,
  });

  resizer.initDrag(ev);
}

// flash ---------------------------------------------------------------------

// TODO this is common, move to utils

export async function flash($el, className) {
  $el.classList.add(className);
  await $wait(300);
  $el.classList.remove(className);
}

/*
async function error(id) {
  await flash($id(id), "error");
}
*/

function handle_room_intro() {
  // let hasSeenIntro = !['guide', 'intro'].includes(room) && localStorage.getItem(`seen_intro_${room}`);
  let hasSeenIntro = false;  // giving up on auto scroll-down for the moment!
  if (!hasSeenIntro) {
    suppressInitialScroll = true;
    setTimeout(() => {
      localStorage.setItem(`seen_intro_${room}`, true);
      suppressInitialScroll = false;
    }, 10000);
  }
}

// selection and hidden checkboxes -------------------------------------------

function setup_select() {
  // listen on div.messages for clicks
  $on($messages, "click", messages_click);
}

function messages_click(ev) {
  // if not select mode, return for default
}

// filter images -------------------------------------------------------------


function filter_make_word_selector(term, isNegative) {
	term = term.replace(/_/g, ' ');
//	const isSubstring = term.startsWith('*') && term.endsWith('*');
//	const cleanTerm = isSubstring ? term.slice(1, -1) : term;
//	const op = isSubstring ? '*=' : '~=';
//	const selector = `[alt${op}"${cleanTerm}"]`;
	const selector = `[alt*="${term}"]`;

	return isNegative ? `:not(${selector})` : selector;
}

function filter_process_term_set(termSet) {
	const words = termSet.trim().split(/\s+/).filter(w => w);
	let baseSelector = 'img';
	let positiveSelectors = '';

	for (const word of words) {
		if (word.startsWith('-'))
			baseSelector += filter_make_word_selector(word.slice(1), true);
		else
			positiveSelectors += filter_make_word_selector(word, false);
	}

	// If there are no positive terms, the selector matches everything not excluded.
	// If there are positive terms, they must all be present.
	return positiveSelectors ? baseSelector + positiveSelectors : baseSelector;
}

function filter_string_to_CSS(filterString) {
	const filterGroups = filterString.split(/;\s+/);

	const groupSelectors = [];
	for (const group of filterGroups) {
		if (!group.trim())
			continue;
		const isNegated = group.startsWith('!');
		const cleanGroup = isNegated ? group.slice(1) : group;
		const termSets = cleanGroup.split(/\s*,\s*/);
		const termSelectors = [];
		for (const termSet of termSets)
			termSelectors.push(filter_process_term_set(termSet));
		const groupSelector = termSelectors.join(', ');
		groupSelectors.push(isNegated ? `:not(${groupSelector})` : groupSelector);
	}

	// Combine groups using :is()
	const finalSelectorParts = groupSelectors.map(group => {
		// const innerSelector = group.split(',').map(s => s.trim().substring(3)).join(',');
		return `:is(${group})`;
	});

	const finalSelector = finalSelectorParts.join('');

  if (finalSelector === "")
    return "";

	return `
:is(img,video):not(${finalSelector}) { display: none !important; }
div.image:has(img:not(${finalSelector})) { display: none !important; }
.message:not(:has(:is(img,video)${finalSelector}, .content > p > :not(.label, .image), .content > :not(.label, p, video))) { display: none !important; }
`;
}

function update_image_filter(filterString) {
	const existingStyle = document.getElementById('image-filter');

	const CSSRules = filter_string_to_CSS(filterString.toLowerCase());

	// console.log(CSSRules);

	const style = document.createElement('style');
	style.id = 'image-filter';
	style.textContent = CSSRules;

	document.head.appendChild(style);

	// remove old filter after adding new, to avoid flashes of unwanted content
	if (existingStyle)
		existingStyle.remove();
}

// timestamp -----------------------------------------------------------------

function getRelativeTimeString(diff) {
  // Convert seconds to different units
  const seconds = Math.floor(diff);
  const minutes = Math.floor(seconds / 60);
  const hours = Math.floor(minutes / 60);
  const days = Math.floor(hours / 24);

  if (days > 0) {
    return `${days}d`;
  } else if (hours > 0) {
    return `${hours}h`;
  } else if (minutes > 0) {
    return `${minutes}m`;
  } else if (seconds > 0) {
    return `${seconds}s`;
  } else {
    return `0s`;
  }
}

function formatLocalDateTime(date) {
  return date.getFullYear() + '-' +
    String(date.getMonth() + 1).padStart(2, '0') + '-' +
    String(date.getDate()).padStart(2, '0') + ' ' +
    String(date.getHours()).padStart(2, '0') + ':' +
    String(date.getMinutes()).padStart(2, '0') + ':' +
    String(date.getSeconds()).padStart(2, '0');
}

async function get_date_and_mtime() {
  try {
    const response = await fetch(window.location.pathname, {method: 'HEAD'});
    const lastMod = response.headers.get('last-modified');
    const serverDate = response.headers.get('date');
    if (serverDate && lastMod)
      return [new Date(serverDate), new Date(lastMod)];
  } catch (err) {
    console.error('Error fetching timestamp:', err);
  }
  return [null, null];
}

export async function show_timestamp(date, mtime) {
  const diff = (date - mtime) / 1000;
  let relativeTime = getRelativeTimeString(diff) + ' ago';
  if (relativeTime == "0s ago")
    relativeTime = "now";
  const fullTimestamp = formatLocalDateTime(mtime);

  await wait_for(() => $id('timestamp'), 5000);

  const timestampElement = $id('timestamp');
  timestampElement.textContent = relativeTime;
  timestampElement.title = fullTimestamp;
  // if (timestampElement.parentNode == $body)
  //   $messages.prepend(timestampElement);
  show('timestamp');
}

function hide_timestamp() {
  hide('timestamp');
}

// sticky notes --------------------------------------------------------------

let dragSticky = null;
let initialX = 0;
let initialY = 0;
let currentX = 0;
let currentY = 0;

// Helper to get coordinates from either mouse or touch event
function getEventCoordinates(e) {
  if (e.touches && e.touches.length > 0) {
    return {
      clientX: e.touches[0].clientX,
      clientY: e.touches[0].clientY
    };
  }
  return {
    clientX: e.clientX,
    clientY: e.clientY
  };
}

// Get current transform values
function getTransformValues(element) {
  const transform = window.getComputedStyle(element).transform;
  if (transform === 'none') {
    return { x: 0, y: 0 };
  }
  const matrix = transform.match(/matrix\((.+)\)/)[1].split(', ');
  return {
    x: parseFloat(matrix[4]),
    y: parseFloat(matrix[5])
  };
}

function mouse_down(e) {
  if (e.target.tagName === 'STICKY') {
    const coords = getEventCoordinates(e);
    dragSticky = e.target;
    dragSticky.classList.add('moving');

    // Get current transform position
    const currentTransform = getTransformValues(dragSticky);
    currentX = currentTransform.x;
    currentY = currentTransform.y;

    // Calculate initial mouse/touch position relative to the element's current position
    initialX = coords.clientX - currentX;
    initialY = coords.clientY - currentY;

    // Set will-change for optimization hint
    dragSticky.style.willChange = 'transform';
  }
}

function mouse_move(e) {
  if (dragSticky) {
    const coords = getEventCoordinates(e);

    // Calculate new position
    currentX = coords.clientX - initialX;
    currentY = coords.clientY - initialY;

    // Use transform for better performance
    dragSticky.style.transform = `translate(${currentX}px, ${currentY}px)`;
  }
}

function mouse_up() {
  if (dragSticky) {
    // Check if element is at origin
    if (currentX === 0 && currentY === 0) {
      dragSticky.classList.remove('moving');
      dragSticky.style.removeProperty('transform');
    }

    // Clean up will-change
    dragSticky.style.willChange = 'auto';

    dragSticky = null;
  }
}

function mouse_double_click(e) {
  // move back to original position
  if (e.target.tagName === 'STICKY') {
    e.target.style.removeProperty('transform');
    e.target.classList.remove('moving');
    e.target.style.willChange = 'auto';
    currentX = 0;
    currentY = 0;
  }
}

// Touch event handlers with proper cancel handling
function touch_start(e) {
  if (e.target.tagName === 'STICKY' && e.touches.length === 1) {
    mouse_down(e);
  }
}

function touch_move(e) {
  if (dragSticky && e.touches.length === 1) {
    e.preventDefault(); // Prevent scrolling while dragging
    mouse_move(e);
  }
}

function touch_end(e) {
  mouse_up();
}

// Handle touch cancel (e.g., when call comes in or gesture is interrupted)
function touch_cancel(e) {
  if (dragSticky) {
    // Optionally snap back to original position on cancel
    dragSticky.style.transform = 'translate(0px, 0px)';
    dragSticky.classList.remove('moving');
    dragSticky.style.willChange = 'auto';
    currentX = 0;
    currentY = 0;
    dragSticky = null;
  }
}

// intersection observer for lazy loading images ----------------------------

let lazy_images_observer;

async function setup_lazy_images_observer() {
  await wait_for_load();
  lazy_images_observer = new IntersectionObserver((images) => {
    images.forEach(entry => {
      if (entry.isIntersecting && entry.target.dataset.src) {
        const img = entry.target;
        img.src = img.dataset.src;
        img.removeAttribute('data-src');
        // img.removeAttribute('loading');
        lazy_images_observer.unobserve(img);
      }
    });
  }, {
    root: $messages_wrap,
    rootMargin: '1000px',
  });
}

export async function lazy_image(img) {
  if (!lazy_images_observer)
    await setup_lazy_images_observer();
  lazy_images_observer.observe(img);
}

// agent colours -------------------------------------------------------------

async function load_agent_colours() {
  const response = await fetch(`${ALLYCHAT_CHAT_URL}/agent_colours.tsv`, { credentials: 'include' });
  const tsvContent = await response.text();
  const lines = tsvContent.split('\n');
  const cssRules = [];

  for (let i = 0; i < lines.length; i++) {
    const [name, lightColor, darkColor] = lines[i].split('\t');
    const cssRule = `.message[user="${name}"] .label { color: ${lightColor}; }; body.dark .message[user="${name}"] .label { color: ${darkColor}; }`;
    cssRules.push(cssRule);
  }

  const fullCss = cssRules.join('\n');
  $css("agent_colours", fullCss);
}

// main ----------------------------------------------------------------------

async function load_user_script() {
  modules.user_script = await import(ALLYCHAT_CHAT_URL + "/users/" + user + "/script.js")
}

/*
function bugfix_hack_load_bootstrap_icons_font() {
  // There's some CORS issue with fetching our minimal icons font in Firefox,
  // so use the CDN one for now
  if (!isFirefox)
    return;
  const link = document.createElement('link');
  link.rel = 'stylesheet';
  link.href = 'https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.css';
  document.head.appendChild(link);
}
*/

export async function room_main() {
  file_type = "room";

  // register_service_worker();
  deregister_service_worker();

  online();

  $on(document, "readystatechange", ready_state_change);
  $on(document, "error", load_error);

  room = decodeURIComponent(location.pathname.replace(/\.html$/, '').replace(/^\//, ''));

  // check for ?snapshot=1 in URL, properly by parsing the query string
  const url = new URL(location.href);
  if (url.searchParams.has("snapshot")) {
    snapshot = url.searchParams.get("snapshot") && true;
  }

  theme_loaded();

  setup_view_options();

  handle_room_intro();

  // bugfix_hack_load_bootstrap_icons_font();

  setup_mutation_observer();
  await process_current_messages(); // must be after setup_mutation_observer

  await wait_for_load();
  // console.log("room loaded");

  $on($overlay, "click", overlay_click);
  $on($overlay, "auxclick", overlay_click);
  setup_swipe();
  $on(document, "click", click);
  $on(document, "auxclick", click);
  $on(window, "resize", () => run_hooks("window_resize"));
  $on(window, "message", handle_message);

  $on($body, "mousedown", mouse_down);
  $on($body, "mousemove", mouse_move);
  $on($body, "mouseup", mouse_up);
  $on($body, "touchstart", touch_start, { passive: true });
  $on($body, "touchmove", touch_move, { passive: false });
  $on($body, "touchend", touch_end);
  $on($body, "touchcancel", touch_cancel);
  // double click / tap
  $on($body, "dblclick", mouse_double_click);

  setup_keyboard_shortcuts();
  if (inIframe)
    window.parent.postMessage({ type: "ready", theme: theme }, ALLYCHAT_CHAT_URL);
  add_hook("window_resize", window_resized);

//  new ResizeObserver(canvas_resized).observe($canvas_div);
  $on($messages_wrap, "scroll", messages_scrolled);
  const resizeObserver = new ResizeObserver(messages_resized);
  resizeObserver.observe($messages);
//  $on($canvas_div, "scroll", canvas_scrolled);

  window_resized();
  messages_scrolled();

  $on($("div.resizer"), "mousedown", dragResizer);
  $on($("div.resizer"), "touchstart", dragResizer, { passive: true });

  $on(document, "fullscreenchange", fullscreenchange);

  $on($id("overlay_help"), "click", hide_overlay_help);

  if (typeof room_user_script === 'function') {
    room_user_script();
  }

  const [date, mtime] = await get_date_and_mtime();
  if (date && mtime)
    show_timestamp(date, mtime);
  setTimeout(hide_timestamp, 10000);

  load_agent_colours(); // async
}

export async function folder_main() {
  file_type = "dir";

  // register_service_worker();

  room = decodeURIComponent(location.pathname.replace(/\.html$/, '').replace(/^\//, ''));

  // check for ?snapshot=1 in URL, properly by parsing the query string
  const url = new URL(location.href);
  if (url.searchParams.has("snapshot")) {
    snapshot = url.searchParams.get("snapshot") && true;
  }

  theme_loaded();

  setup_view_options();

  $on(window, "message", handle_message);
  // setup_keyboard_shortcuts();

  if (typeof room_user_script === 'function') {
    room_user_script();
  }

  if (inIframe) {
    await wait_for_document_load(true);
    window.parent.postMessage({ type: "ready", theme: theme }, ALLYCHAT_CHAT_URL);
  }
}
