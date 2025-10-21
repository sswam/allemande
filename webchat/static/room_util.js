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

function previous(selector, lookBack = 0, ref = document.currentScript||script) {
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
	if (img.dataset.src) {
		img.src = img.dataset.src;
		img.removeAttribute('data-src');
	}
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

function image_text(texts, options = {}) {
	const img = options.el || previous('img');
	img.classList.add('layout');
	const current_script = document.currentScript||script;
	return image_text_async(img, texts, options, current_script);
}

// Helper to create text element
function image_text_create_text(content, font, sizePercent) {
	if (!Array.isArray(content))
		content = [content];

	const container = document.createElement('div');
	container.style.cssText = `
		display: flex;
		justify-content: ${content.length === 1 ? 'center' : 'space-between'};
		width: 100%;
	`;

	for (const text of content) {
		const textElement = document.createElement('div');
		textElement.textContent = text;
		textElement.style.cssText = `
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
		container.appendChild(textElement);
	}

	return content.length == 1 ? container.firstChild : container;
}

async function image_text_async(img, texts = [], options = {}, script = null) {
	await waitForMessage(script);

	if (!img)
		throw new Error("image_text: img is null or undefined");

	await waitForImageLoad(img);

	const { font = "'Brush Script MT', 'Lucida Handwriting', 'TeX Gyre Chorus', cursive", size = 1 } = options;

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

	// Ensure texts is an array
	if (!Array.isArray(texts))
		texts = [texts];

	// Calculate spacing
	for (const text of texts) {
		const textElement = image_text_create_text(text, font, sizePercent);
		overlay.appendChild(textElement);
	}

	wrapper.appendChild(overlay);
}

// Example:
// image_text(['Top text', ['Left', 'Center', 'Right'], 'Bottom text'], { size: 1.2, font: 'Arial' });

// snow ----------------------------------------------------------------------

// Snowflake class
snow = () => {
	class Snowflake {
		constructor(canvas) {
			this.canvas = canvas;
			this.reset();
		}

		reset() {
			this.x = Math.random() * this.canvas.width;
			this.y = -Math.random() * this.canvas.height;
			this.radius = Math.random() * 2 + 1;
			this.density = Math.random() + 0.5;
		}

		update(angle) {
			this.y += Math.pow(this.density, 2) + 1;
			this.x += Math.sin(angle) * 2;

			if (this.y > this.canvas.height) {
				this.x = Math.random() * this.canvas.width;
				this.y = 0;
			}
		}

		draw(ctx) {
			// ctx.beginPath(); // <--- REMOVE THIS LINE
			ctx.moveTo(this.x, this.y); // Use moveTo to prevent lines between flakes
			ctx.arc(this.x, this.y, this.radius, 0, Math.PI * 2, true);
		}
	}

	var snow_canvas;
	var snowflakes = [];
	var angle = 0;
	var velocity = 0.05;
	var maxVelocity = 0.01; // Maximum velocity magnitude
	var minVelocity = -0.01; // Minimum velocity magnitude
	var maxAcceleration = 0.005; // Maximum change in velocity per frame
	var animationFrameId;

	function snowing() {
		const ctx = snow_canvas.getContext('2d');
		ctx.clearRect(0, 0, snow_canvas.width, snow_canvas.height);

		ctx.fillStyle = 'rgba(255, 255, 255, 0.8)';
		ctx.beginPath();


		// Randomly change velocity
		velocity += (Math.random() - 0.5) * maxAcceleration;

		// Limit velocity to the range [-0.02, 0.02]
		velocity = Math.max(minVelocity, Math.min(maxVelocity, velocity));

		// Update angle using velocity
		angle += velocity;

		snowflakes.forEach(flake => {
			flake.update(angle);
			flake.draw(ctx);
		});

		ctx.fill();
		animationFrameId = requestAnimationFrame(snowing);
	}

	function createFlakes() {
		const flakeCount = Math.floor(window.innerWidth / 4);
		snowflakes = Array(flakeCount).fill().map(() => new Snowflake(snow_canvas));
	}

	function resizeCanvas() {
		snow_canvas.width = window.innerWidth;
		snow_canvas.height = window.innerHeight;
		createFlakes();
	}

	function snow() {
		if (checkReducedMotionPreference()) {
			console.log('Reduced motion preferred - snow effect disabled');
			return;
		}

		// Create and setup canvas
		snow_canvas = document.createElement('canvas');
		snow_canvas.id = 'snowCanvas';
		snow_canvas.style.cssText = 'position: fixed; top: 0; left: 0; pointer-events: none; z-index: 9999;';

		// Add canvas to document
		const body = document.body;
		body.insertBefore(snow_canvas, body.firstChild);

		// Initialize canvas and snowflakes
		resizeCanvas();
		window.addEventListener('resize', resizeCanvas);

		// Stop any existing animation before starting new one
		if (animationFrameId) {
			cancelAnimationFrame(animationFrameId);
		}

		// Start animation
		snowing();
	}

	snow();
}

// rain ----------------------------------------------------------------------

rain = () => {
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

	rain();
}

// matrix WIP! ---------------------------------------------------------------

matrix = (chars) => {
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
	function matrixFallingSlow(chars) {
		if (!matrix_canvas) return;

		chars = chars || matrix_chars;

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
				const text = chars.charAt(Math.floor(Math.random() * chars.length));
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

		requestAnimationFrame(() => matrixFallingSlow(chars));
	}


	// Main function to set up and start the effect
	function matrix(chars) {
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
		matrixFallingSlow(chars);
	}

	matrix(chars);
}

// bouncing messages ---------------------------------------------------------

function bounceMessage(selector = '.m1') {
	const current_script = document.currentScript||script;
	bounceMessage_async(selector, current_script)
}

async function bounceMessage_async(selector, script) {
	await waitForMessage(script);
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

// echo ----------------------------------------------------------------------

function echo_n_to(script, ...args) {
	// Create echo container if next element isn't our pre.echo
	let pre = script.nextElementSibling;

	if (!pre || pre.tagName !== 'PRE' || !pre.classList.contains('echo')) {
		pre = document.createElement('pre');
		pre.className = 'echo';
		const code = document.createElement('code');
		pre.appendChild(code);
		script.parentNode.insertBefore(pre, script.nextSibling);
	}

	// Append encoded content to the code element
	const code = pre.querySelector('code');
	code.innerHTML += args.map(arg => {
		// Handle DOM elements and collections
		if (arg instanceof HTMLElement) {
			return arg.outerHTML;
		} else if (arg instanceof NodeList || arg instanceof HTMLCollection) {
			return Array.from(arg).map(el => el.outerHTML).join('');
		} else if (arg instanceof DocumentFragment) {
			return Array.from(arg.children).map(el => el.outerHTML).join('');
		} else {
			// Handle non-DOM elements as before
			return encode_entities(typeof arg === 'object' ? JSON.stringify(arg) : String(arg));
		}
	}).join(' ');
	return pre; // For chaining
}

function echo_to(script, ...args) {
	return echo_n_to(script, ...args, '\n');
}

function echo_n(...args) {
	return echo_n_to(document.currentScript||script, ...args);
}

function echo(...args) {
	return echo_n(...args, '\n');
}

// effects: fire -------------------------------------------------------------

(function() {
	const FX_ANIMATION_INTERVAL = 50; // How often to update animations (ms)

	let fire_elements = [];
	let animation_running = false;
	let animation_frame_id = null;
	let last_animation_time = 0;

	// Efficient element finder
	function fx_update_elements() {
		fire_elements = Array.from(document.getElementsByClassName('fire'));

		// Start animation if elements exist and not already running
		if (fire_elements.length > 0 && !animation_running) {
			fx_start_animation();
		}
		// Stop animation if no elements exist
		else if (fire_elements.length === 0 && animation_running) {
			fx_stop_animation();
		}
	}

	function fx_create_fire_shadow() {
		const rand = Math.random;
		const dy = rand() * 2 + 1;
		const x1 = rand() * 4 - 2;
		const y1 = -dy;
		const x2 = rand() * 3 - 1.5;
		const y2 = y1 - dy;
		const x3 = rand() * 2 - 1;
		const y3 = y2 - dy;
		return `${x1}px ${y1}px 7px rgb(255, 255, 0),
				${x2}px ${y2}px 14px rgb(255, 127, 0),
				${x3}px ${y3}px 21px rgb(255, 0, 0)`;
	}

	function fx_animate(timestamp) {
		// Throttle animation to FX_ANIMATION_INTERVAL
		if (timestamp - last_animation_time >= FX_ANIMATION_INTERVAL) {
			// Update fire elements
			for (const element of fire_elements) {
				element.style.textShadow = fx_create_fire_shadow();
			}
			last_animation_time = timestamp;
		}

		if (animation_running && fire_elements.length > 0 && !checkReducedMotionPreference()) {
			animation_frame_id = requestAnimationFrame(fx_animate);
		} else {
			fx_stop_animation();
		}
	}

	function fx_start_animation() {
		if (!animation_running) {
			animation_running = true;
			animation_frame_id = requestAnimationFrame(fx_animate);
		}
	}

	function fx_stop_animation() {
		if (animation_running) {
			animation_running = false;
			if (animation_frame_id) {
				cancelAnimationFrame(animation_frame_id);
				animation_frame_id = null;
			}
		}
	}

	// Set up mutation observer to watch for DOM changes
	const observer = new MutationObserver((mutations) => {
		let should_update = false;

		// TODO too deep nesting, use extra top-level functions perhaps

		for (const mutation of mutations) {
			const hasFireElement = node =>
				node.nodeType === Node.ELEMENT_NODE &&
				(node.classList?.contains('fire') || node.querySelector?.('.fire'));

			const checkNodes = nodes => [...nodes].some(hasFireElement);

			should_update = checkNodes(mutation.addedNodes) ||
							checkNodes(mutation.removedNodes);

			// Check attribute changes for class modifications
			if (!should_update && mutation.type === 'attributes' && mutation.attributeName === 'class') {
				should_update = true;
			}

			if (should_update) break;
		}

		if (should_update) {
			fx_update_elements();
		}
	});

	// Start observing
	async function fx_main() {
		await $waitUntilElement("div.messages");
		observer.observe($("div.messages"), {
			childList: true,
			subtree: true,
			attributes: true,
			attributeFilter: ['class']
		});
		// Initial check
		fx_update_elements();
	}

	fx_main();
})();


// let fameElements = [];
// let a = 0; // Fame animation angle

// fameElements = Array.from(document.getElementsByClassName('fame'));
// if ((fireElements.length > 0 || fameElements.length > 0) && !animationRunning) {

// // Update fame elements
// fameElements.forEach(element => {
// 	element.style.textShadow = createFameShadow(a);
// });

// a += Math.PI * 2 * 20/360;

// function createFameShadow(angle) {
// 	const sin = Math.sin, cos = Math.cos, pi2 = 2 * Math.PI;
// 	const r = 4;
// 	const x1 = r * sin(angle), y1 = r * cos(angle);
// 	const x2 = r * sin(angle + pi2/3), y2 = r * cos(angle + pi2/3);
// 	const x3 = r * sin(angle - pi2/3), y3 = r * cos(angle - pi2/3);
// 	return `${x1}px ${y1}px 15px rgb(255, 0, 0),
// 			${x2}px ${y2}px 15px rgb(0, 200, 0),
// 			${x3}px ${y3}px 15px rgb(63, 63, 255)`;
// }
//

// fixed header --------------------------------------------------------------

function header(query) {
	const $header = $(query || ".header");
	const observer = new ResizeObserver(entries => {
		const height = entries[0].contentRect.height;
		$("div.messages").style.marginTop = height + 'px';
	});
	observer.observe($header);
}
