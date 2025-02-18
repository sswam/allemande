// status indicator ----------------------------------------------------------

const timeout_seconds = 60;

const CHAT_URL =
  location.protocol + "//" + location.host.replace(/^rooms\b/, "chat");

let $body, $messages, $overlay;

let timeout;

let overlay_mode = false;
let $currentImg;
let currentImgIndex;
let allImages;
let overlay_fullscreen = true;

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

function online() {
  clearTimeout(timeout);
  timeout = setTimeout(offline, 1000 * timeout_seconds);
  const status = get_status_element();
  //	status.innerText = '🔵';
  status.innerText = "";
}

function offline() {
  const status = get_status_element();
  status.innerText = "🔴";
  document.body.addEventListener("mouseenter", reload, { once: true });
}

function clear() {
  $("div.messages").innerHTML = "";
}

function ready_state_change() {
  if (document.readyState !== "loading") {
    offline();
  }
}

online();

$on(document, "readystatechange", ready_state_change);

// scrolling to the bottom ---------------------------------------------------

let messages_at_bottom = true;
let messages_height_at_last_scroll;

function is_at_bottom($e) {
  const bot = Math.abs($e.scrollHeight - $e.scrollTop - $e.offsetHeight) < 8;
  return bot;
}

function scroll_to_bottom() {
  var $e = $("html");
  $e.scrollTop = $e.scrollHeight;
  messages_height_at_last_scroll = $e.scrollHeight;
}

function messages_scrolled() {
  var $e = $("html");
  if (messages_at_bottom) {
    var messages_height = $e.scrollHeight;
    if (messages_height != messages_height_at_last_scroll) {
      messages_height_at_last_scroll = messages_height;
      scroll_to_bottom($e);
    }
  }
  messages_at_bottom = is_at_bottom($e);
}

function check_for_new_content(mutations) {
  let new_content = false;
  for (const mutation of mutations) {
    if (mutation.type != "childList") {
      continue;
    }
    for (const node of mutation.addedNodes) {
      if (
        node.nodeType == Node.ELEMENT_NODE &&
        node.tagName == "DIV" &&
        node.classList.contains("content")
      ) {
        return true;
      }
    }
  }
  return false;
}

// resize observer -----------------------------------------------------------

function resized(entries) {
  messages_scrolled();
}

async function setup_resize_observer() {
  await wait_for_body();
  new ResizeObserver(resized).observe(document.body);
}

// mutation observer ---------------------------------------------------------

function mutated(mutations) {
  if (check_for_new_content(mutations)) {
    online();
  }
  process_messages(mutations);
  messages_scrolled();
}

function setup_mutation_observer() {
  new MutationObserver(mutated).observe($("html"), {
    childList: true,
    subtree: true,
  });
}

$on(window, "scroll", messages_scrolled);

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
];
const ctrlKeysToKeep = ["c", "a", "f", "0"];

function key_event(ev) {
  setup_ids();
  // console.log("key_event", ev);
  if (overlay_mode) {
    return key_event_overlay(ev);
  }
  if (ev.altKey && ev.key == "f") {
    ev.preventDefault();
    toggle_fullscreen();
    return;
  }
  if (
    keysToKeep.includes(ev.key) ||
    (ev.ctrlKey && ctrlKeysToKeep.includes(ev.key))
  ) {
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
  window.parent.postMessage(copy, CHAT_URL);
  ev.preventDefault();
}

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

// embed = `<iframe width="280" height="157" src="https://www.youtube.com/embed/{video_id}" title="{title_enc}" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" allowfullscreen></iframe>`

function embed_click($thumb) {
  const $embed = $thumb.parentNode;
  let iframe_html;
  if ($embed.dataset.site == "youtube") {
    iframe_html = `<iframe width="280" height="157" src="https://www.youtube.com/embed/${$embed.dataset.videoid}?autoplay=1" title="${$thumb.alt}" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share; fullscreen" allowfullscreen></iframe>`;
  } else if ($embed.dataset.site == "pornhub") {
    iframe_html = `<iframe src="https://www.pornhub.com/embed/${$embed.dataset.videoid}" frameborder="0" width="280" height="157" scrolling="no" allowfullscreen></iframe>`;
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

function is_fullscreen() {
  return document.fullscreenElement;
}

function go_fullscreen() {
  if (is_fullscreen()) {
    return;
  }
  document.documentElement.requestFullscreen().catch((err) => console.error(err));
}

function exit_fullscreen() {
  if (!is_fullscreen()) {
    return;
  }
  document.exitFullscreen().catch((err) => console.error(err));
}

function toggle_fullscreen() {
  if (is_fullscreen()) {
    exit_fullscreen();
    overlay_fullscreen = false;
  } else {
    go_fullscreen();
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

function image_overlay($img) {
  setup_ids();
  const $img_clone = $img.cloneNode();
  $overlay.innerHTML = "";
  $overlay.appendChild($img_clone);
  $body.classList.add("overlay");
  overlay_mode = true;
  signal_overlay(true);

  // Get all images and current image index
  allImages = Array.from($messages.getElementsByTagName("IMG"));
  $currentImg = $img;
  currentImgIndex = allImages.indexOf($img);

  // focus the overlay, for keyboard scrolling
  $overlay.focus();

  if (overlay_fullscreen) {
    go_fullscreen();
  }

  add_hook("resize", setup_overlay_image_cover);
  setup_overlay_image_cover();
}

function overlay_close(ev) {
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
  $currentImgIndex = null;

  remove_hook("resize", setup_overlay_image_cover);
}

function signal_overlay(overlay) {
  window.parent.postMessage({ type: "overlay", overlay: overlay }, CHAT_URL);
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
}

function overlay_click(ev) {
  if (lastSwipeDistance > maxClickDistance) {
    lastSwipeDistance = 0;
    return;
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
  e.preventDefault();
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
  $overlay.addEventListener('touchstart', touch_start);
  $overlay.addEventListener('touchmove', touch_move, { passive: false });
  $overlay.addEventListener('touchend', touch_end);
  // For desktop dragging also
  $overlay.addEventListener('mousedown', touch_start);
  $overlay.addEventListener('mousemove', touch_move);
  $overlay.addEventListener('mouseup', touch_end);
  $overlay.addEventListener('mouseleave', touch_end);
}

// ---------------------------------------------------------------------------

function image_click($img, ev) {
  // check if in overlay
  if (ev.shiftKey) {
    window.open($img.src, "_blank");
  } else if (ev.ctrlKey || ev.metaKey || ev.button === 1) {
    window.open($img.src, "_blank").focus();
  } else if (ev.altKey) {
    window.top.location.href = ev.target.src;
  } else if (!overlay_mode) {
    image_overlay($img);
  }
}

function click(ev) {
  setup_ids();
  if (!$messages.contains(ev.target)) {
    return;
  }
  if (ev.target.classList.contains("thumb") && ev.button == 0) {
    embed_click(ev.target);
    return;
  }
  // check for img tag, and view or browse to the src
  if (ev.target.tagName == "IMG") {
    image_click(ev.target, ev);
    return;
  }
}

function setup_ids() {
  if ($body) {
    return;
  }
  $body = $("body");
  $messages = $("div.messages");
  $overlay = $("div.overlay");
  $on($overlay, "click", overlay_click);
  setup_swipe();
}

function notify_new_message(newMessage) {
  // send a message to the parent window
  window.parent.postMessage({ type: "new_message", message: newMessage }, CHAT_URL);
}

// view options --------------------------------------------------------------

async function handle_message(ev) {
  // console.log("room handle_message", ev);
  if (ev.origin !== CHAT_URL) {
    console.error("ignoring message from", ev.origin);
    return;
  }
  if (ev.data.type === "set_view_options") {
    await wait_for_body();
    const view_images = ev.data.images;
    const cl = document.body.classList;
    if (view_images == 2) {
      cl.add("images");
      cl.remove("images_alt");
    } else if (view_images == 1) {
      cl.add("images_alt");
      cl.remove("images");
    } else {
      cl.remove("images");
      cl.remove("images_alt");
    }

    const view_sources = ev.data.source;
    if (view_sources == 1) {
      cl.add("source");
    } else {
      cl.remove("source");
    }
  }
}

// wait for body to be ready -------------------------------------------------

function wait_for_body() {
  return new Promise(resolve => {
    if (document.body) {
      resolve();
      return;
    }

    const observer = new MutationObserver(mutations => {
      if (document.body) {
        observer.disconnect();
        resolve();
      }
    });

    observer.observe(document.documentElement, { childList: true });
  });
}

// main ----------------------------------------------------------------------

function room_main() {
  $on(document, "click", click);
  $on(document, "auxclick", click);
  $on(window, "resize", () => run_hooks("resize"));
  $on(window, "message", handle_message);
  setup_keyboard_shortcuts();
  window.parent.postMessage({ type: "ready" }, CHAT_URL);
  setup_resize_observer();
  setup_mutation_observer();
}

room_main();
