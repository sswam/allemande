const $head = $('head');
const $room = $id('room');
const $content = $id('content');
const $messages_iframe = $id('messages_iframe');
const $form = $id('form');
const $title = $('title');
const $inputrow = $id("inputrow");
const $messages_overlay = $id("messages_overlay");

let VERSION;
let DEBUG = false;

let room;
let user;
let admin;

const ROOMS_URL = location.protocol + "//" + location.host.replace(/^chat\b/, "rooms")
const MAX_ROOM_NUMBER = 1e3; // 1e12;
const DEFAULT_ROOM = 'Ally Chat';


// utility functions ---------------------------------------------------------

function set_debug(debug) {
	DEBUG = debug;
	console.log = DEBUG ? console.log : () => {};
	$id("debug").style.display = DEBUG ? "block" : "none";
}

async function flash($el, className) {
	$('#attach').classList.add(className);
	await $wait(300);
	$('#attach').classList.remove(className);
}

// send a message ------------------------------------------------------------

function set_content(content) {
	$content.value = content;
	message_changed();
}

async function send(ev) {
	console.log("send");
	ev.preventDefault();

	const formData = new FormData($form);
	const message = $content.value;
	set_content("");

	const error = async (message) => {
		console.error(message);
		set_content(message);
		await flash($id('send'), 'error');
	};

	const response = await fetch('/x/post', {
		method: 'POST',
		body: formData,
	});

	if (!response.ok) {
		await error("send failed");
		return;
	}

	const data = await response.json();

	if (data.error) {
		await error(data.error);
		return;
	}
}


// clear messages (admin function) not implemented yet -----------------------

function clear() {
}

// handle enter key press ----------------------------------------------------

/*
function message_keypress(ev) {
        if (ev.keyCode == 13 && !ev.shiftKey) {
		ev.preventDefault();
		send(ev);
        }
}
*/

function message_keydown(ev) {
	if (ev.keyCode == 13 && ev.ctrlKey) {
		ev.preventDefault();
		send(ev);
	}
}

function room_keypress(ev) {
        if (ev.keyCode == 13) {
		ev.preventDefault();
		$content.focus();
		return false;
        }
}

// handle message change -----------------------------------------------------

function message_changed(ev) {
	if ($content.value == "") {
		$id('send').textContent = "poke";
	} else {
		$id('send').textContent = "send";
	}
}

// change room ---------------------------------------------------------------

function messages_iframe_set_src(url) {
	$messages_iframe.contentWindow.location.replace(url);
}

function clear_messages_box() {
	console.log("clearing messages box");
	messages_iframe_set_src("about:blank");
}

function set_room(r) {
	// check if r was passed
	console.log("setting room");
	if (r === undefined) {
		r = $room.value;
	}
	$room.value = r;
	clear_messages_box();
	room = r;
	set_title_hash(room);  // okay above the if?
	if (!room)
		return;
//	who();
	const room_stream_url = ROOMS_URL + "/"+room+".html?stream=1";
	console.log("setting $messages_iframe.src to", room_stream_url);
	messages_iframe_set_src(room_stream_url);
	setup_user_button();
}

/*
function set_room_user() {
	if (room == user)
		set_room("");
	else
		set_room(user);
}
*/


// user info and settings ----------------------------------------------------

function load_user_styles() {
	const $style = $id('user_styles');
	if ($style) { $remove($style); }
	const $link = $create('link');
	$link.id = 'user_styles';
	$link.rel = 'stylesheet';
	$link.type = 'text/css';
	$link.href = '/users/'+user+'/theme.css';
	$head.append($link);
}

function logged_out() {
	// hide #logout button
	// TODO show a different logged-out screen, or just go to https://allemande.ai

	const $logout = $id('logout');
	if ($logout) { $logout.style.display = "none"; }
}

/*
async function who() {
	// TODO use user info from cookie instead of asking the server
	const response = await fetch('/x/whoami', {
		method: 'POST',
		headers: {
			"Content-Type": "application/json",
		},
		body: JSON.stringify({
			room: room,
		}),
	});

	if (!response.ok) {
		logged_out();
		return;
	}

	const data = await response.json();

	if (data.error) {
		alert(data.error);
		return;
	}

	user = data.user;
	admin = data.admin;

	const $user = $id('user');
	$user.innerText = user;

	if (admin) {
		for (const $e of $$(".admin")) {
			$e.style.display = "block";
		}
	}
	load_user_styles();
}
*/

// hash change ---------------------------------------------------------------

let new_hash;
let new_title;

function query_to_title(query) {
	return query;
}

function query_to_hash(query) {
	return '#'+query.replace(/ /g, '+');
}

function set_title_hash(query) {
	console.log("setting title hash", query);
	new_hash = query_to_hash(query);
	new_title = query_to_title(query);
	location.hash = new_hash;
	$title.innerText = new_title;
}

function on_hash_change() {
	$title.innerText = query_to_title(hash_to_query(location.hash));
	let h = location.hash;
	console.log("hash change", h, location, location.url);
	if (h == "" || h == "#") {
		h = "#" + DEFAULT_ROOM;
	}
	if (h != new_hash && h == "#-") {
		clear_messages_box();
	}
	if (h != new_hash) {
		let query = hash_to_query(h);
		$room.value = query;
		set_room();
	}
}

function hash_to_query(hash) {
	let query = hash.replace(/\+|%20/g, ' ');
	if (query.length) {
		query = query.substr(1);
	}
	return query;
}

function setup_file_input_label() {
}

function push_notifications() {
}

function leave_room() {
	console.log("leaving room");
	// the following doesn't work reliably, so we're going out out
	if (room == "-")
		set_room("");
	else
		set_room("-");
}

function change_room() {
	console.log("changing room");
	if ($room === document.activeElement) {
		leave_room();
	} else {
		$room.focus();
		$room.select();
	}
	return false;
}

// room numbers --------------------------------------------------------------

function room_set_number(n) {
	if (n === "") {
		room = room.replace(/(.*\D|)(\d+)(\D.*|)$/, "$1$3");
		room = room.replace(/\/+$/, "");
		set_room(room);
	}
	if (n < 0) {
		n = 0
	}
	if (n > MAX_ROOM_NUMBER) {
		n = MAX_ROOM_NUMBER;
	}
	set_room(room.replace(/\d+|$/, n));
}

function room_get_number() {
	return room.match(/\d+$/);
}

function room_random() {
	room_set_number(Math.floor(Math.random() * (MAX_ROOM_NUMBER+1)));
}

function room_next() {
	let num = room_get_number();
	if (num === null && !room.match(/\/$/)) {
		num = "/0";
	} else {
		num = +num + 1;
	}
	room_set_number(num);
}

function room_prev() {
	let num = room_get_number();
	if (num == 0 && room.match(/\/0+$/)) {
		return room_set_number("");
	} else if (num === null) {
		return;
	} else if (num == 0) {
		num = ""
	} else {
		num -= 1;
	}
	room_set_number(num);
}



// TODO use something like a Makefile to handle events and avoid loops

// keyboard shortcuts --------------------------------------------------------
// use mousetrap.js   -- Copilot suggestion <3

function keyboard_shortcuts() {
	// TODO: some way to access these features from mobile?  maybe swipe gestures?
	Mousetrap.bind("esc", change_room);
	Mousetrap.bind("ctrl+.", room_next);
	Mousetrap.bind("ctrl+,", room_prev);
	Mousetrap.bind("ctrl+/", room_random);
	Mousetrap.bind("ctrl+'", () => room_set_number(""));
	Mousetrap.bind("ctrl+;", change_room);
}

// reload the page -----------------------------------------------------------

let reloading = false;
function reload_page() {
	if (reloading)
		return;
	reloading = true;
	console.log("reloading page");
	location.reload();
}

// handle messages from the messages iframe ----------------------------------

function handle_message(ev) {
	console.log("handle_message", ev);
	if (ev.origin != ROOMS_URL) {
		console.log("ignoring message from", ev.origin);
		return;
	}

	$content.focus();

	// detect F5 or ctrl-R to reload the page
	console.log(ev.data.type, ev.data.key, ev.data.ctrlKey);
	if (ev.data.type == "keydown" && (ev.data.key == "F5" || ev.data.ctrlKey && ev.data.key.toLowerCase() == "r")) {
		reload_page();
		return;
	}

	// sending on the event cannot enter text in the input,
	// but it's useful for other events we handle such as ctrl-.
	ev.data.view = window;
	ev.data.bubbles = true;
	ev.data.cancelable = true;

	console.log("dispatching", ev.data.type, "event");
	if (ev.data.type == "keypress" || ev.data.type == "keydown") {
		// can we simulate this same keypress on this document?
		// ev.data.key, ev.data.ctrlKey, ev.data.altKey, ev.data.shiftKey;
		const okay = $content.dispatchEvent(new KeyboardEvent(ev.data.type, ev.data));
		console.log("dispatched", ev.data.type, "event", okay);
	}
}

// Register service worker ---------------------------------------------------

let sw_registration;
let sw_message_channel;

function handle_sw_message(event) {
	if (event.data.type == 'APP_INFO') {
		VERSION = event.data.version;
		$id("debug").value = VERSION;
	}
}

function sw_updatefound() {
	const newWorker = sw_registration.installing;

	// Listen for state changes on the new service worker
	newWorker.addEventListener('statechange', sw_statechange);
}

function sw_statechange(ev) {
	if (ev.target.state === 'activated')
		reload_page();
}

async function register_service_worker() {
	if (!'serviceWorker' in navigator)
		return;
	try {
		sw_registration = await navigator.serviceWorker.register('/service_worker.js');
		console.log('ServiceWorker registration successful');
	} catch (err) {
		console.error('ServiceWorker registration failed: ', err);
		return;
	}

	await navigator.serviceWorker.ready;

	sw_registration.addEventListener('updatefound', sw_updatefound);
	sw_registration.update();

	// Request the app version from the service worker
	sw_message_channel = new MessageChannel();
	sw_registration.active.postMessage({type: 'PORT_INITIALIZATION'}, [
		sw_message_channel.port2,
	]);
	sw_message_channel.port1.onmessage = handle_sw_message;
	sw_message_channel.port1.postMessage('getAppInfo');
}

// Handle notification permissions -------------------------------------------

async function notify_clicked() {
	if (!('Notification' in window)) {
		console.error('This browser does not support notifications');
		return;
	}

	const permission = await Notification.requestPermission();
	if (permission === 'granted') {
		const registration = await navigator.serviceWorker.ready;
		const subscription = await registration.pushManager.subscribe({
			userVisibleOnly: true,
			applicationServerKey: 'YOUR_VAPID_PUBLIC_KEY' // You'll need to replace this
		});

		// Send subscription to server
		await fetch('/x/subscribe', {
			method: 'POST',
			headers: {
				'Content-Type': 'application/json',
			},
			body: JSON.stringify(subscription)
		});

		document.getElementById('notify').textContent = 'notifications on';
	}
}

// authentication ------------------------------------------------------------

function authChat() {
	$on($id('logout'), 'click', logoutChat);
	userData = getJSONCookie('user_data');
	if (!userData)
		throw new Error('Setup error: Not logged in');
	console.log('username:', userData.username);

	return userData.username;
}

// set the user button text and href -----------------------------------------

function setup_user_button() {
	const $user = $id('user');
	$user.innerText = user;
	if (room == user)
		$user.href = '/' + query_to_hash(DEFAULT_ROOM);
	else
		$user.href = '/' + query_to_hash(user);
}

// drag to resize the input row ----------------------------------------------

let resizeStartY, resizeStartHeight;

function initDrag(e) {
	e.preventDefault();
	console.log("initDrag");
	resizeStartY = e.clientY || e.touches[0].clientY;
	resizeStartHeight = $inputrow.offsetHeight;
	document.addEventListener('mousemove', doDrag);
	document.addEventListener('mouseup', stopDrag);
	document.addEventListener('touchmove', doDrag);
	document.addEventListener('touchend', stopDrag);
	$messages_overlay.style.display = "block";
}

function doDrag(e) {
	e.preventDefault();
	const clientY = e.clientY || e.touches[0].clientY;
	$inputrow.style.flexBasis = (resizeStartHeight + resizeStartY - clientY) + 'px';
}

function stopDrag(e) {
	e.preventDefault();
	console.log("stopDrag");
	document.removeEventListener('mousemove', doDrag);
	document.removeEventListener('mouseup', stopDrag);
	document.removeEventListener('touchmove', doDrag);
	document.removeEventListener('touchend', stopDrag);
	$messages_overlay.style.removeProperty('display');
}

// file attachments ----------------------------------------------------------

// plan:
// 1. user clicks on the attach button
// 2. user selects a file
// 3. file is uploaded to the server
// 4. server responds with a URL
// 5. URL is inserted into the message box as markdown or HTML (link, image, audio, video)
// 6. user sends the message
// 7. server receives the message and the URL

function attach_clicked() {
	$id('files').click();
}

function files_changed(ev) {
	const files = ev.target.files;
	console.log("files_changed", files);
	for (const file of files) {
		console.log("file", file);
		upload_file(file);  // async, we're not waiting for it
	}
	// clear the file input so we can upload the same file again
	ev.target.value = '';
}

async function upload_file(file) {
	// upload in the background using fetch
	console.log("upload_file", file);

	const formData = new FormData();
	formData.append('room', room);
	formData.append('file', file);

	const response = await fetch('/x/upload', {
		method: 'POST',
		body: formData,
	});

	if (!response.ok) {
		// flash the attach button red
		await flash($id('attach'), 'error');
		return;
	}

	const data = await response.json();
	console.log("upload_file response", data);

	const { name, url, medium, markdown } = data;

	// make sure the message content ends with whitespace
	if (!/\s$/.test($content.value)) {
		$content.value += "\n";  // TODO this kills undo
	}

	$content.value += markdown;
}

// main ----------------------------------------------------------------------

function chat_main() {
	set_debug(DEBUG);
	user = authChat();
	load_user_styles();
	on_hash_change();

	$on($id('send'), 'click', send);
//	$on($id('clear'), 'click', clear);
//	$on($content, 'keypress', message_keypress);
	$on($content, 'keydown', message_keydown);
	$on($content, 'input', message_changed);
	message_changed();
	$on($room, 'keypress', room_keypress);
	$content.focus();
	$on($room, 'change', () => set_room());
	$on(window, 'hashchange', on_hash_change);
//	$on($messages, 'scroll', messages_scrolled);
	setup_file_input_label();
	$on($('label.attach > button'), 'click', attach_clicked);
	$on($id('files'), 'change', files_changed);
	push_notifications();
	// scroll_to_bottom();
	keyboard_shortcuts();
	$on(window, 'message', handle_message);
//	$on($id('user'), 'click', set_room_user);
//	$on($id('logout'), 'click', logoutChat);
	$on($id('notify'), 'click', notify_clicked);
	$on($id('resizer'), 'mousedown', initDrag);
	$on($id('resizer'), 'touchstart', initDrag);
	register_service_worker();
}
