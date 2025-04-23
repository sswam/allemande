function shuffleImages(selector) {
	const containers = document.querySelectorAll(selector);
	for (const container of containers) {
		const divs = Array.from(container.querySelectorAll("div.image"));

		container.innerHTML = "";

		// Fisher-Yates shuffle
		for (let i = divs.length - 1; i > 0; i--) {
			const j = Math.floor(Math.random() * (i + 1));
			[divs[i], divs[j]] = [divs[j], divs[i]];
		}

		divs.forEach(div => container.appendChild(div));
	}
}

setTimeout(() => shuffleImages('.cast > p'), 1000);
