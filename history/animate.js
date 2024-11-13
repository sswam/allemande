function animate_fire() {
	const rand = Math.random;
	const dy = rand() * 2 + 1;
	const x1 = rand() * 4 - 2;
	const y1 = -dy;
	const x2 = rand() * 3 - 1.5;
	const y2 = y1 - dy;
	const x3 = rand() * 2 - 1;
	const y3 = y2 - dy;
	const shadow1 = `${x1}px ${y1}px 7px rgba(255, 255, 0, 0.5)`;
	const shadow2 = `${x2}px ${y2}px 14px rgba(255, 127, 0, 0.5)`;
	const shadow3 = `${x3}px ${y3}px 21px rgba(255, 0, 0, 0.5)`;
	const shadow = `${shadow1}, ${shadow2}, ${shadow3}`;

	for (const e of document.querySelectorAll(".fire")) {
		e.style.textShadow = shadow;
	}
}

let fame_angle = 0;

function animate_fame() {
	const { sin, cos, PI } = Math;
	const r = 4;
	const a = fame_angle;
	const pi2 = 2 * PI;

	const x1 = r * sin(a), y1 = r * cos(a);
	const x2 = r * sin(a + pi2/3), y2 = r * cos(a + pi2/3);
	const x3 = r * sin(a - pi2/3), y3 = r * cos(a - pi2/3);

	const shadow1 = `${x1}px ${y1}px 15px rgba(255, 0, 0, 0.8)`;
	const shadow2 = `${x2}px ${y2}px 15px rgba(0, 200, 0, 0.8)`;
	const shadow3 = `${x3}px ${y3}px 15px rgba(63, 63, 255, 0.8)`;
	const shadow = `${shadow1}, ${shadow2}, ${shadow3}`;

	for (const e of document.querySelectorAll(".fame")) {
		e.style.textShadow = shadow;
	}

	fame_angle += pi2 * 20 / 360;
}

function animate() {
	animate_fire();
	animate_fame();
}
