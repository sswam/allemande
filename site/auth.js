function getCookie(name) {
	const value = `; ${document.cookie}`;
	const parts = value.split(`; ${name}=`);
	if (parts.length !== 2)
		return null;
	return parts.pop().split(';').shift();
}

function getJSONCookie(name) {
	const cookieValue = getCookie(name);
	if (!cookieValue)
		return null;
	try {
		const decodedValue = decodeURIComponent(cookieValue);
		return JSON.parse(decodedValue);
	} catch (e) {
		console.error('Error parsing cookie:', e);
		return null;
	}
}

async function loginFailed() {
	// flash the login button red
	$('#login').classList.add('error');
	await $wait(300);
	$('#login').classList.remove('error');
}

async function login(e) {
	e.preventDefault();
	const email = $('#email').value;
	const password = $('#password').value;
	if (!email || !password) {
		console.error('Email and password are required');
		await loginFailed();
		return;
	}
	console.log('Logging in:', email);
	const response = await fetch('/x/login', {
		method: 'POST',
		headers: {
			'Content-Type': 'application/json'
		},
		body: JSON.stringify({ email, password })
	});
	if (!response.ok) {
		console.error('Login failed:', response.status);
		await loginFailed();
		return;
	}
	const data = await response.json();
	// we don't need the response data
	console.log("Login successful:", data);
	checkLogin();
}

async function logout(e) {
	e.preventDefault();
	console.log('Logging out');
	const response = await fetch('/x/logout', {
		method: 'POST'
	});
	if (!response.ok) {
		console.error('Logout failed:', response.status);
		return;
	}
	const data = await response.json();
	// we don't need the response data
	console.log("Logout successful:", data);
	checkLogin();
}

let userData;

function setupLoggedIn() {
	console.log('Email:', userData.email);
// 	console.log('Theme:', userData.preferences.theme);
// 	console.log('Numbers:', userData.numbers);
	$('#session_email').value = userData.email;
	for (const e of $$('.login'))
		e.classList.add('hidden');
	for (const e of $$('.session.hidden'))
		e.classList.remove('hidden');
}

function setupLoggedOut() {
	for (const e of $$('.session'))
		e.classList.add('hidden');
	for (const e of $$('.login.hidden'))
		e.classList.remove('hidden');
}

function checkLogin() {
	userData = getJSONCookie('user_data');
	if (userData)
		setupLoggedIn();
	else
		setupLoggedOut();
}

$('#login').addEventListener('click', login);
$('#logout').addEventListener('click', logout);

checkLogin();
