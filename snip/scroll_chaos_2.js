

/*

let restoringScroll = false;

let scrollAnchor = null; // { id: string, percentage: number } | null

let $messages_wrap = null;
let room = null;

const saveScrollPosition = debounce(saveScrollPosition2, SCROLL_DEBOUNCE_DELAY);

function saveScrollPosition2() {
  console.log("saveScrollPosition called, restoringScroll =", restoringScroll);
  if (restoringScroll) return;

  const $e = $messages_wrap;

  // Update messages_at_bottom status immediately
  const currentlyAtBottom = is_at_bottom($e);
  set_messages_at_bottom(currentlyAtBottom);

  // if (currentlyAtBottom) {
  //   localStorage.setItem(`scroll_${room}`, JSON.stringify(null));
  //   scrollAnchor = null; // Clear anchor if at bottom
  //   console.log("At bottom, cleared scroll anchor");
  //   return; // Exit if at bottom
  // }

  const visibleMessages = findVisibleMessages($e);

  if (visibleMessages.length == 0) {
    // If no messages are visible (e.g., chat is empty, or all messages scrolled off-screen),
    // clear the anchor.
    localStorage.setItem(`scroll_${room}`, JSON.stringify(null));
    scrollAnchor = null;
    console.log("No visible messages found, cleared scroll anchor.");
    return;
  }

  const firstVisible = visibleMessages[0];
  const rect = firstVisible.getBoundingClientRect();
  const containerRect = $e.getBoundingClientRect();
  const isColumns = view_options.columns;

  let visibleStart, elementStart, percentage;
  if (isColumns) {
    visibleStart = Math.max(rect.left, containerRect.left);
    elementStart = rect.left;
    percentage = ((visibleStart - elementStart) / rect.width) * 100;
  } else {
    visibleStart = Math.max(rect.top, containerRect.top);
    elementStart = rect.top;
    percentage = ((visibleStart - elementStart) / rect.height) * 100;
  }

  scrollAnchor = {
    id: firstVisible.id || "m0",
    // Ensure percentage is valid, clamp between 0 and 100
    percentage: Math.max(0, Math.min(100, percentage))
  };
  localStorage.setItem(`scroll_${room}`, JSON.stringify(scrollAnchor));
  console.log("Saved scroll anchor based on findVisibleMessages", scrollAnchor);
}

// eslint-disable-next-line no-unused-vars
async function restoreScrollPosition() {
  const $e = $messages_wrap;

  const savedData = localStorage.getItem(`scroll_${room}`);
  const scrollData = JSON.parse(savedData || "null");

  if (!scrollData) {
    console.log("No saved scroll data");
    return;
  }

  restoringScroll = true;

  let targetElement = scrollData.id === "m0" ?
    $e.querySelector(".message") :
    document.getElementById(scrollData.id);

  if (!targetElement) {
    try {
      await wait_for(() => document.getElementById(scrollData.id), RESTORE_SCROLL_TIMEOUT);
      targetElement = document.getElementById(scrollData.id);
      console.log("Found target element after wait", scrollData.id, targetElement);
    } catch (e) {
      targetElement = $e.querySelector(".message:last-child");
      console.error("timeout waiting for target element", scrollData.id, e);
      console.log("Falling back to last message", targetElement);
    }
  }

  if (targetElement) {
    const isColumns = view_options.columns;
    const msgStart = isColumns ?
      (targetElement.offsetLeft - $e.offsetLeft) :
      (targetElement.offsetTop - $e.offsetTop);
    const msgSize = isColumns ?
      targetElement.offsetWidth :
      targetElement.offsetHeight;

    let scrollPos = 0;

    if (!(scrollData.id === "m0" && scrollData.percentage === 0)) {
      scrollPos = msgStart + (msgSize * scrollData.percentage / 100);
    }

    if (isColumns) {
      $e.scrollLeft = scrollPos;
    } else {
      $e.scrollTop = scrollPos;
    }

    console.log("Restored scroll position to", scrollData, scrollPos);
  }

  set_messages_at_bottom(is_at_bottom($e));

  restoringScroll = false;
}

function scroll_to_bottom($e) {
  console.log("scroll_to_bottom called");
  if (view_options.columns) {
    $e.scrollLeft = $e.scrollWidth;
  } else {
    $e.scrollTop = $e.scrollHeight;
  }
}

// eslint-disable-next-line no-unused-vars
function scroll_to_bottom_if_needed() {
  if (messages_at_bottom)
    scroll_to_bottom($messages_wrap);
}

// Main scroll handler
// eslint-disable-next-line no-unused-vars
function messages_scrolled() {
  saveScrollPosition();
}

function setup_scroll($messages_wrap_, room_) {
  $messages_wrap = $messages_wrap_;
  room = room_;
}
*/

