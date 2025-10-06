// scrolling to the bottom ---------------------------------------------------

let suppressInitialScroll = true;

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



function room_scroll_setup() {
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
