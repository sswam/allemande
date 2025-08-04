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
  return new Promise((resolve, reject) => {
    if (img.complete) {
      // Even if complete, check if there was an error
      if (img.naturalWidth === 0 || img.naturalHeight === 0) {
        reject(new Error('Image failed to load'));
      } else {
        resolve();
      }
    } else {
      img.addEventListener('load', () => resolve());
      img.addEventListener('error', () => reject(new Error('Image failed to load')));
    }
  });
}

function image_text(img, texts, size = 1, font = "'Brush Script MT', 'Lucida Handwriting', 'TeX Gyre Chorus', cursive") {
  img.classList.add('layout');
  const current_script = document.currentScript;
  return image_text_async(img, texts, size, font, current_script);
}

async function image_text_async(img, texts = [], size = 1, font = "'Brush Script MT', 'Lucida Handwriting', 'TeX Gyre Chorus', cursive", ref = null) {
	await waitForMessage(ref);

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
    img.parentNode.insertBefore(wrapper, img);
    wrapper.appendChild(img);
  }

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

  // Ensure texts is an array
  texts = Array.isArray(texts) ? texts : [texts];

  // Calculate spacing
  for (const text of texts) {
    const textElement = createText(text);
    overlay.appendChild(textElement);
  }

  wrapper.appendChild(overlay);
}

// Example:
// image_text(previous("img"), ["flying", "cow"]);


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


// rain ----------------------------------------------------------------------

// Raindrop class
class Raindrop {
  constructor() {
    // A few shades of blue for variety
    this.blues = ['#a2d2ff', '#bde0fe', '#8ecae6', '#77b5d9', '#5fa8d3'];
    this.reset();
  }

  reset() {
    this.x = Math.random() * rain_canvas.width;
    this.y = -Math.random() * rain_canvas.height;
    this.length = Math.random() * 20 + 10;
    this.speed = Math.random() * 6 + 4; // A bit faster than snow
    this.width = Math.random() * 1.5 + 1;
    this.color = this.blues[Math.floor(Math.random() * this.blues.length)];
  }

  update() {
    this.y += this.speed;
    // Reset if it goes off the bottom of the screen
    if (this.y > rain_canvas.height) {
      this.reset();
    }
  }

  draw(ctx) {
    ctx.beginPath();
    ctx.moveTo(this.x, this.y);
    // The line is drawn "behind" the leading point (y)
    ctx.lineTo(this.x, this.y - this.length);
    ctx.strokeStyle = this.color;
    ctx.lineWidth = this.width;
    ctx.lineCap = 'round'; // Makes the drops look softer
    ctx.stroke();
  }
}

// Global variables for the rain effect
var rain_canvas;
var raindrops;

// Animation loop
function raining() {
  if (!rain_canvas) return;
  const ctx = rain_canvas.getContext('2d');
  ctx.clearRect(0, 0, rain_canvas.width, rain_canvas.height);

  raindrops.forEach(drop => {
    drop.update();
    drop.draw(ctx);
  });

  requestAnimationFrame(raining);
}

// Main function to set up and start the rain
function rain() {
  // Check for the user's motion preference, assuming the function exists globally
  if (typeof checkReducedMotionPreference === 'function' && checkReducedMotionPreference()) {
    console.log('Reduced motion preferred - rain effect disabled');
    return;
  }

  rain_canvas = document.createElement('canvas');
  rain_canvas.id = 'rainCanvas';
  rain_canvas.style.cssText = 'position: fixed; top: 0; left: 0; pointer-events: none; z-index: 9999;';

  const body = document.body;
  body.insertBefore(rain_canvas, body.firstChild);

  // Keep the canvas sized to the window
  function resizeCanvas() {
    rain_canvas.width = window.innerWidth;
    rain_canvas.height = window.innerHeight;
  }
  resizeCanvas();
  window.addEventListener('resize', resizeCanvas);

  // Create a nice dense array of raindrops
  raindrops = Array(300).fill().map(() => new Raindrop());
  raining();
}

// matrix WIP! ---------------------------------------------------------------

// Function to convert any color to rgba with opacity
function convertToRGBA(color, opacity) {
  // Create a temporary div to compute the color
  const temp = document.createElement('div');
  temp.style.color = color;
  document.body.appendChild(temp);

  // Get the computed color in rgb format
  const computedColor = window.getComputedStyle(temp).color;
  document.body.removeChild(temp);

  // Convert to rgba
  return computedColor.replace('rgb', 'rgba').replace(')', `, ${opacity})`);
}

function getRainbowColor() {
  // Get current time in milliseconds
  const now = Date.now();
  // Complete cycle every 180 seconds (6 colors × 30 seconds each)
  const hue = (now / 180000 * 360) % 360;

  return `hsla(${hue}, 100%, 50%, 0.25)`;
}

// Global variables for the Matrix effect
var matrix_canvas;
var matrix_ctx;
var matrix_bgcolor;

// An array to store the Y position of the last character in each column
var y_positions;

// The characters to be used in the rain
const katakana = 'アァカサタナハマヤャラワガザダバパイィキシチニヒミリヰギジヂビピウゥクスツヌフムユュルグズブヅプエェケセテネヘメレヱゲゼデベペオォコソトノホモヨョロヲゴゾドボポヴッン';
const latin = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ';
const nums = '0123456789';
const matrix_chars = katakana + latin + nums;

// A slower, more sparse Matrix effect

// (Global variables from before are reused: matrix_canvas, matrix_ctx, y_positions, matrix_chars)

const FONT_SIZE = 16; // Using a constant for clarity
const FALL_SPEED = 5; // The higher the number, the slower the fall. Updates every 5th frame.
const COLUMN_SPACING = 1; // Multiplier for spacing. 3 means columns are 3x font size apart.
const RESET_CHANCE = 0.99; // Chance a column will *not* reset. Higher = more empty space.

// A counter to regulate animation speed
let matrixFrameCount = 0;

// The revised animation loop
function matrixFallingSlow() {
  if (!matrix_canvas) return;

  matrixFrameCount++;
  // Only execute the main logic if the frame count is a multiple of FALL_SPEED
  if (matrixFrameCount % FALL_SPEED === 0) {
    // Fading effect

    matrix_ctx.fillStyle = matrix_bgcolor;

    matrix_ctx.fillRect(0, 0, matrix_canvas.width, matrix_canvas.height);

    // Then replace your original line with:
    matrix_ctx.fillStyle = getRainbowColor();

    matrix_ctx.font = FONT_SIZE + 'px monospace';

    // Loop over each column
    for (let i = 0; i < y_positions.length; i++) {
      const text = matrix_chars.charAt(Math.floor(Math.random() * matrix_chars.length));
      // The x position is now spaced out by the multiplier
      const x = i * FONT_SIZE * COLUMN_SPACING;
      const y = y_positions[i] * FONT_SIZE;

      matrix_ctx.fillText(text, x, y);

      if (y > matrix_canvas.height && Math.random() > RESET_CHANCE) {
        y_positions[i] = 0;
      }
      y_positions[i]++;
    }
  }

  requestAnimationFrame(matrixFallingSlow);
}


// Main function to set up and start the effect
function matrix() {
  if (typeof checkReducedMotionPreference === 'function' && checkReducedMotionPreference()) {
    console.log('Reduced motion preferred - matrix effect disabled');
    return;
  }

  matrix_canvas = document.createElement('canvas');
  matrix_canvas.id = 'matrixCanvas';
  matrix_canvas.style.cssText = 'position: fixed; top: 0; left: 0; pointer-events: none; z-index: -1;';
  document.body.insertBefore(matrix_canvas, document.body.firstChild);
  matrix_ctx = matrix_canvas.getContext('2d');

  // Get the computed background color
  const bgColor = getComputedStyle(document.documentElement)
          .getPropertyValue('--background');

  matrix_bgcolor = convertToRGBA(bgColor, 0.1);

  function resizeCanvas() {
    matrix_canvas.width = window.innerWidth;
    matrix_canvas.height = window.innerHeight;
    // Calculate columns based on the new spacing
    const columns = Math.floor(matrix_canvas.width / (FONT_SIZE * COLUMN_SPACING));
    y_positions = Array(columns).fill(1);
  }

  resizeCanvas();
  window.addEventListener('resize', resizeCanvas);

  // Reset the frame counter and start the new animation loop
  matrixFrameCount = 0;
  matrixFallingSlow();
}


// bouncing messages ---------------------------------------------------------

function bounceMessage(selector = '.m1') {
  const current_script = document.currentScript;
  bounceMessage_async(selector, current_script)
}

async function bounceMessage_async(selector, ref) {
  await waitForMessage(ref);
  const msg = document.querySelector(selector);
  console.log(msg);

  const rect = msg.getBoundingClientRect();
  let x = Math.max(rect.left, 0);
  let y = Math.max(rect.top, 0);
  let dx = 0.3;
  let dy = 0.2;

  msg.classList.add('bouncing-message');

  const animate = () => {
    x += dx;
    y += dy;

    if (x + msg.offsetWidth > window.innerWidth) {
      x = window.innerWidth - msg.offsetWidth;
      dx *= -1;
    } else if (x < 0) {
      x = 0;
      dx *= -1;
    }

    if (y + msg.offsetHeight > window.innerHeight) {
      y = window.innerHeight - msg.offsetHeight;
      dy *= -1;
    } else if (y < 0) {
      y = 0;
      dy *= -1;
    }

    msg.style.left = x + 'px';
    msg.style.top = y + 'px';

    msg.animationId = requestAnimationFrame(animate);
  };

  msg.onclick = () => {
    cancelAnimationFrame(msg.animationId);
    msg.classList.remove('bouncing-message');

    // Reset styles
    msg.style.left = '';
    msg.style.top = '';
    msg.onclick = null;
  };

  animate();
}
