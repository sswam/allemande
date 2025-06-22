function getForegroundColorWithOpacity(opacity) {
  return hexColorWithOpacity(getCssVarColorHex('--text'), opacity);
}

function getCssVarColorHex(varName = '--text') {
  const temp = document.createElement('div');
  temp.style.color = getComputedStyle(document.body).getPropertyValue(varName);
  document.body.appendChild(temp);
  const rgb = getComputedStyle(temp).color;
  document.body.removeChild(temp);
  const match = rgb.match(/^rgb\((\d+),\s*(\d+),\s*(\d+)\)$/);
  if (!match) return '#808080';
  const hex = '#' + match.slice(1).map(x =>
    parseInt(x).toString(16).padStart(2, '0')
  ).join('');
  return hex;
}

function hexColorWithOpacity(color, opacity) {
    const alpha = Math.round(opacity * 255);
    return color + alpha.toString(16).padStart(2, '0');
}

function previous(selector, lookBack = 0, ref = document.currentScript) {
	// Get all elements matching the selector
	const elements = Array.from(document.querySelectorAll(selector));

	// Find elements before the script
	const beforeScript = elements.filter(element =>
		!(ref.compareDocumentPosition(element) & Node.DOCUMENT_POSITION_FOLLOWING)
	);

	// If no elements found before script, return null
	if (!beforeScript.length) return null;

	// Get the element at the specified lookBack position from the end
	const index = beforeScript.length - 1 - lookBack;
	return index >= 0 ? beforeScript[index] : null;
}

function rem_to_px(n) {
    return n * parseFloat(getComputedStyle(document.documentElement).fontSize);
}

async function waitForImageLoad(img) {
  // Return a promise that resolves when the image is loaded or rejects on error
  return new Promise((resolve, reject) => {
    if (img.complete) {
      if (img.naturalWidth === 0) {
        reject(new Error('Image failed to load'));
      } else {
        resolve(img);
      }
      return;
    }
    img.addEventListener('load', () => resolve(img));
    img.addEventListener('error', () => {
      reject(new Error('Image failed to load'));
    });
  });
}

// Example usage:
async function loadImage(src) {
  try {
    const img = new Image();
    img.src = src;
    await waitForImageLoad(img);
    console.log('Image loaded successfully');
    return img;
  } catch (error) {
    console.error('Error loading image:', error.message);
    throw error; // Re-throw if you want calling code to handle the error
  }
}

// Using the function
loadImage('https://example.com/image.jpg')
  .then(img => {
    // Use the loaded image
    document.body.appendChild(img);
  })
  .catch(error => {
    // Handle error (e.g., show fallback image)
    console.error('Failed to load image:', error);
  });
```

Key improvements in this version:

1. **Error Handling**: Added an 'error' event listener to catch loading failures.

2. **Complete Check**: When checking `img.complete`, also verifies `naturalWidth` to detect failed loads.

3. **Promise Rejection**: Properly rejects the promise when errors occur.

4. **Event Cleanup**: The event listeners will be automatically cleaned up once either resolved or rejected.

5. **Returns Image**: Resolves with the image object for convenience.

6. **Example Usage**: Includes a practical example showing how to use the function with proper error handling.

Additional considerations you might want to add:

```javascript
async function waitForImageLoad(img, timeout = 5000) {
  return new Promise((resolve, reject) => {
    // Timeout handler
    const timeoutId = setTimeout(() => {
      reject(new Error('Image load timed out'));
    }, timeout);

    if (img.complete) {
      clearTimeout(timeoutId);
      if (img.naturalWidth === 0) {
        reject(new Error('Image failed to load'));
      } else {
        resolve(img);
      }
      return;
    }

    const handleSuccess = () => {
      clearTimeout(timeoutId);
      cleanup();
      resolve(img);
    };

    const handleError = () => {
      clearTimeout(timeoutId);
      cleanup();
      reject(new Error('Image failed to load'));
    };

    const cleanup = () => {
      img.removeEventListener('load', handleSuccess);
      img.removeEventListener('error', handleError);
    };

    img.addEventListener('load', handleSuccess);
    img.addEventListener('error', handleError);
  });
}
```

This enhanced version includes:

1. **Timeout**: Adds a timeout option to prevent infinite waiting.

2. **Event Cleanup**: Properly removes event listeners after resolution/rejection.

3. **Memory Management**: Better handles cleanup to prevent memory leaks.

Usage with all features:

```javascript
async function loadImageWithTimeout(src, timeout = 5000) {
  try {
    const img = new Image();
    img.src = src;
    await waitForImageLoad(img, timeout);
    return img;
  } catch (error) {
    if (error.message === 'Image load timed out') {
      // Handle timeout specifically
      console.error('Image load timed out');
    } else {
      // Handle other loading errors
      console.error('Image failed to load');
    }
    throw error;
  }
}
```

This implementation provides a robust way to handle image loading with proper error handling, timeouts, and cleanup.

function image_text(img, text1, text2, size = 1, font = "'Brush Script MT', 'Lucida Handwriting', 'TeX Gyre Chorus', cursive") {
  const current_script = document.currentScript;
  return image_text_async(img, text1, text2, size, font, current_script);
}

async function image_text_async(img, text1, text2, size = 1, font = "'Brush Script MT', 'Lucida Handwriting', 'TeX Gyre Chorus', cursive", ref = null) {
  const process_messages = await $import("chat:process_messages");
  const message = ref.closest('div.message');
  await process_messages.processMessage(message);

  if (!img)
    throw new Error("image_text: img is null or undefined");

  await waitForImageLoad(img);

  let wrapper;

  // Check if img already has a div parent
  if (img.parentElement && img.parentElement.tagName === 'DIV') {
    wrapper = img.parentElement;
  } else {
    // Create new wrapper div if needed
    wrapper = document.createElement('div');
    // Wrap the image
    img.parentNode.insertBefore(wrapper, img);
    wrapper.appendChild(img);
  }

  // Set styles regardless of whether it's new or existing
  wrapper.style.position = 'relative';
  wrapper.style.display = 'inline-block';

  // Create overlay
  const overlay = document.createElement('div');
  overlay.style.cssText = `
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    align-items: center;
    pointer-events: none;
    padding: 20px;
    box-sizing: border-box;
  `;

  const sizePercent = 8 * size;

  // Helper to create text element
  function createText(content) {
    if (!content) return null;

    const text = document.createElement('div');
    text.textContent = content;
    text.style.cssText = `
      font-family: ${font};
      font-size: ${sizePercent}cqmin;
      color: white;
      text-shadow:
        -2px -2px 4px rgba(0,0,0,0.8),
        2px -2px 4px rgba(0,0,0,0.8),
        -2px 2px 4px rgba(0,0,0,0.8),
        2px 2px 4px rgba(0,0,0,0.8),
        0 0 10px rgba(0,0,0,0.9);
      font-weight: bold;
      text-align: center;
    `;
    return text;
  }

  // Add top text
  const topText = createText(text1);
  if (topText) overlay.appendChild(topText);
  else overlay.appendChild(document.createElement('div')); // spacer

  // Add bottom text
  const bottomText = createText(text2);
  if (bottomText) overlay.appendChild(bottomText);

  wrapper.appendChild(overlay);
}

// Example:
// image_text(previous("img"), "flying", "cow");


// snowing ------------------------------------------------------------------

// Snowflake class
class Snowflake {
  constructor() {
    this.reset();
  }

  reset() {
    this.x = Math.random() * snow_canvas.width;
    this.y = -Math.random() * snow_canvas.height;
    this.size = Math.random() * 3 + 1;
    this.speed = Math.random() * 1 + 0.5;
    this.drift = Math.random() * 0.5 - 0.25;
  }

  update() {
    this.y += this.speed;
    this.x += this.drift;

    if (this.y > snow_canvas.height) {
      this.reset();
    }
  }

  draw(ctx) {
    ctx.beginPath();
    ctx.arc(this.x, this.y, this.size, 0, Math.PI * 2);
    ctx.fillStyle = 'rgba(255, 255, 255, 0.8)';
    ctx.fill();
  }
}

var snow_canvas;

function snowing() {
  const ctx = snow_canvas.getContext('2d');
  ctx.clearRect(0, 0, snow_canvas.width, snow_canvas.height);

  snowflakes.forEach(flake => {
    flake.update();
    flake.draw(ctx);
  });

  requestAnimationFrame(snowing);
}

function snow() {
  snow_canvas = document.createElement('canvas');
  snow_canvas.id = 'snowCanvas';
  snow_canvas.style.cssText = 'position: fixed; top: 0; left: 0; pointer-events: none; z-index: 9999;';

  const body = document.body;
  body.insertBefore(snow_canvas, body.firstChild);

  snow_canvas = document.getElementById('snowCanvas');

  // Set canvas size to window size
  function resizeCanvas() {
    snow_canvas.width = window.innerWidth;
    snow_canvas.height = window.innerHeight;
  }
  resizeCanvas();
  window.addEventListener('resize', resizeCanvas);

  snowflakes = Array(100).fill().map(() => new Snowflake());
  snowing();
}
