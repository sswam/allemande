// sticky notes --------------------------------------------------------------
// clauden version using transform, is broken

let dragSticky = null;
let offsetX = 0;
let offsetY = 0;
let initialTransform = { x: 0, y: 0 }; // Track the initial transform when dragging starts

// Helper to get coordinates from either mouse or touch event
function getEventCoordinates(e) {
  if (e.touches) {
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

// Helper to get current transform values
function getCurrentTransform(element) {
  const transform = element.style.transform;
  if (!transform || transform === 'none') {
    return { x: 0, y: 0 };
  }

  const match = transform.match(/translate\((-?\d+(?:\.\d+)?)px,\s*(-?\d+(?:\.\d+)?)px\)/);
  if (match) {
    return {
      x: parseFloat(match[1]),
      y: parseFloat(match[2])
    };
  }
  return { x: 0, y: 0 };
}

// Helper to set transform
function setTransform(element, x, y) {
  element.style.transform = `translate(${x}px, ${y}px)`;
}

function mouse_down(e) {
  if (e.target.tagName === 'STICKY') {
    const coords = getEventCoordinates(e);
    const rect = e.target.getBoundingClientRect();

    dragSticky = e.target;
    dragSticky.classList.add('moving');

    // Get current transform values
    initialTransform = getCurrentTransform(dragSticky);

    // Calculate offset from the element's current position (including any existing transform)
    offsetX = coords.clientX - rect.left;
    offsetY = coords.clientY - rect.top;
  }
}

function mouse_move(e) {
  if (dragSticky) {
    const coords = getEventCoordinates(e);
    const rect = dragSticky.getBoundingClientRect();

    // Calculate new position relative to the element's original position
    const newX = initialTransform.x + (coords.clientX - offsetX - (rect.left - initialTransform.x));
    const newY = initialTransform.y + (coords.clientY - offsetY - (rect.top - initialTransform.y));

    setTransform(dragSticky, newX, newY);
  }
}

function mouse_up() {
  if (dragSticky) {
    const currentTransform = getCurrentTransform(dragSticky);

    // If back at origin (or very close), remove transform entirely
    if (Math.abs(currentTransform.x) < 1 && Math.abs(currentTransform.y) < 1) {
      dragSticky.classList.remove('moving');
      dragSticky.style.removeProperty('transform');
    }

    dragSticky.classList.remove('moving');
    dragSticky = null;
  }
}

function mouse_double_click(e) {
  // move back to original position
  if (e.target.tagName === 'STICKY') {
    e.target.style.removeProperty('transform');
    e.target.classList.remove('moving');
  }
}

// Touch event handlers
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

function touch_end() {
  mouse_up();
}

// Handle touch cancel - this fires when the touch is interrupted
// (e.g., by a system gesture, phone call, or moving finger outside browser)
function touch_cancel() {
  if (dragSticky) {
    // Reset to the position before dragging started
    setTransform(dragSticky, initialTransform.x, initialTransform.y);
    dragSticky.classList.remove('moving');
    dragSticky = null;
  }
}



  $on($body, "touchcancel", touch_cancel);
