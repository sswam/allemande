// Load a profile card from a template and data file
// With image processing to extract colors for styling

async function createCard(template) {
	const container = document.createElement('div');
	container.className = 'card-container';
	const container2 = document.createElement('div');
	container2.className = 'card-container-2';
	container2.innerHTML = await $get(template, { credentials: 'include' });
	container.appendChild(container2);
	return container;
}

function getAverageColor(img) {
	const canvas = document.createElement('canvas');
	const ctx = canvas.getContext('2d');
	const res = 16;
	canvas.width = res;
	canvas.height = res;
	ctx.drawImage(img, 0, 0, res, res);
	const imageData = ctx.getImageData(0, 0, res, res).data;
	let r = 0, g = 0, b = 0;
	for (let i = 0; i < imageData.length; i += 4) {
		r += imageData[i];
		g += imageData[i + 1];
		b += imageData[i + 2];
	}
	const count = imageData.length / 4;
	r = Math.round(r / count);
	g = Math.round(g / count);
	b = Math.round(b / count);
//	const brightness = (r * 299 + g * 587 + b * 114) / 1000;
	return {
		bg: `rgb(${r},${g},${b})`,
//		text: brightness > 128 ? '#000' : '#fff'
	};
}

function getSaturatedColors(img, dark) {
	const canvas = document.createElement('canvas');
	const ctx = canvas.getContext('2d');
	const res = 64;
	canvas.width = res;
	canvas.height = res;
	ctx.drawImage(img, 0, 0, res, res);
	const imageData = ctx.getImageData(0, 0, res, res).data;

	// Initialize 12 hue buckets (30-degree segments)
	const hueBuckets = Array(12).fill(null).map(() => ({
		r: 0, g: 0, b: 0, 
		hue: 0, saturation: 0, lightness: 0,
		count: 0,
	}));

	// Process each pixel
	for (let i = 0; i < imageData.length; i += 4) {
		const r = imageData[i];
		const g = imageData[i + 1];
		const b = imageData[i + 2];

		// Convert to HSL to check saturation and get hue
		const max = Math.max(r, g, b);
		const min = Math.min(r, g, b);
		const delta = max - min;
		const lightness = (max + min) / 510; // 0-1 range
		const saturation = max === 0 ? 0 : delta / max;

		// Calculate hue (0-360 degrees)
		let hue = 0;
		if (delta !== 0) {
			if (max === r) {
				hue = ((g - b) / delta) % 6;
			} else if (max === g) {
				hue = (b - r) / delta + 2;
			} else {
				hue = (r - g) / delta + 4;
			}
			hue = (hue * 60 + 360) % 360;
		}

		// Calculate dullness confidence (0-1)
		let dull = Math.max(
			Math.max(0, 0.2 - saturation), // Low saturation
			Math.max(0, 0.2 - lightness),  // Too dark
			Math.max(0, lightness - 0.8)   // Too light
		);
		dull = Math.min(1, dull * 5); // Normalize to 0-1

		if (dull > 0.5) continue; // Skip dull colors

		let skinTone = 1;
		skinTone *= Math.max(0, 1 - Math.abs(hue - 25) / 25); // Hue between 0-50, centered at 25
		skinTone *= Math.max(0, 1 - Math.abs(saturation - 0.4) / 0.2); // Saturation around 0.4
		skinTone *= Math.max(0, 1 - Math.abs(lightness - 0.5) / 0.3); // Lightness around 0.5
		skinTone *= (r > g && g > b) ? Math.min(1, (100 - Math.abs(r - g)) / 50) : 0; // R>G>B check

		const weight = 1 - Math.max(dull, skinTone);

		// Add to appropriate bucket (0-11)
		const bucketIndex = Math.floor(hue / 30);
		const bucket = hueBuckets[bucketIndex];
		bucket.r += r * weight;
		bucket.g += g * weight;
		bucket.b += b * weight;
		bucket.hue += hue * weight;
		bucket.saturation += saturation * weight;
		bucket.lightness += lightness * weight;
		bucket.count += weight;
	}

	const minCount = imageData.length * 1/10000

	// Calculate averages and filter buckets with too few pixels
	let colors = hueBuckets
		.map((bucket, index) => {
			if (bucket.count < minCount)
				return null;
			return {
				r: bucket.r / bucket.count,
				g: bucket.g / bucket.count,
				b: bucket.b / bucket.count,
				hue: bucket.hue / bucket.count,
				saturation: bucket.saturation / bucket.count,
				lightness: bucket.lightness / bucket.count,
				count: bucket.count,
				bucketHue: index * 30 + 15 // Center of bucket
			};
		})
		.filter(color => color !== null);

	// Merge similar adjacent colors
	const mergedColors = [];
	let skipFirst = false;

	for (let i = 0; i < colors.length; i++) {
		// Skip first iteration if we merged first and last
		if (i === 0 && skipFirst) continue;

		const current = colors[i];
		const nextIndex = (i + 1) % colors.length;
		const next = colors[nextIndex];

		// Skip if no next color or we're at the last color (unless checking wraparound)
		if (!next || (i === colors.length - 1 && mergedColors.length > 0)) {
			mergedColors.push(current);
			continue;
		}

		// Check if hues are too different
		if (Math.abs(current.hue - next.hue) > 30) {
			mergedColors.push(current);
			continue;
		}

		// Check if colors are similar enough to merge
		const colorDiff = Math.abs(current.r - next.r) +
						Math.abs(current.g - next.g) +
						Math.abs(current.b - next.b);

		if (colorDiff >= 50) {
			mergedColors.push(current);
			continue;
		}

		// Merge colors using weighted average based on pixel count
		const totalCount = current.count + next.count;
		const merged = {
			r: Math.round((current.r * current.count + next.r * next.count) / totalCount),
			g: Math.round((current.g * current.count + next.g * next.count) / totalCount),
			b: Math.round((current.b * current.count + next.b * next.count) / totalCount),
			hue: (current.hue * current.count + next.hue * next.count) / totalCount,
			saturation: (current.saturation * current.count + next.saturation * next.count) / totalCount,
			lightness: (current.lightness * current.count + next.lightness * next.count) / totalCount,
			count: totalCount,
			bucketHue: (current.bucketHue + next.bucketHue) / 2,
		};

		// Handle wraparound case (merging last with first)
		if (i === colors.length - 1) {
			mergedColors[0] = merged;
			skipFirst = true;
		} else {
			mergedColors.push(merged);
			i++; // Skip next color as it's merged
		}
	}

	colors = mergedColors;

	// If no colors were found, return no gradient
	if (colors.length === 0) {
		return { colors: [], gradient: 'none' };
	}

	// Find the most populous color and reorder from there
	colors = [...colors].sort((a, b) => b.count - a.count);

	const startHue = colors[0].bucketHue;

	colors = colors.sort((a, b) => {
		const aOffset = (a.bucketHue - startHue + 360) % 360;
		const bOffset = (b.bucketHue - startHue + 360) % 360;
		return aOffset - bOffset;
	});

	// For background colours, we want light colours, so apply minimum lightness and covert back to RGB
	colors = colors.map(color => {
		let { hue, saturation, lightness } = color;

		// Ensure lightness appropriate for dark or light mode
		let lightnessCard;
		let lightnessBorder;
		if (dark) {
			lightnessCard = lightness / 5 + 0.05;
			lightnessBorder = lightness / 3 + 0.1;
		} else {
			lightnessCard = lightness / 5 + 0.75;
			lightnessBorder = lightness / 3 + 0.2;
		}

		// Ensure saturation is at least 0.2 for visibility
		saturation = clamp(saturation, 0.2, 1);

		// Convert HSL back to RGB
		const rgb = hslToRgb(hue, saturation, lightnessCard);
		const rgbBorder = hslToRgb(hue, saturation, lightnessBorder);

		return {
			...color,
			r: rgb.r,
			g: rgb.g,
			b: rgb.b,
			rBorder: rgbBorder.r,
			gBorder: rgbBorder.g,
			bBorder: rgbBorder.b,
		};
	});

	// Calculate positions based on hue
	const colorStops = colors.map((color, index) => {
		const hueOffset = (color.bucketHue - startHue + 360) % 360;
		const position = (hueOffset / 360) * 100;
		return {
			...color,
			position: Math.round(position * 10) / 10 // Round to 1 decimal place
		};
	});

	// Add the first color at 100% to close the gradient loop
	colorStops.push({
		...colors[0],
		position: 100
	});

	// Create CSS gradient with positioned color stops
	const gradientColors = colorStops
//		.map(color => `rgb(${color.r},${color.g},${color.b}) ${color.position}%`)
		.map(color => `rgb(${color.r},${color.g},${color.b})`)
		.join(', ');

	const gradientColorsBorder = colorStops
		.map(color => `rgb(${color.rBorder},${color.gBorder},${color.bBorder})`)
		.join(', ');

	const gradient = `linear-gradient(165deg, ${gradientColors})`;

	const gradientBorder = `linear-gradient(165deg, ${gradientColorsBorder})`;

	return {
		colors: colors.map(color => ({
			rgb: `rgb(${color.r},${color.g},${color.b})`,
			count: color.count
		})),
		gradient: gradient,
		gradientBorder: gradientBorder,
	};
}

function label_and_value(label, value) {
	const em = document.createElement('em');
	em.style.fontWeight = 'bold';
	em.textContent = label;
	const html = em.outerHTML + ': ' + value;
	return html;
}

async function loadProfile(path, template = ALLYCHAT_CHAT_URL + '/card.html') {
	// check dark mode, if body has "dark" class
	const dark = document.body.matches('.dark');
	const name = path.replace(/.*\//, '');
	const container = await createCard(template);
	const card = container.querySelector('.card');

	const text = await $get(`/cast/${path}.rec`);

	const data = {};
	for (const line of text.split('\n')) {
		const [key, value] = line.split(':', 2).map(s => s.trim());
		if (key) data[key] = value;
	}

	// Fill in content
	const link = document.createElement('a');
	link.href = ALLYCHAT_CHAT_URL + `/#cast/${path}`;
	link.innerText = name;
	card.querySelector(".card-name").appendChild(link);
	card.querySelector('.card-bio').textContent = data.bio;
	card.querySelector('.card-interests').innerHTML = label_and_value('Interests', data.interests);
	card.querySelector('.card-match').innerHTML = label_and_value('Match', data.match);
	card.querySelector('.card-motto').textContent = `"${data.motto}"`;
	card.querySelector('.card-chat').textContent = data.chat;
	card.querySelector('.card-likes').innerHTML = label_and_value('Likes', data.likes);
	card.querySelector('.card-dislikes').innerHTML = label_and_value('Dislikes', data.dislikes);
	card.querySelector('.card-fun-fact').textContent = data['fun fact'];

	// Overlay texture image
	const overlay = container.querySelector('.card-overlay');
	const texture = document.createElement('img');
	texture.src = `${ALLEMANDE_LOGIN_URL}/card/gold.jpg`
	texture.classList.add('nobrowse');
	overlay.appendChild(texture);

	// Wait for image to load to get colors
	const img = card.querySelector('.card-avatar');
	img.src = `/cast/${path}.jpg`;
	await waitForImageLoad(img);
	const colors = getAverageColor(img);
	colors.text = dark ? 'white' : 'black';
	const saturatedColors = getSaturatedColors(img, dark);
	const front = card.querySelector('.card-front');
	const back = card.querySelector('.card-back');
	card.style.setProperty('--card-bg', colors.bg);
	card.style.setProperty('--text-color', colors.text);
	card.style.setProperty('--card-gradient', saturatedColors.gradient);
	card.style.setProperty('--card-border-gradient', saturatedColors.gradientBorder);

	// Get flip rotation
	function getFlipRotation() {
		const oldTransform = card.style.transform || 'rotateY(0deg)';
		const oldTurn = parseFloat(oldTransform.match(/rotateY\((.+?)deg\)/)[1]);
		const flipRotation = Math.round(oldTurn / 180) * 180;
		return flipRotation;
	}

	// Handle flip
	card.addEventListener('click', function(ev) {
		// Ignore clicks on images or links
		if (['IMG', 'A'].includes(ev.target.tagName)) return;

		// Check if there's any text selected
		if (window.getSelection().toString().length > 0) return;

		// Check right or left side of card
		const rect = card.getBoundingClientRect();
		const x = ev.clientX - rect.left;
		const left = x < rect.width / 2;
		const delta = left ? 180 : -180;
		const flipRotation = getFlipRotation();
		const newTurn = flipRotation + delta;

		const flipped = card.classList.contains('flipped');
		card.classList.toggle('flipped');
		card.style.transform = `rotateY(${newTurn}deg)`;
	});

	// Add shine effect on hover
	function handleMove(x, y) {
		const rect = container.getBoundingClientRect();
		x -= rect.left;
		y -= rect.top;

		// Convert to percentages for shine position
		const xPercent = (x / rect.width) * 100;
		const yPercent = (y / rect.height) * 100;

		// Convert coordinates for tilt
		const xTilt = -(x / rect.width - 0.5) * 2;
		const yTilt = -(y / rect.height - 0.5) * 2;

		// Apply rotation
		const maxTilt = 15;
		const maxShade = 0.2;
		const rotateX = yTilt * -maxTilt;
		const rotateY = xTilt * maxTilt;

		const flipped = card.classList.contains('flipped');

		// Combine 3D effect with flip state
		const flipRotation = getFlipRotation();

		// Set transform-origin for more natural movement
		// card.style.transformOrigin = `${xPercent}% ${yPercent}%`;
		card.style.transform = `rotateY(${flipRotation + rotateY}deg) rotateX(${flipped ? -rotateX : rotateX}deg)`;

		// Update shine effect position and opacity
		container.style.setProperty('--shine-x', `${flipped ? 100-xPercent : xPercent}%`);
		container.style.setProperty('--shine-y', `${yPercent}%`);
		container.style.setProperty('--glow-x', `${xPercent}%`);
		container.style.setProperty('--glow-y', `${yPercent}%`);
		container.style.setProperty('--texture-x', -Math.round(Math.random()*20) + '%');
		container.style.setProperty('--texture-y', -Math.round(Math.random()*20) + '%');
		/*
		container.style.setProperty('--texture-x', `${flipped ? -xPercent : -100+xPercent}px`);
		container.style.setProperty('--texture-y', `${-yPercent}px`);
		*/
		container.style.setProperty('--mask-x', `${(flipped ? 1 : -1) * xPercent/4}px`);
		container.style.setProperty('--mask-y', `${-yPercent/4}px`);
		container.style.setProperty('--shine-opacity', '1');
		container.style.setProperty('--shade', Math.max(-rotateX / maxTilt * maxShade, 0).toString());
	}

	container.addEventListener('mousemove', (e) => handleMove(e.clientX, e.clientY));
	container.addEventListener('touchmove', (e) => {
		const touch = e.touches[0];
		handleMove(touch.clientX, touch.clientY);
	});

	function handleLeave() {
		const oldTransform = card.style.transform || 'rotateY(0deg)';
		const oldTurn = parseFloat(oldTransform.match(/rotateY\((.+?)deg\)/)[1]);
		const flipRotation = Math.round(oldTurn / 180) * 180;

		// Reset transform origin to center
		// card.style.transformOrigin = '50% 50%';
		card.style.transform = `rotateY(${flipRotation}deg)`;
		container.style.setProperty('--shine-opacity', '0');
		container.style.setProperty('--shade', '0');
	}

	container.addEventListener('mouseleave', handleLeave);
	container.addEventListener('touchend', handleLeave);
	container.addEventListener('touchcancel', handleLeave);

	// Load additional images if available
	// Try to load extra images until one fails
	const extraImagesContainer = card.querySelector('.card-extra-images-scrolling-content');
	for (let i=0; ; i++) {
		const extraImg = document.createElement('img');
		extraImg.src = `/cast/${path}-${i}.jpg`;
		try {
			await waitForImageLoad(extraImg);
		} catch (error) {
			break;
		}
		extraImagesContainer.appendChild(extraImg);
	}

	// add images again for continuous scroll
	const len = extraImagesContainer.children.length;
	for (let i=0; i < len; i++) {
		const img = extraImagesContainer.children[i];
		const secondImg = document.createElement('img');
		secondImg.src = img.src;
		secondImg.className = "nobrowse";
		extraImagesContainer.appendChild(secondImg);
	}

	return container;
}

async function loadProfiles(paths) {
	// Load all profiles in parallel and store them in order
	const profilePromises = paths.map(path => loadProfile(path));
	const profiles = await Promise.all(profilePromises);

	const cards = document.getElementById('cards-container');
	await waitForMessage(cards);

	// Append cards in the original order
	for (const card of profiles) {
		cards.appendChild(card);
	}
}
