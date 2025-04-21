var widget = document.getElementById("help-widget");
var header = document.getElementById("help-widget-header");
var iframe = document.getElementById("help-frame");
var overlay = document.getElementById("messages_overlay");

var isDragging = false;
var isResizing = false;
var currentX, currentY, initialX, initialY;
var initialWidth, initialHeight, initialTop, initialLeft;
var resizeEdge = { top: false, right: false, bottom: false, left: false };

// --- Get CSS Variables ---
var computedStyle = getComputedStyle(widget);
var pad = parseInt(computedStyle.getPropertyValue("--pad")) || 10; // Get padding value
var borderThreshold = pad; // Use padding size as resize threshold
var minVisible =
  parseInt(computedStyle.getPropertyValue("--ui-size-min")) || 30; // Min visible size

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

  // Adjust threshold checks to account for padding
  var onLeftEdge = Math.abs(e.clientX - rect.left) < borderThreshold;
  var onRightEdge = Math.abs(e.clientX - rect.right) < borderThreshold;
  var onTopEdge =
    e.clientY > rect.top + header.offsetHeight &&
    Math.abs(e.clientY - rect.top) < borderThreshold + header.offsetHeight; // Check below header

  // More precise check: Ensure click is *outside* the inner content area
  var onBottomEdge = Math.abs(e.clientY - rect.bottom) < borderThreshold;

  // Simplify resize detection - check if click is within the padding area

  var isWithinHorizontalPadding =
    (e.clientX > rect.left && e.clientX < rect.left + pad) ||
    (e.clientX < rect.right && e.clientX > rect.right - pad);
  var isWithinVerticalPadding =
    (e.clientY > rect.top + header.offsetHeight &&
      e.clientY < rect.top + header.offsetHeight + pad) ||
    (e.clientY < rect.bottom && e.clientY > rect.bottom - pad); // Below header

  // Reset edges
  isResizing = false;
  resizeEdge = { top: false, right: false, bottom: false, left: false };

  // Detect resize based on padding click

  if (isWithinHorizontalPadding || isWithinVerticalPadding) {
    isResizing = true;
    // Determine specific edge - prioritize corners
    var cornerThreshold = pad * 1.5; // slightly larger threshold for corners
    onLeftEdge =
      e.clientX > rect.left && e.clientX < rect.left + cornerThreshold;
    onRightEdge =
      e.clientX < rect.right && e.clientX > rect.right - cornerThreshold;
    onBottomEdge =
      e.clientY < rect.bottom && e.clientY > rect.bottom - cornerThreshold;
    // Top resize is still tricky due to header, let's focus on L/R/B and corners involving them
    onTopEdge =
      e.clientY > rect.top + header.offsetHeight && e.clientY < rect.top + cornerThreshold;

    if (onBottomEdge && onLeftEdge) {
      resizeEdge = { bottom: true, left: true };
    } else if (onBottomEdge && onRightEdge) {
      resizeEdge = { bottom: true, right: true };
    }
    // Add top corners if top resize was enabled
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
      isResizing = false;
    }
  }

  // Detect drag (only if not resizing and click is on header)

  if (!isResizing && (e.target === header || header.contains(e.target))) {
    isDragging = true;
    header.classList.add("dragging"); // Add class for CSS styling
  } else {
    isDragging = false;
    if (overlay)
      overlay.style.removeProperty('display');
  }

  if (isDragging || isResizing) {
    iframe.style.pointerEvents = "none"; // Prevent iframe from capturing mouse events
    document.addEventListener("mousemove", handleMouseMove);
    document.addEventListener("mouseup", handleMouseUp);
    document.addEventListener("touchmove", handleMouseMove, { passive: false }); // Use same handler
    document.addEventListener("touchend", handleMouseUp);
    if (overlay) {
      overlay.style.display = 'block';
    }
  }
};

// --- Mouse/Touch Move Handler (Dragging or Resizing) ---
function handleMouseMove(e) {
  // Determine current coords from mouse or touch event
  var currentClientX = e.clientX ?? e.touches?.[0]?.clientX;
  var currentClientY = e.clientY ?? e.touches?.[0]?.clientY;

  if (currentClientX === undefined || currentClientY === undefined) return;

  // Use preventDefault for touchmove to stop scrolling
  if (e.touches) e.preventDefault();

  currentX = currentClientX;
  currentY = currentClientY;
  var dx = currentX - initialX;
  var dy = currentY - initialY;

  if (isResizing) {
    var newWidth = initialWidth;
    var newHeight = initialHeight;
    var newLeft = initialLeft; // Only used for left resize

    var minWidthPx = parseInt(widget.style.minWidth || "170");
    var minHeightPx = parseInt(widget.style.minHeight || "130");

    // Calculate potential new dimensions
    if (resizeEdge.right) newWidth = initialWidth + dx;
    if (resizeEdge.bottom) newHeight = initialHeight + dy;
    if (resizeEdge.left) {
      newWidth = initialWidth - dx;
      if (newWidth >= minWidthPx) { // Check min width for LEFT resize
        newLeft = initialLeft + dx;
      } else { // If goes below min width
        newWidth = minWidthPx;
        // Left edge position is fixed relative to right edge (initialLeft + initialWidth)
        newLeft = initialLeft + initialWidth - minWidthPx;
      }
    }
    // Note: Top resize is disabled, so no newTop calculation here

    // Ensure widget stays within screen bounds while resizing
    // effectiveLeft is newLeft if resizing left, otherwise initialLeft
    var effectiveLeft = resizeEdge.left ? newLeft : initialLeft;
    if (effectiveLeft + newWidth > window.innerWidth) {
      // This caps width based on the current effectiveLeft position.
      // If resizing left and hitting the right boundary, the right edge is window.innerWidth.
      // The new width is window.innerWidth - effectiveLeft.
      newWidth = window.innerWidth - effectiveLeft;
    }
    // effectiveTop is initialTop as top resize is disabled
    var effectiveTop = initialTop;
    if (effectiveTop + newHeight > window.innerHeight) {
      newHeight = window.innerHeight - effectiveTop;
    }

    // Apply constrained values - Only apply if >= minWidthPx/minHeightPx after boundary checks
    // This allows the boundary to override the min size initially, but the style won't be applied if it drops below min.
    // A more robust implementation would re-clamp by min after boundary check.
    // But following the provided changes logic exactly:
    if (newWidth >= minWidthPx) {
      widget.style.width = newWidth + "px";
      // Only apply left style if resizing left (and it was calculated)
      if (resizeEdge.left) widget.style.left = newLeft + "px";
    }
    if (newHeight >= minHeightPx) {
      widget.style.height = newHeight + "px";
    }
  } else if (isDragging) {
    // Calculate new position (using dragTop/dragLeft to avoid redeclaration confusion)
    var dragTop = initialTop + dy;
    var dragLeft = initialLeft + dx;

    // Keep widget fully within viewport
    dragTop = Math.max(0, Math.min(dragTop, window.innerHeight - widget.offsetHeight));
    dragLeft = Math.max(0, Math.min(dragLeft, window.innerWidth - widget.offsetWidth));

    widget.style.top = dragTop + "px";
    widget.style.left = dragLeft + "px";
    widget.style.right = "auto";
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
      preventDefault: function () {
        /* Don't call e.preventDefault here yet */
      },
      touches: e.touches // Pass touches array for handleMouseMove
    };
    widget.onmousedown(mockEvent); // Trigger the mouse down logic
    // preventDefault is called in handleMouseMove if dragging/resizing starts
  }
  // Don't prevent default here, allow potential scrolling if not dragging/resizing
};

// Touch move and end listeners are added dynamically in onmousedown
