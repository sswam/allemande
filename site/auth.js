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
	const username = $('#username').value;
	const password = $('#password').value;
	if (!username || !password) {
		console.error('Username and password are required');
		await loginFailed();
		return;
	}
	console.log('Logging in:', username);
	const response = await fetch('/x/login', {
		method: 'POST',
		headers: {
			'Content-Type': 'application/json'
		},
		body: JSON.stringify({ username, password })
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

function mainDomainURL() {
	const { protocol, hostname } = window.location;
	return `${protocol}//${hostname.split('.').slice(-2).join('.')}`;
}

async function logout(e) {
	e.preventDefault();
	console.log('Logging out');
	// We need to strip the subdomain off the current URL proto and host
	// because the logout endpoint is on the main domain.
	const logoutURL = mainDomainURL() + '/x/logout';
	const response = await fetch(logoutURL, {
		method: 'POST',
		credentials: 'include',
	});
	if (!response.ok) {
		console.error('Logout failed:', response.status);
		return;
	}
	const data = await response.json();
	// we don't need the response data
	console.log("Logout successful:", data);
}

async function logoutHome(e) {
	await logout(e);
	checkLogin();
}

async function logoutChat(e) {
	await logout(e);
	const homeURL = mainDomainURL();
	window.location = homeURL;
}

let userData;

function setupLoggedIn() {
	console.log('username:', userData.username);
	$('#session_username').value = userData.username;
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

function authHomepage() {
	$on($id('login'), 'click', login);
	$on($id('logout'), 'click', logoutHome);

	checkLogin();
}
