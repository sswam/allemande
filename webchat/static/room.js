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

function mutated(mutations) {
  if (check_for_new_content(mutations)) {
    online();
  }
  process_messages(mutations);
  messages_scrolled();
}

new MutationObserver(mutated).observe($("html"), {
  childList: true,
  subtree: true,
});

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
    toggle_maxpect();
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

function is_fullscreen() {
  return document.fullscreenElement;
}

function go_fullscreen() {
  if (is_fullscreen()) {
    return;
  }
  document.documentElement.requestFullscreen().catch((err) => console.log(err));
}

function exit_fullscreen() {
  if (!is_fullscreen()) {
    return;
  }
  document.exitFullscreen().catch((err) => console.log(err));
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

function toggle_maxpect() {
  if ($overlay.classList.contains("maxpect")) {
    $overlay.classList.remove("maxpect");
  } else {
    $overlay.classList.add("maxpect");
  }
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

function image_overlay($img) {
  console.log("image_overlay");
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
}

function overlay_close(ev) {
  ev.preventDefault();
  console.log("overlay_close");
  $body.classList.remove("overlay");
  $overlay.innerHTML = "";
  exit_fullscreen();
  overlay_mode = false;
  signal_overlay(false);

  // Reset current image index
  allImages = null;
  $currentImg = null;
  $currentImgIndex = null;
}

function signal_overlay(overlay) {
  console.log("signal_overlay", overlay);
  window.parent.postMessage({ type: "overlay", overlay: overlay }, CHAT_URL);
}

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
  $on($overlay, "click", overlay_close);
}

function notify_new_message(newMessage) {
  // send a message to the parent window
  window.parent.postMessage({ type: "new_message", message: newMessage }, CHAT_URL);
}

$on(document, "click", click);
$on(document, "auxclick", click);

setup_keyboard_shortcuts();
