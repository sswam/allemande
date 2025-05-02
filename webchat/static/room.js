const offline_timeout_seconds = 10;

const isMobile = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
const inIframe = window.parent !== window.self;

let file_type;
let room;

let $body, $messages, $overlay, $messages_wrap, $canvas_div;

let offline_timeout;

let overlay_mode = false;
let $currentImg;
let currentImgIndex;
let allImages;
let overlay_fullscreen = isMobile;

let suppressInitialScroll = false;

export let view_options = {
  images: 1,
  image_size: 8,
  font_size: 4,
  items: 10,
};

let mode_options = {
  select: 0,
};

let snapshot = false;

// status indicator ----------------------------------------------------------

function get_status_element() {
  let status = $id("allemande_status");
  if (!status) {
    status = $create("div");
    status.id = "allemande_status";
    $append(document.lastChild, status);
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
  clean_up_server_events();
}

function offline() {
  // console.log("offline!");
  if (snapshot)
    return;
  const status = get_status_element();
  status.innerText = "🔴";
  document.body.addEventListener("mouseenter", reload, { once: true });
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

let messages_at_bottom = true;
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

async function messages_scrolled() {
  // console.log("messages scrolled");
  await wait_for_load();
  var $e = $messages_wrap;
  if (!$e)
    return;
  if (messages_at_bottom && view_options.columns) {
    var messages_width = $e.scrollWidth;
    if (messages_width != messages_width_last) {
      messages_width_last = messages_width;
      if (!suppressInitialScroll) {
        scroll_to_bottom($e);
      }
    }
  } else if (messages_at_bottom) {
    var messages_height = $e.scrollHeight;
    if (messages_height != messages_height_last) {
      messages_height_last = messages_height;
      if (!suppressInitialScroll) {
        scroll_to_bottom($e);
      }
    }
  }
  messages_at_bottom = is_at_bottom($e);

  if (view_options.columns) {
    top_message = getLeftmostVisibleElement();
  } else {
    top_message = getTopmostVisibleElement();
  }
  // console.log("top message", top_message);
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
    await wait_for(() => node_has_next_sibling(node), 1000);   // newline works
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
  "Alt",
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
  // console.log("key_event", ev);
  if (overlay_mode) {
    return key_event_overlay(ev);
  }
  if (ev.altKey && ev.key == "g") {
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
  if (ev.key == "Escape" || ev.key == "q") {
    overlay_close(ev);
  } else if (ev.key == "f") {
    toggle_fullscreen();
  } else if (ev.key == "m") {
    cycle_zoom();
  } else if (ev.key == "ArrowLeft" || ev.key == "Backspace") {
    image_go(-1);
  } else if (ev.key == "ArrowRight" || ev.key == " ") {
    image_go(1);
  } else if (ev.key == "PageUp") {
    image_go(-10);
  } else if (ev.key == "PageDown") {
    image_go(10);
  } else if (ev.key == "Home") {
    image_go_to(0);
  } else if (ev.key == "End") {
    image_go_to(-1);
  } else {
    return;
  }
  ev.preventDefault();
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
    iframe_html = `<iframe width="280" height="157" src="https://www.youtube.com/embed/${$embed.dataset.videoid}?autoplay=1" title="${$thumb.alt}" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share; fullscreen" allowfullscreen></iframe>`;
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

function toggle_fullscreen(target) {
  if (is_fullscreen()) {
    exit_fullscreen();
    signal_overlay(false);
    overlay_fullscreen = false;
  } else {
    go_fullscreen(target);
    signal_overlay(true);
    overlay_fullscreen = true;
  }
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
  // console.log("image_overlay", $el);
  // check if it's an A
  let $img;
  if ($el.tagName === "A") {
    $currentImg = $el.querySelector("img");
  } else {
    $currentImg = $el;
  }
  $overlay.innerHTML = "";
  $img = $create("img");
  $overlay.appendChild($img);
  $body.classList.add("overlay");
  overlay_mode = true;
  signal_overlay(true);

  // Get all images and links containing images in document order
  allImages = Array.from($messages.querySelectorAll('img:not(.hidden)')).filter(img => !img.closest('.hidden'));

  currentImgIndex = allImages.indexOf($currentImg);
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
}

function overlay_close(ev) {
  if (ev)
    ev.preventDefault();
  $body.classList.remove("overlay");
  clear_overlay_image_cover();
  $overlay.innerHTML = "";
  exit_fullscreen();
  overlay_mode = false;
  signal_overlay(false);

  // Reset current image index
  allImages = null;
  $currentImg = null;
  currentImgIndex = null;

  remove_hook("resize", setup_overlay_image_cover);
}

function signal_overlay(overlay) {
  if (inIframe)
    window.parent.postMessage({ type: "overlay", overlay: overlay }, ALLYCHAT_CHAT_URL);
}

function image_go(delta) {
  image_go_to(currentImgIndex + delta);
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
  if (ev.clientX < container.width / 4) {
    image_go(-1);
  } else if (ev.clientX > container.width * 3 / 4) {
    image_go(1);
  } else if (ev.clientY < container.height / 4) {
    toggle_fullscreen();
  } else if (ev.clientY > container.height * 3 / 4) {
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
    if (Math.abs(swipeDistanceY) >= minSwipeDistance) {
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

function touch_start(e) {
  if (e.touches && e.touches.length == 1) {
    touchStartX = touchStartY = null;
    return;
  }
  if (e.touches) {
    touchStartX = e.touches[0].clientX;
    touchStartY = e.touches[0].clientY;
  } else {
    touchStartX = e.clientX;
    touchStartY = e.clientY;
  }
}

function touch_end(e) {
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

function touch_move(e) {
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
  $overlay.addEventListener('touchstart', touch_start, { passive: true });
  $overlay.addEventListener('touchmove', touch_move, { passive: false });
  $overlay.addEventListener('touchend', touch_end);
  // For desktop dragging also
  $overlay.addEventListener('mousedown', touch_start);
  $overlay.addEventListener('mousemove', touch_move);
  $overlay.addEventListener('mouseup', touch_end);
  $overlay.addEventListener('mouseleave', touch_end);
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
  } else if (ev.ctrlKey || ev.metaKey || ev.button === 1 || view_options["embed"]) {
    window.open(src, "_blank").focus();
  } else if (!overlay_mode) {
    image_overlay($el);
  }
}

function click(ev) {
  if (!$messages.contains(ev.target)) {
    return;
  }

  // focus on message if clicked, can show IDs
  // TODO, only in "select mode", keyboard control / accessibility...
  /*
  const $message = ev.target.closest(".message");
  if ($message) {
    ev.preventDefault();
    select_message($message, ev.shiftKey, ev.ctrlKey);
  }
  */

  if (ev.target.classList.contains("thumb") && ev.target.parentNode.classList.contains("embed")) {
    ev.preventDefault();
    return embed_click(ev, ev.target);
  }
  // check for img tag, and view or browse to the src
  if (ev.target.tagName == "IMG") {
    ev.preventDefault();
    return image_click(ev.target, ev);
  }
  // check for A tag containing an image
  if (ev.target.tagName === "A" && ev.target.querySelector("img")) {
    ev.preventDefault();
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
    cl.toggle("images", view_options.images == 1);
    cl.toggle("alt", view_options.alt == 1);
    cl.toggle("script_source", view_options.source >= 1);
    cl.toggle("rendered_source", view_options.source >= 2);
    cl.toggle("canvas", view_options.canvas >= 1);
    cl.toggle("messages", view_options.canvas <= 1);
    cl.toggle("clean", view_options.clean == 1);
    cl.toggle("columns", view_options.columns == 1);
    cl.toggle("history", view_options.history == 1);
    cl.toggle("ids-hover", view_options.ids == 1);
    cl.toggle("ids", view_options.ids == 2);
  }

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

// scroll to home or end, page up, page down ---------------------------------

function scroll_home_end(p) {
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
  const hasSeenIntro = !['guide', 'intro'].includes(room) && localStorage.getItem(`seen_intro_${room}`);
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

// main ----------------------------------------------------------------------

async function load_user_script() {
  modules.user_script = await import(ALLYCHAT_CHAT_URL + "/users/" + user + "/script.js")
}

async function deregister_service_worker() {
  if (!navigator.serviceWorker)
    return;
  const registrations = await navigator.serviceWorker?.getRegistrations() || [];
  for (const registration of registrations) {
    await registration.unregister();
  }
}

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

  setup_mutation_observer();
  await process_current_messages(); // must be after setup_mutation_observer

  await wait_for_load();
  // console.log("room loaded");

  $on($overlay, "click", overlay_click);
  $on($overlay, "auxclick", overlay_click);
  setup_swipe();
  // $on(document, "click", click);
  $on(document, "click", click);
  $on(document, "auxclick", click);
  $on(window, "resize", () => run_hooks("window_resize"));
  $on(window, "message", handle_message);
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

  if (typeof room_user_script === 'function') {
    room_user_script();
  }

  // $on(document, "fullscreenchange", fullscreenchange);
}

/*
function fullscreenchange(ev) {
  if (!is_fullscreen())
    overlay_close();
}
*/

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
  if (inIframe)
    window.parent.postMessage({ type: "ready", theme: theme }, ALLYCHAT_CHAT_URL);

  if (typeof room_user_script === 'function') {
    room_user_script();
  }
}
