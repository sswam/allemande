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

function previous(selector, lookBack = 0) {
	// Get all elements matching the selector
	const elements = Array.from(document.querySelectorAll(selector));

	// Find elements before the script
	const beforeScript = elements.filter(element =>
		!(document.currentScript.compareDocumentPosition(element) & Node.DOCUMENT_POSITION_FOLLOWING)
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

function image_text(img, text1, text2, size = 1, font = "'Brush Script MT', 'Lucida Handwriting', cursive") {
  if (!img)
    throw new Error("image_text: img is null or undefined");

  // Create wrapper div
  const wrapper = document.createElement('div');
  wrapper.style.position = 'relative';
  wrapper.style.display = 'inline-block';

  // Wrap the image
  img.parentNode.insertBefore(wrapper, img);
  wrapper.appendChild(img);

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

  // Helper to create text element
  function createText(content) {
    if (!content) return null;

    const text = document.createElement('div');
    text.textContent = content;
    text.style.cssText = `
      font-family: ${font};
      font-size: ${Math.min(img.width / 8, 60) * size}px;
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
