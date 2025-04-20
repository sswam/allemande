var widget = document.getElementById("help-widget");
var header = document.getElementById("help-widget-header");
var closeButton = document.getElementById("help-widget-close");
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

// --- Close Button ---
if (closeButton) {
  // Use mousedown to prevent drag start when clicking close button
  closeButton.onmousedown = function (e) {
    if (e.button !== 0) return;
    e.stopPropagation(); // Prevent triggering widget's mousedown
    widget.classList.add("hidden")
  };
}

// --- Mouse Down Handler (Drag or Resize Start) ---
widget.onmousedown = function (e) {
  if (e.button !== 0) return;
  // Do nothing if the click is on the close button or inside the iframe content area (already handled)
  if (
    e.target === closeButton ||
    closeButton.contains(e.target) ||
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
  // Actually, top resize shouldn't happen easily because of header. Let's only allow L/R/B and corners.
  onTopEdge = false; // Disable top edge resize for simplicity

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
    onTopEdge = false; // Reiterate: disable top edge

    if (onBottomEdge && onLeftEdge) {
      resizeEdge = { bottom: true, left: true };
    } else if (onBottomEdge && onRightEdge) {
      resizeEdge = { bottom: true, right: true };
    }
    // Add top corners if top resize was enabled
    // else if (onTopEdge && onLeftEdge) { resizeEdge = { top: true, left: true }; }
    // else if (onTopEdge && onRightEdge) { resizeEdge = { top: true, right: true }; }
    // Edges
    else if (onLeftEdge) {
      resizeEdge = { left: true };
    } else if (onRightEdge) {
      resizeEdge = { right: true };
    }
    // else if (onTopEdge) { resizeEdge = { top: true }; } // Disabled
    else if (onBottomEdge) {
      resizeEdge = { bottom: true };
    } else {
      isResizing = false;
    } // Click in padding but not near edge/corner? Should be rare.
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
      console.log("showing overlay");
      overlay.style.display = 'block';
    }
  }
};

// --- Mouse/Touch Move Handler (Dragging or Resizing) ---
function handleMouseMove(e) {
  // Determine current coords from mouse or touch event
  var currentClientX = e.clientX ?? e.touches?.[0]?.clientX;
  var currentClientY = e.clientY ?? e.touches?.[0]?.clientY;

  if (currentClientX === undefined || currentClientY === undefined) return; // No coords

  // Use preventDefault for touchmove to stop scrolling
  if (e.touches) e.preventDefault();

  currentX = currentClientX;
  currentY = currentClientY;
  var dx = currentX - initialX;
  var dy = currentY - initialY;

  if (isResizing) {
    var newWidth = initialWidth;
    var newHeight = initialHeight;
    var newTop = initialTop;
    var newLeft = initialLeft;

    var minWidthPx = parseInt(widget.style.minWidth || "170"); // Use parsed minWidth
    var minHeightPx = parseInt(widget.style.minHeight || "130"); // Use parsed minHeight

    if (resizeEdge.right) {
      newWidth = initialWidth + dx;
    }
    if (resizeEdge.bottom) {
      newHeight = initialHeight + dy;
    }
    if (resizeEdge.left) {
      newWidth = initialWidth - dx;
      if (newWidth >= minWidthPx) {
        newLeft = initialLeft + dx;
      } else {
        newWidth = minWidthPx; // prevent shrinking past min
      }
    }
    // if (resizeEdge.top) { // Top resizing disabled
    //     newHeight = initialHeight - dy;
    //      if (newHeight >= minHeightPx) {
    //        newTop = initialTop + dy;
    //     } else {
    //        newHeight = minHeightPx;
    //     }
    // }

    // Apply constraints
    if (newWidth >= minWidthPx) {
      widget.style.width = newWidth + "px";
      if (resizeEdge.left) widget.style.left = newLeft + "px";
    }
    if (newHeight >= minHeightPx) {
      widget.style.height = newHeight + "px";
      // if (resizeEdge.top) widget.style.top = newTop + 'px'; // Disabled
    }
  } else if (isDragging) {
    var newTop = initialTop + dy;
    var newLeft = initialLeft + dx;

    // Viewport constraints
    var maxTop = window.innerHeight - widget.offsetHeight; // Simpler bottom constraint for now
    var maxLeft = window.innerWidth - minVisible; // Keep minVisible visible on the right
    var minLeft = -(widget.offsetWidth - minVisible); // Keep minVisible visible on the left
    var minTop = 0; // Don't allow title bar off the top

    // Apply constraints
    widget.style.top =
      Math.max(minTop, Math.min(newTop, window.innerHeight - minVisible)) +
      "px"; // Prevent bottom going off too much
    widget.style.left = Math.max(minLeft, Math.min(newLeft, maxLeft)) + "px";

    // Ensure explicit L/T are set, remove R/B if they exist from initial CSS
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
    };
    widget.onmousedown(mockEvent); // Trigger the mouse down logic
    // preventDefault is called in handleMouseMove if dragging/resizing starts
  }
  // Don't prevent default here, allow potential scrolling if not dragging/resizing
};

// Touch move and end listeners are added dynamically in onmousedown
