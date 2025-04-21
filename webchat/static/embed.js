var widget = document.getElementById("help-widget");
var header = document.getElementById("help-widget-header");
var iframe = document.getElementById("help-frame");
var overlay = document.getElementById("messages_overlay");

// Config
var allowOffscreen = false; // Whether widget can partially move offscreen

// Track widget state
var isDragging = false;
var isResizing = false;
var currentX, currentY, initialX, initialY;
var initialWidth, initialHeight, initialTop, initialLeft;
var resizeEdge = { top: false, right: false, bottom: false, left: false };
var preMaximizeState = null; // Store pre-maximize dimensions

// --- Get CSS Variables ---
var computedStyle = getComputedStyle(widget);
var pad = parseInt(computedStyle.getPropertyValue("--pad")) || 10; // Get padding value


// Add resize cursors
var cursorMap = {
  top: "n-resize",
  right: "e-resize",
  bottom: "s-resize",
  left: "w-resize",
  "top,left": "nw-resize",
  "top,right": "ne-resize",
  "bottom,left": "sw-resize",
  "bottom,right": "se-resize"
};

// Window resize handler
window.addEventListener("resize", function() {
  if(!allowOffscreen) {
    // Keep widget in bounds
    var rect = widget.getBoundingClientRect();
    var newLeft = Math.min(rect.left, window.innerWidth - rect.width);
    var newTop = Math.min(rect.top, window.innerHeight - rect.height);
    newLeft = Math.max(0, newLeft);
    newTop = Math.max(0, newTop);

    widget.style.left = newLeft + "px";
    widget.style.top = newTop + "px";
  }
});

// Double click handler for maximize
header.addEventListener("dblclick", function() {
  if(preMaximizeState) {
    // Restore
    Object.assign(widget.style, preMaximizeState);
    preMaximizeState = null;
  } else {
    // Maximize
    preMaximizeState = {
      top: widget.style.top,
      left: widget.style.left,
      width: widget.style.width,
      height: widget.style.height
    };
    widget.style.top = "0";
    widget.style.left = "0";
    widget.style.width = "100%";
    widget.style.height = "100%";
  }
});

// Active link handling
document.querySelectorAll("#help-widget-header a").forEach(link => {
  link.addEventListener("click", function() {
    document.querySelectorAll("#help-widget-header a").forEach(l => {
      l.classList.remove("link_active");
    });
    this.classList.add("link_active");
  });
});


// --- Cursor Hover Logic ---
function updateCursor(e) {
  if (isDragging || isResizing) return;

  var rect = widget.getBoundingClientRect();
  var pad = parseInt(getComputedStyle(widget).getPropertyValue("--pad")) || 10;

  // Check proximity to edges within padding area
  var nearLeft = e.clientX > rect.left && e.clientX < rect.left + pad;
  var nearRight = e.clientX < rect.right && e.clientX > rect.right - pad;
  var nearTop = e.clientY > rect.top && e.clientY < rect.top + pad;
  var nearBottom = e.clientY < rect.bottom && e.clientY > rect.bottom - pad;

  var edgeKey = [];
  // Check corners first
  if (nearTop && nearLeft) edgeKey = ['top','left'];
  else if (nearTop && nearRight) edgeKey = ['top','right'];
  else if (nearBottom && nearLeft) edgeKey = ['bottom','left'];
  else if (nearBottom && nearRight) edgeKey = ['bottom','right'];
  // Then edges
  else if (nearTop) edgeKey = ['top'];
  else if (nearBottom) edgeKey = ['bottom'];
  else if (nearLeft) edgeKey = ['left'];
  else if (nearRight) edgeKey = ['right'];

  var cursor = cursorMap[edgeKey.join(',')];
  widget.style.cursor = cursor || 'default';
  header.style.cursor = cursor || 'move';
}

// Attach cursor hover listeners
widget.addEventListener("mousemove", updateCursor);
widget.addEventListener("mouseleave", function() {
    if (!isDragging && !isResizing) {
        widget.style.cursor = 'default';
    }
});


// --- Mouse Down Handler (Drag or Resize Start) ---
widget.onmousedown = function (e) {
  if (e.button !== 0) return;
  // Do nothing if the click is on the close button or inside the iframe content area (already handled)
  if (
    e.target.closest("button") ||
    iframe.contains(e.target) ||
    e.target === iframe
  ) {
    // Check if target is within the iframe container but *not* the iframe itself (i.e. the padding)
    var frameContainer = document.getElementById("help-frame-container");
    if (
      frameContainer &&
      frameContainer.contains(e.target) &&
      e.target !== iframe
    ) {
      // Allow resize/drag detection to proceed if click is in the padding around the iframe
    } else {
      return; // Otherwise, ignore clicks inside iframe/on close button
    }
  }

  initialX = e.clientX;
  initialY = e.clientY;
  initialWidth = widget.offsetWidth;
  initialHeight = widget.offsetHeight;
  initialTop = widget.offsetTop;
  initialLeft = widget.offsetLeft;

  var rect = widget.getBoundingClientRect();

  // Simplify resize detection - check if click is within the padding area
  // This logic matches the original provided code structure
  var isWithinHorizontalPadding =
    (e.clientX > rect.left && e.clientX < rect.left + pad) ||
    (e.clientX < rect.right && e.clientX > rect.right - pad);

  // Vertical padding check - now includes the header area for top
  var isWithinVerticalPadding =
    (e.clientY > rect.top && e.clientY < rect.top + pad) || // Top padding including header
    (e.clientY < rect.bottom && e.clientY > rect.bottom - pad); // Bottom padding


  // Reset edges
  isResizing = false;
  resizeEdge = { top: false, right: false, bottom: false, left: false };

  // Detect resize based on padding click
  if (isWithinHorizontalPadding || isWithinVerticalPadding) {
    isResizing = true;
    // Determine specific edge - prioritize corners
    var cornerThreshold = pad * 1.5; // slightly larger threshold for corners
    var onLeftEdge =
      e.clientX > rect.left && e.clientX < rect.left + cornerThreshold;
    var onRightEdge =
      e.clientX < rect.right && e.clientX > rect.right - cornerThreshold;
    var onBottomEdge =
      e.clientY < rect.bottom && e.clientY > rect.bottom - cornerThreshold;
    // Top edge check - now includes header area within cornerThreshold
    var onTopEdge =
      e.clientY > rect.top && e.clientY < rect.top + cornerThreshold;


    if (onBottomEdge && onLeftEdge) {
      resizeEdge = { bottom: true, left: true };
    } else if (onBottomEdge && onRightEdge) {
      resizeEdge = { bottom: true, right: true };
    }
    // Add top corners
    else if (onTopEdge && onLeftEdge) { resizeEdge = { top: true, left: true }; }
    else if (onTopEdge && onRightEdge) { resizeEdge = { top: true, right: true }; }
    // Edges
    else if (onLeftEdge) {
      resizeEdge = { left: true };
    } else if (onRightEdge) {
      resizeEdge = { right: true };
    }
    else if (onTopEdge) { resizeEdge = { top: true }; }
    else if (onBottomEdge) {
      resizeEdge = { bottom: true };
    } else {
      isResizing = false; // Click was in padding area but not close enough to an edge? (Shouldn't happen with padding check?)
    }
  }

  // Detect drag (only if not resizing and click is on header)
  // Now that top resize includes the header, we need to ensure clicks on the header
  // that are *not* near the top edge (within cornerThreshold) initiate drag.
  // Clicks on the header near the top edge initiate top/corner resize.
  var isClickOnHeader = (e.target === header || header.contains(e.target));
  var isClickNearTopEdge = e.clientY > rect.top && e.clientY < rect.top + cornerThreshold; // Use the same threshold as resize detection

  if (!isResizing && isClickOnHeader && !isClickNearTopEdge) {
    isDragging = true;
    header.classList.add("dragging"); // Add class for CSS styling
    widget.style.cursor = 'grabbing'; // Set cursor for dragging
  } else {
    isDragging = false;
  }

  if (isDragging || isResizing) {
    iframe.style.pointerEvents = "none"; // Prevent iframe from capturing mouse events
    document.addEventListener("mousemove", handleMouseMove);
    document.addEventListener("mouseup", handleMouseUp);
    /* TODO can't move / resize on mobile yet, some bug I guess */
    document.addEventListener("touchmove", handleMouseMove, { passive: false }); // Use same handler, preventDefault in handler
    document.addEventListener("touchend", handleMouseUp);
    if (overlay) {
      overlay.style.display = 'block';
    }
    if (isResizing) { // Set cursor specifically for resizing if resize started
      var edgeKey = [];
      if (resizeEdge.top) edgeKey.push('top');
      if (resizeEdge.bottom) edgeKey.push('bottom');
      if (resizeEdge.left) edgeKey.push('left');
      if (resizeEdge.right) edgeKey.push('right');
      widget.style.cursor = cursorMap[edgeKey.join(',')] || 'default';
    }
  } else {
    // If click didn't start drag or resize, ensure cursor is correct (handled by mousemove hover)
    // widget.style.cursor = 'default'; // This might flash, handled by hover listener
  }
};

// --- Mouse/Touch Move Handler (Dragging or Resizing) ---
function handleMouseMove(e) {
  // Determine current coords from mouse or touch event
  var currentClientX = e.clientX ?? e.touches?.[0]?.clientX;
  var currentClientY = e.clientY ?? e.touches?.[0]?.clientY;

  if (currentClientX === undefined || currentClientY === undefined) return;

  // Use preventDefault for touchmove to stop scrolling when dragging/resizing
  if (e.touches && (isDragging || isResizing)) {
      e.preventDefault();
  }


  currentX = currentClientX;
  currentY = currentClientY;
  var dx = currentX - initialX;
  var dy = currentY - initialY;

  if (isResizing) {
    var newWidth = initialWidth;
    var newHeight = initialHeight;
    var newLeft = initialLeft;
    var newTop = initialTop;

    var minWidthPx = parseInt(widget.style.minWidth || "170");
    var minHeightPx = parseInt(widget.style.minHeight || "130");

    // Calculate potential new dimensions based on drag
    if (resizeEdge.right) newWidth = initialWidth + dx;
    if (resizeEdge.bottom) newHeight = initialHeight + dy;
    if (resizeEdge.left) {
        newWidth = initialWidth - dx;
        newLeft = initialLeft + dx; // Calculate potential newLeft
    }
    if (resizeEdge.top) {
        newHeight = initialHeight - dy;
        newTop = initialTop + dy; // Calculate potential newTop
    }

    // Ensure widget stays within screen bounds while resizing (Conditional based on allowOffscreen)
    if (!allowOffscreen) {
        // Check outer edges (right and bottom)
        var effectiveLeftForOuterCheck = resizeEdge.left ? newLeft : initialLeft;
        var effectiveTopForOuterCheck = resizeEdge.top ? newTop : initialTop;

        if (effectiveLeftForOuterCheck + newWidth > window.innerWidth) {
          newWidth = window.innerWidth - effectiveLeftForOuterCheck;
        }
        if (effectiveTopForOuterCheck + newHeight > window.innerHeight) {
          newHeight = window.innerHeight - effectiveTopForOuterCheck;
        }

        // Check inner edges (left and top) if resizing from that edge
        if (resizeEdge.left && newLeft < 0) {
            // newLeft is negative, so adding it to newWidth decreases width
            newWidth += newLeft;
            newLeft = 0; // Pin left edge to 0
        }
        if (resizeEdge.top && newTop < 0) {
            // newTop is negative, so adding it to newHeight decreases height
            newHeight += newTop;
            newTop = 0; // Pin top edge to 0
        }
    }

    // Apply constrained values - Only apply if >= minWidthPx/minHeightPx after boundary checks
    // This allows the boundary to override the min size initially, but the style won't be applied if it drops below min.
    // Following the provided changes logic exactly:
    if (newWidth >= minWidthPx) {
      widget.style.width = newWidth + "px";
      // Only apply left style if resizing left
      if (resizeEdge.left) widget.style.left = newLeft + "px";
    }
    if (newHeight >= minHeightPx) {
      widget.style.height = newHeight + "px";
      // Only apply top style if resizing top
      if (resizeEdge.top) widget.style.top = newTop + "px";
    }
  } else if (isDragging) {
    // Calculate new position
    var dragTop = initialTop + dy;
    var dragLeft = initialLeft + dx;

    // Keep widget fully within viewport (Conditional based on allowOffscreen)
    if (!allowOffscreen) { // Wrap boundary checks
        dragTop = Math.max(0, Math.min(dragTop, window.innerHeight - widget.offsetHeight));
        dragLeft = Math.max(0, Math.min(dragLeft, window.innerWidth - widget.offsetWidth));
    }

    widget.style.top = dragTop + "px";
    widget.style.left = dragLeft + "px";
    widget.style.right = "auto"; // Set these to auto when using top/left
    widget.style.bottom = "auto";
  }
}

// --- Mouse/Touch Up Handler (Drag or Resize End) ---
function handleMouseUp() {
  if (isDragging) {
    header.classList.remove("dragging"); // Remove dragging class
  }
  if (overlay)
    overlay.style.removeProperty('display');

  isDragging = false;
  isResizing = false;
  resizeEdge = { top: false, right: false, bottom: false, left: false }; // Reset edges
  iframe.style.pointerEvents = "auto"; // Re-enable iframe interaction

  // Remove listeners
  document.removeEventListener("mousemove", handleMouseMove);
  document.removeEventListener("mouseup", handleMouseUp);
  document.removeEventListener("touchmove", handleMouseMove);
  document.removeEventListener("touchend", handleMouseUp);

  // Reset cursor to default. The hover mousemove listener will correct it if needed.
  widget.style.cursor = 'default';
}

// Prevent text selection during drag/resize (already present, keep)
document.addEventListener("selectstart", function (e) {
  if (isDragging || isResizing) {
    e.preventDefault();
  }
});

// --- Touch Start Handler ---
widget.ontouchstart = function (e) {
  // Allow touch only if it's on header or padding area
  var frameContainer = document.getElementById("help-frame-container");
  var isHeaderTouch = e.target === header || header.contains(e.target);
  var isPaddingTouch =
    frameContainer && frameContainer.contains(e.target) && e.target !== iframe;

  if (e.touches.length === 1 && (isHeaderTouch || isPaddingTouch)) {
    var touch = e.touches[0];
    var mockEvent = {
      // Create a mouse-like event
      clientX: touch.clientX,
      clientY: touch.clientY,
      target: touch.target,
      // Don't prevent default here. Let handleMouseMove decide if dragging/resizing starts.
      preventDefault: function () { e.preventDefault(); }, // Pass through actual preventDefault
      touches: e.touches // Pass touches array for handleMouseMove
    };
    // Call the mousedown handler which contains the core logic for starting drag/resize
    widget.onmousedown(mockEvent);
    // If mousedown/handleMouseMove determines drag/resize is starting, preventDefault will be called there.
  }
  // If not a valid touch start for drag/resize, allow default behavior (e.g., scrolling)
};

// Touch move and end listeners are added dynamically in onmousedown
