// matrix WIP! ---------------------------------------------------------------

// Global variables for the Matrix effect
var matrix_canvas;
var matrix_ctx;

// An array to store the Y position of the last character in each column
var y_positions;

// The characters to be used in the rain
const katakana = 'アァカサタナハマヤャラワガザダバパイィキシチニヒミリヰギジヂビピウゥクスツヌフムユュルグズブヅプエェケセテネヘメレヱゲゼデベペオォコソトノホモヨョロヲゴゾドボポヴッン';
const latin = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ';
const nums = '0123456789';
const matrix_chars = katakana + latin + nums;

// Font size for the characters
const font_size = 16;

// The main animation loop
function matrixFalling() {
  if (!matrix_canvas) return;

  // Draw a semi-transparent black rectangle over the whole canvas.
  // This is what creates the fading trail effect for the characters.
  matrix_ctx.fillStyle = 'rgba(0, 0, 0, 0.05)';
  matrix_ctx.fillRect(0, 0, matrix_canvas.width, matrix_canvas.height);

  // Set the color for the characters
  matrix_ctx.fillStyle = '#0F0'; // Bright green
  matrix_ctx.font = font_size + 'px monospace';

  // Loop over each column
  for (let i = 0; i < y_positions.length; i++) {
    // Pick a random character from the character set
    const text = matrix_chars.charAt(Math.floor(Math.random() * matrix_chars.length));

    // Get the x and y coordinates for this character
    const x = i * font_size;
    const y = y_positions[i] * font_size;

    // Draw the character
    matrix_ctx.fillText(text, x, y);

    // If the character reaches the bottom of the screen,
    // there's a chance it will be reset back to the top.
    // The random check makes the columns reset at different times.
    if (y > matrix_canvas.height && Math.random() > 0.975) {
      y_positions[i] = 0;
    }

    // Move the y position down for the next frame
    y_positions[i]++;
  }

  requestAnimationFrame(matrixFalling);
}

// Main function to set up and start the Matrix effect
function matrix() {
  if (typeof checkReducedMotionPreference === 'function' && checkReducedMotionPreference()) {
    console.log('Reduced motion preferred - matrix effect disabled');
    return;
  }

  matrix_canvas = document.createElement('canvas');
  matrix_canvas.id = 'matrixCanvas';
  matrix_canvas.style.cssText = 'position: fixed; top: 0; left: 0; pointer-events: none; z-index: 9999; background-color: black;';

  const body = document.body;
  body.insertBefore(matrix_canvas, body.firstChild);

  matrix_ctx = matrix_canvas.getContext('2d');

  // Function to handle resizing the canvas
  function resizeCanvas() {
    matrix_canvas.width = window.innerWidth;
    matrix_canvas.height = window.innerHeight;

    // Calculate how many columns of text can fit
    const columns = Math.floor(matrix_canvas.width / font_size);
    // Initialize an array to track the y-position for each column
    y_positions = Array(columns).fill(1);
  }

  resizeCanvas();
  window.addEventListener('resize', resizeCanvas);

  matrixFalling();
}
