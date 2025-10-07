// Scroll position management ---------------------------------------------------

const SCROLL_THRESHOLD = 24; // pixels from bottom to consider "at bottom"
const SCROLL_DEBOUNCE_DELAY_SAVE = 100;
const SCROLL_DEBOUNCE_DELAY_SCROLLED = 200;
const SCROLL_DEBOUNCE_DELAY_RESTORE = 100;
const SCROLL_RESTORE_TIMEOUT = 5000;
const SCROLL_SHOW_LAST_DURATION = 10000;

let scroll_at_end = false;

let $messages_wrap = null;
let room = null;
let scroll_restored = false;

// intersection observer for scroll position ---------------------------------

let messages_intersection_observer;
let first_visible_message_id = null, last_visible_message_id = null;
let first_visible_message = null, last_visible_message = null;
let visibleMessages = new Set();

function scroll_init($messages_wrap_, room_) {
  $messages_wrap = $messages_wrap_;
  room = room_;
  messages_intersection_observer = new IntersectionObserver((entries) => scroll_messages_intersection_changed(entries), {
    root: $messages_wrap,
    threshold: 0.0,
  });
}

function scroll_messages_intersection_changed(entries) {
  for (const entry of entries) {
    entry.target.classList.toggle("visible", entry.isIntersecting);
    const id = +entry.target.id.substring(1);
    if (entry.isIntersecting)
      visibleMessages.add(id);
    else
      visibleMessages.delete(id);
  }

  const ids = Array.from(visibleMessages);
  first_visible_message_id = ids.length ? Math.min(...ids) : null;
  last_visible_message_id = ids.length ? Math.max(...ids) : null;
  first_visible_message = first_visible_message_id !== null ? document.getElementById("m" + first_visible_message_id) : null;
  last_visible_message = last_visible_message_id !== null ? document.getElementById("m" + last_visible_message_id) : null;

  scroll_save_position();
}

function scroll_save_position_2() {
  // console.log("scroll_save_position_2");
  const isColumns = view_options.columns;
  const containerRect = $messages_wrap.getBoundingClientRect();
  const messageRect = first_visible_message?.getBoundingClientRect();
  // console.log("containerRect =", containerRect);
  // console.log("messageRect =", messageRect);

  // console.log(containerRect.top, messageRect?.top);

  const frac = !first_visible_message
  ? 0
  : isColumns
  ? (containerRect.left - messageRect.left) / (messageRect.width || 1)
  : (containerRect.top - messageRect.top) / (messageRect.height || 1);

  const scrollData = { first: first_visible_message_id, frac, last: last_visible_message_id };
  // console.log("scroll data:", scrollData);
  localStorage.setItem(`scroll_${room}`, JSON.stringify(scrollData));
}

const scroll_save_position = debounce(scroll_save_position_2, SCROLL_DEBOUNCE_DELAY_SAVE);

function scroll_add_message($msg) {
  messages_intersection_observer.observe($msg);
}

function scroll_remove_message($msg) {
  // not used yet
  messages_intersection_observer.unobserve($msg);
}

function scroll_is_at_end($e) {
  return view_options.columns
    ? Math.abs($e.scrollWidth - $e.scrollLeft - $e.clientWidth) < SCROLL_THRESHOLD
    : Math.abs($e.scrollHeight - $e.scrollTop - $e.clientHeight) < SCROLL_THRESHOLD;
}

function scroll_scrolled_2() {
  const at_end = scroll_is_at_end($messages_wrap);
  scroll_set_messages_at_end(at_end);  // inline?
  scroll_save_position_2();
}

const scroll_scrolled = debounce(scroll_scrolled_2, SCROLL_DEBOUNCE_DELAY_SCROLLED);

function scroll_set_messages_at_end(at_end) {
  if (at_end != scroll_at_end) {
    scroll_at_end = at_end;
    window.parent.postMessage({
      type: "status",
      scroll_at_end: scroll_at_end
    }, ALLYCHAT_CHAT_URL);
  }
  // console.log("scroll_at_end =", scroll_at_end);
}

const scroll_restore = debounce(scroll_restore_2, SCROLL_DEBOUNCE_DELAY_RESTORE);

async function scroll_restore_2() {
  // console.log("scroll_restore_2");
  const savedData = localStorage.getItem(`scroll_${room}`);
  const scrollData = JSON.parse(savedData || "null") || { first: null, frac: 0, last: null };

  let $first = null, $last = null;
  try {
    if (scrollData.first !== null) {
      await wait_for(() => document.getElementById("m"+scrollData.first), SCROLL_RESTORE_TIMEOUT);
      $first = $id("m" + scrollData.first);
    }
    if (scrollData.last !== null) {
      await wait_for(() => document.getElementById("m"+scrollData.last), SCROLL_RESTORE_TIMEOUT);
      $last = $id("m" + scrollData.last);
    }
  } catch (e) {
    console.warn("scroll_restore_2: timeout waiting for messages to appear");
  }

  // console.log("scroll_restore: scrollData =", scrollData, "$first =", $first, "$last =", $last);

  if (!$first)
    return;

  const isColumns = view_options.columns;
  const msgStart = isColumns ?
    ($first.offsetLeft - $messages_wrap.offsetLeft) :
    ($first.offsetTop - $messages_wrap.offsetTop);
  const msgSize = isColumns ?
    $first.offsetWidth :
    $first.offsetHeight;

  const scrollPos = msgStart + (msgSize * scrollData.frac);

  if (isColumns)
    $messages_wrap.scrollLeft = scrollPos;
  else
    $messages_wrap.scrollTop = scrollPos;

  scroll_scrolled_2();

  // console.log("$last = ", $last, "scroll_restored =", scroll_restored, "scroll_at_end =", scroll_at_end);

  if ($last && !scroll_restored && !scroll_at_end && $last !== $messages_wrap.querySelector(".message:not(.hidden)")) {
    $last.classList.add("last")
    setTimeout(() => $last.classList.remove("last"), SCROLL_SHOW_LAST_DURATION)
  }
  scroll_restored = true;
}

function scroll_to_end($e) {
  if (view_options.columns)
    $e.scrollLeft = $e.scrollWidth;
  else
    $e.scrollTop = $e.scrollHeight;
}

function scroll_follow_end() {
  if (scroll_at_end)
    scroll_to_end($messages_wrap);
}
