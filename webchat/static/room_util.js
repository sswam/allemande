function checkReducedMotionPreference() {
	// Check if the browser supports matchMedia
	if (!window.matchMedia) {
		return false;
	}

	// Check for the prefers-reduced-motion media query
	const mediaQuery = window.matchMedia('(prefers-reduced-motion: reduce)');

  /*
	// Function to handle preference changes
	const handlePreferenceChange = (e) => {
		const shouldReduceMotion = e.matches;
		return shouldReduceMotion;
	};

	// Add listener for preference changes
	mediaQuery.addEventListener('change', handlePreferenceChange);
  */

	// Return current preference
	return mediaQuery.matches;
}

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
  // Return a promise that resolves when the image is loaded
  return new Promise((resolve) => {
    if (img.complete) {
      resolve();
    } else {
      img.addEventListener('load', () => resolve());
    }
  });
}

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
    container-type: inline-size;
  `;

  const sizePercent = 12.5 * size;

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
	if (checkReducedMotionPreference()) {
		console.log('Reduced motion preferred - snow effect disabled');
		return;
	}

  snow_canvas = document.createElement('canvas');
  snow_canvas.id = 'snowCanvas';
  snow_canvas.style.cssText = 'position: fixed; top: 0; left: 0; pointer-events: none; z-index: 9999;';

  const body = document.body;
  body.insertBefore(snow_canvas, body.firstChild);

  // Set canvas size to window size
  function resizeCanvas() {
    snow_canvas.width = window.innerWidth;
    snow_canvas.height = window.innerHeight;
  }
  resizeCanvas();
  window.addEventListener('resize', resizeCanvas);

  snowflakes = Array(50).fill().map(() => new Snowflake());
  snowing();
}
