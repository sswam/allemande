function shuffleImages(selector) {
	// Find the container element
	const container = document.querySelector(selector);
	if (!container) return;

	const images = container.querySelectorAll("img");

	// Get all img+div pairs
	const pairs = [];

	// Group images with their alt divs into pairs
	for (let img of images) {
		const altDiv = img.nextElementSibling;
		if (altDiv && altDiv.classList.contains('alt')) {
			pairs.push([img, altDiv]);
		} else {
			pairs.push([img, null]);
		}
	}

	container.innerHTML = "";

	// Fisher-Yates shuffle
	for (let i = pairs.length - 1; i > 0; i--) {
		const j = Math.floor(Math.random() * (i + 1));
		[pairs[i], pairs[j]] = [pairs[j], pairs[i]];
	}

	// Reinsert shuffled pairs
	pairs.forEach(([img, altDiv]) => {
		container.appendChild(img);
		if (altDiv) {
			container.appendChild(altDiv);
		}
	});
}

// Usage:
shuffleImages('.image_size_1 > p');
