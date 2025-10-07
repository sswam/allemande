"use strict";
var widget = document.getElementById("help-widget");
var header = document.getElementById("help-widget-header");
var iframe = document.getElementById("help-frame");
var overlay = document.getElementById("messages_overlay");

// Config
var allowOffscreen = false; // Whether widget can partially move offscreen
const DRAG_THRESHOLD = 5; // pixels to move before drag starts

// Track widget state
var isDragging = false;
var isResizing = false;
var isDragPending = false;
var capturedPointerId = null;
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
  // Don't show resize cursor for touch
  if (e.pointerType === "touch") return;

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
widget.addEventListener("pointermove", updateCursor);
widget.addEventListener("pointerleave", function(e) {
    if (!isDragging && !isResizing) {
        // Only reset cursor for mouse, not for touch/pen leaving the area
        if (e.pointerType === "mouse") {
            widget.style.cursor = 'default';
            header.style.cursor = 'move';
        }
    }
});


// --- Unified Pointer Handlers for Drag and Resize ---

function handlePointerDown(e) {
  // For mouse, only respond to left-click. For touch/pen, e.button is 0.
  if (e.pointerType === 'mouse' && e.button !== 0) return;

  // Do nothing if the click is on the close button or inside the iframe content area
  if (
    e.target.closest("button") || e.target.closest("a") ||
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
  var cornerThreshold = pad * 1.5; // slightly larger threshold for corners

  // Detect resize based on padding click
  if (isWithinHorizontalPadding || isWithinVerticalPadding) {
    isResizing = true;
    // Determine specific edge - prioritize corners
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
      isResizing = false; // Click was in padding area but not close enough to an edge?
    }
  }

  // Reset drag states
  isDragging = false;
  isDragPending = false;

  // Detect potential drag (only if not resizing and click is on header)
  var isClickOnHeader = (e.target === header || header.contains(e.target));
  var isClickNearTopEdge = e.clientY > rect.top && e.clientY < rect.top + cornerThreshold; // Use the same threshold as resize detection

  if (!isResizing && isClickOnHeader && !isClickNearTopEdge) {
    isDragPending = true;
  }

  if (isResizing || isDragPending) {
    capturedPointerId = e.pointerId; // Store for potential capture.

    // For resize, start immediately. This prevents clicks on edges.
    if (isResizing) {
        e.preventDefault(); // Prevent text selection, etc.
        iframe.style.pointerEvents = "none"; // Prevent iframe from capturing events
        if (overlay) {
            overlay.style.display = 'block';
        }

        // Set cursor specifically for resizing
        var edgeKey = [];
        if (resizeEdge.top) edgeKey.push('top');
        if (resizeEdge.bottom) edgeKey.push('bottom');
        if (resizeEdge.left) edgeKey.push('left');
        if (resizeEdge.right) edgeKey.push('right');
        widget.style.cursor = cursorMap[edgeKey.join(',')] || 'default';

        // Capture the pointer for resizing
        widget.setPointerCapture(capturedPointerId);
    }

    // Add listeners for both resize and potential drag
    document.addEventListener("pointermove", handlePointerMove);
    document.addEventListener("pointerup", handlePointerUp);
    document.addEventListener("pointercancel", handlePointerUp); // Also end on cancel
  }
}

function handlePointerMove(e) {
  if (isDragPending) {
    const dx = e.clientX - initialX;
    const dy = e.clientY - initialY;
    if (Math.abs(dx) > DRAG_THRESHOLD || Math.abs(dy) > DRAG_THRESHOLD) {
      // Threshold passed, start a real drag.
      isDragPending = false;
      isDragging = true;

      // Apply dragging styles and capture the pointer now.
      header.classList.add("dragging");
      widget.style.cursor = 'grabbing';
      iframe.style.pointerEvents = "none";
      if (overlay) {
        overlay.style.display = 'block';
      }
      widget.setPointerCapture(capturedPointerId);
    } else {
      // Not yet a drag, do nothing.
      return;
    }
  }
  // We check isDragging/isResizing again because a pointermove can be fired between
  // pointerdown and the logic that sets these flags.
  if (!isDragging && !isResizing) return;

  e.preventDefault(); // Prevents scrolling on touch, text selection on mouse

  currentX = e.clientX;
  currentY = e.clientY;
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
        newLeft = initialLeft + dx;
    }
    if (resizeEdge.top) {
        newHeight = initialHeight - dy;
        newTop = initialTop + dy;
    }

    // Ensure widget stays within screen bounds while resizing
    if (!allowOffscreen) {
        var effectiveLeftForOuterCheck = resizeEdge.left ? newLeft : initialLeft;
        var effectiveTopForOuterCheck = resizeEdge.top ? newTop : initialTop;

        if (effectiveLeftForOuterCheck + newWidth > window.innerWidth) {
          newWidth = window.innerWidth - effectiveLeftForOuterCheck;
        }
        if (effectiveTopForOuterCheck + newHeight > window.innerHeight) {
          newHeight = window.innerHeight - effectiveTopForOuterCheck;
        }

        if (resizeEdge.left && newLeft < 0) {
            newWidth += newLeft;
            newLeft = 0;
        }
        if (resizeEdge.top && newTop < 0) {
            newHeight += newTop;
            newTop = 0;
        }
    }

    // Apply constrained values - Only apply if >= minWidthPx/minHeightPx after boundary checks
    if (newWidth >= minWidthPx) {
      widget.style.width = newWidth + "px";
      if (resizeEdge.left) widget.style.left = newLeft + "px";
    }
    if (newHeight >= minHeightPx) {
      widget.style.height = newHeight + "px";
      if (resizeEdge.top) widget.style.top = newTop + "px";
    }
  } else if (isDragging) {
    var dragTop = initialTop + dy;
    var dragLeft = initialLeft + dx;

    if (!allowOffscreen) {
        dragTop = Math.max(0, Math.min(dragTop, window.innerHeight - widget.offsetHeight));
        dragLeft = Math.max(0, Math.min(dragLeft, window.innerWidth - widget.offsetWidth));
    }

    widget.style.top = dragTop + "px";
    widget.style.left = dragLeft + "px";
    widget.style.right = "auto";
    widget.style.bottom = "auto";
  }
}

function handlePointerUp(e) {
  if (isDragging) {
    header.classList.remove("dragging");
  }
  if (overlay) {
    overlay.style.removeProperty('display');
  }

  isDragPending = false;
  isDragging = false;
  isResizing = false;
  resizeEdge = { top: false, right: false, bottom: false, left: false };
  iframe.style.pointerEvents = "auto";

  // Release pointer capture and remove listeners
  if (capturedPointerId !== null) {
      if (widget.hasPointerCapture(capturedPointerId)) {
          widget.releasePointerCapture(capturedPointerId);
      }
      capturedPointerId = null;
  }
  document.removeEventListener("pointermove", handlePointerMove);
  document.removeEventListener("pointerup", handlePointerUp);
  document.removeEventListener("pointercancel", handlePointerUp);

  // Reset cursors. The hover listener will correct it if needed.
  widget.style.cursor = 'default';
  header.style.cursor = 'move';
}

// Attach the main pointer down listener
widget.addEventListener("pointerdown", handlePointerDown);

// Prevent text selection during drag/resize
document.addEventListener("selectstart", function (e) {
  if (isDragging || isResizing) {
    e.preventDefault();
  }
});
