// Load a profile card from a template and data file
// With image processing to extract colors for styling

async function createCard(template) {
	const container = document.createElement('div');
	container.className = 'card-container';
	container.innerHTML = await $get(template, { credentials: 'include' });
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

function getSaturatedColors(img) {
	const canvas = document.createElement('canvas');
	const ctx = canvas.getContext('2d');
	const res = 64;
	canvas.width = res;
	canvas.height = res;
	ctx.drawImage(img, 0, 0, res, res);
	const imageData = ctx.getImageData(0, 0, res, res).data;

	// Initialize 12 hue buckets (30-degree segments)
	const hueBuckets = Array(12).fill(null).map(() => ({
		r: 0, g: 0, b: 0, count: 0
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

		// Filter out dull colors (low saturation, too dark/light)
		if (saturation < 0.1 || lightness < 0.40 || lightness > 0.8) continue;

		// Filter out typical skin/hair tones (browns, tans)
		const isSkintone = (r > g && g > b) &&
						(r - b < 100) &&
						(saturation < 0.5) &&
						(lightness > 0.3 && lightness < 0.7);
		if (isSkintone) continue;

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

		// Add to appropriate bucket (0-11)
		const bucketIndex = Math.floor(hue / 30);
		hueBuckets[bucketIndex].r += r;
		hueBuckets[bucketIndex].g += g;
		hueBuckets[bucketIndex].b += b;
		hueBuckets[bucketIndex].count++;
	}

	// Calculate averages and filter empty buckets
	const colors = hueBuckets
		.map((bucket, index) => {
			if (bucket.count === 0) return null;
			return {
				r: Math.round(bucket.r / bucket.count),
				g: Math.round(bucket.g / bucket.count),
				b: Math.round(bucket.b / bucket.count),
				count: bucket.count,
				hue: index * 30 + 15 // Center of bucket
			};
		})
		.filter(color => color !== null);

	/*
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
			count: totalCount,
			hue: (current.hue * current.count + next.hue * next.count) / totalCount
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
	*/
	mergedColors = colors;

	// If no colors were found, return no gradient
	if (mergedColors.length === 0) {
		return { colors: [], gradient: 'none' };
	}

	// Find the most populous color and reorder from there
	const sortedColors = [...mergedColors].sort((a, b) => b.count - a.count);

	const startHue = sortedColors[0].hue;

	const reorderedColors = mergedColors.sort((a, b) => {
		const aOffset = (a.hue - startHue + 360) % 360;
		const bOffset = (b.hue - startHue + 360) % 360;
		return aOffset - bOffset;
	});

	// Calculate positions based on hue
	const colorStops = reorderedColors.map((color, index) => {
		const hueOffset = (color.hue - startHue + 360) % 360;
		const position = (hueOffset / 360) * 100;
		return {
			...color,
			position: Math.round(position * 10) / 10 // Round to 1 decimal place
		};
	});

	// Add the first color at 100% to close the gradient loop
	colorStops.push({
		...reorderedColors[0],
		position: 100
	});

	// Create CSS gradient with positioned color stops
	const gradientColors = colorStops
//		.map(color => `rgb(${color.r},${color.g},${color.b}) ${color.position}%`)
		.map(color => `rgb(${color.r},${color.g},${color.b})`)
		.join(', ');

	const gradient = reorderedColors.length > 0
		? `linear-gradient(165deg, ${gradientColors})`
		: 'none';

	return {
		colors: reorderedColors.map(color => ({
			rgb: `rgb(${color.r},${color.g},${color.b})`,
			count: color.count
		})),
		gradient: gradient
	};
}

function label_em_and_value(label, value) {
	const em = document.createElement('em');
	em.textContent = label;
	const html = em.outerHTML + ': ' + value;
	return html;
}

async function loadProfile(path, template = ALLYCHAT_CHAT_URL + '/card.html') {
	const name = path.replace(/.*\//, '');
	const container = await createCard(template);
	const card = container.firstElementChild;

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
	card.querySelector('.card-interests').innerHTML = label_em_and_value('Interests', data.interests);
	card.querySelector('.card-match').innerHTML = label_em_and_value('Match', data.match);
	card.querySelector('.card-motto').textContent = `"${data.motto}"`;
	card.querySelector('.card-chat').textContent = data.chat;
	card.querySelector('.card-likes').innerHTML = label_em_and_value('Likes', data.likes);
	card.querySelector('.card-dislikes').innerHTML = label_em_and_value('Dislikes', data.dislikes);
	card.querySelector('.card-fun-fact').textContent = data['fun fact'];

	// Wait for image to load to get colors
	const img = card.querySelector('.card-avatar');
	img.src = `/cast/${path}.jpg`;
	await waitForImageLoad(img);
	const colors = getAverageColor(img);
	colors.text = "black";
	const saturatedColors = getSaturatedColors(img);
	const front = card.querySelector('.card-front');
	const back = card.querySelector('.card-back');
	front.style.setProperty('--card-bg', colors.bg);
//	front.style.setProperty('--text-color', colors.text);
	front.style.setProperty('--card-gradient', saturatedColors.gradient);
	back.style.setProperty('--card-bg', colors.bg);
//	back.style.setProperty('--text-color', colors.text);
	back.style.setProperty('--card-gradient', saturatedColors.gradient);

	// Handle flip
	card.addEventListener('click', function(ev) {
		// Ignore clicks on images or links
		if (['IMG', 'A'].includes(ev.target.tagName)) return;

		// Check if there's any text selected
		if (window.getSelection().toString().length > 0) return;

		const flipped = card.classList.contains('flipped');
		this.classList.toggle('flipped');
		if (flipped)
			setTimeout(() => { this.classList.remove('preserve-3d'); }, 600);
		else
			this.classList.add('preserve-3d');
		this.style.transform = `rotateY(${!flipped ? 180 : 0}deg)`;
	});

	// Add shine effect on hover
	container.addEventListener('mousemove', (e) => {
		const rect = container.getBoundingClientRect();
		const x = e.clientX - rect.left;
		const y = e.clientY - rect.top;

		// Convert to percentages for shine position
		const xPercent = (x / rect.width) * 100;
		const yPercent = (y / rect.height) * 100;

		// Convert coordinates for tilt
		const xTilt = -(x / rect.width - 0.5) * 2;
		const yTilt = -(y / rect.height - 0.5) * 2;

		// Apply rotation (max 10 degrees)
		const rotateX = yTilt * -10;
		const rotateY = xTilt * 10;

		const flipped = card.classList.contains('flipped');

		// Combine 3D effect with flip state
		const flipRotation = flipped ? 180 : 0;

		// Set transform-origin for more natural movement
		// card.style.transformOrigin = `${xPercent}% ${yPercent}%`;
		card.style.transform = `rotateY(${flipRotation + rotateY}deg) rotateX(${flipped ? -rotateX : rotateX}deg)`;

		// Update shine effect position and opacity
		card.style.setProperty('--shine-x', `${flipped ? 100-xPercent : xPercent}%`);
		card.style.setProperty('--shine-y', `${yPercent}%`);
		card.style.setProperty('--shine-opacity', '1');
	});

	container.addEventListener('mouseleave', () => {
		const flipRotation = card.classList.contains('flipped') ? 180 : 0;

		// Reset transform origin to center
		// card.style.transformOrigin = '50% 50%';
		card.style.transform = `rotateY(${flipRotation}deg)`;
		card.style.setProperty('--shine-opacity', '0');
	});

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
