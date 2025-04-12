// Generic drag resize handler class
class DragResizer {
  constructor(options = {}) {
    this.element = options.element;
    this.direction = options.direction || 'down';
    this.overlay = options.overlay;
    this.minSize = options.minSize || 0;
    this.maxSize = options.maxSize || Infinity;
    this.property = options.property || 'flexBasis';
    this.notify = options.notify || (() => {});

    // Bound methods
    this.doDrag = this.doDrag.bind(this);
    this.stopDrag = this.stopDrag.bind(this);

    // Initial values
    this.startPos = { x: 0, y: 0 };
    this.startSize = { width: 0, height: 0 };

    this.newSize = 0;
  }

  initDrag(e) {
    e.preventDefault();

    // Store initial positions
    this.startPos.x = e.clientX || (e.touches && e.touches[0].clientX);
    this.startPos.y = e.clientY || (e.touches && e.touches[0].clientY);
    this.startSize.width = this.element.offsetWidth;
    this.startSize.height = this.element.offsetHeight;

    // Add event listeners
    document.addEventListener('mousemove', this.doDrag);
    document.addEventListener('mouseup', this.stopDrag);
    document.addEventListener('touchmove', this.doDrag);
    document.addEventListener('touchend', this.stopDrag);

    // Show overlay if provided
    if (this.overlay) {
      this.overlay.style.display = 'block';
    }

    this.newSize = null;
  }

  doDrag(e) {
    // e.preventDefault();

    const currentX = e.clientX || (e.touches && e.touches[0].clientX);
    const currentY = e.clientY || (e.touches && e.touches[0].clientY);

    let newSize;
    if (this.direction === 'up') {
      newSize = this.startSize.height + this.startPos.y - currentY;
    } else if (this.direction === 'down') {
      newSize = this.startSize.height + currentY - this.startPos.y;
    } else if (this.direction === 'left') {
      newSize = this.startSize.width + this.startPos.x - currentX;
    } else if (this.direction === 'right') {
      newSize = this.startSize.width + currentX - this.startPos.x;
    } else {
      throw new Error('Invalid direction');
    }

    // Apply min/max constraints
    this.newSize = Math.max(this.minSize, Math.min(this.maxSize, newSize));

    this.element.style[this.property] = this.newSize + 'px';
  }

  stopDrag(e) {
    e.preventDefault();

    // Remove event listeners
    document.removeEventListener('mousemove', this.doDrag);
    document.removeEventListener('mouseup', this.stopDrag);
    document.removeEventListener('touchmove', this.doDrag);
    document.removeEventListener('touchend', this.stopDrag);

    // Hide overlay if provided
    if (this.overlay) {
      this.overlay.style.removeProperty('display');
    }

    // Notify changed size
    this.notify(this.newSize);
  }
}
