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
let admin = false;

const ROOMS_URL = location.protocol + "//" + location.host.replace(/^chat\b/, "rooms")
const MAX_ROOM_NUMBER = 1e3; // 1e12;
const DEFAULT_ROOM = 'Ally Chat';
const global_admins = ['sam'];


// utility functions ---------------------------------------------------------

function set_debug(debug) {
	DEBUG = debug;
	console.log = DEBUG ? console.log : () => {};
	$id("debug").style.display = DEBUG ? "block" : "none";
}

async function flash($el, className) {
	$el.classList.add(className);
	await $wait(300);
	$el.classList.remove(className);
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

	const error = async (error_message) => {
		console.error(error_message);
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

// handle enter key press ----------------------------------------------------

/*
// Old code where enter sends, and shift-enter for newline,
// but it does not work on mobile. Maybe detect mobile vs PC.
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
	if ($content.value == "")
		$id('send').textContent = "poke";
	else
		$id('send').textContent = "send";
}

// change room ---------------------------------------------------------------

function messages_iframe_set_src(url) {
	$messages_iframe.contentWindow.location.replace(url);
}

function reload_messages() {
	reload_page();
	// because the following does not work reliably...
	// clear_messages_box();
	// setTimeout(() => set_room(), 1);
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
	setup_admin();
}

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

function file_clicked() {
	$id('files').click();
}

async function files_changed(ev) {
	const files = ev.target.files;
	// clear the file input so we can upload the same file again
	console.log("files_changed", files);
	await upload_files(files);
	ev.target.value = '';
	set_controls();
}

async function upload_files(files) {
	// upload one file at a time, in order
	for (const file of files) {
		await upload_file(file);
	}
}

async function upload_file(file, filename) {
	// upload in the background using fetch
	console.log("upload_file", file);

	const formData = new FormData();
	formData.append('room', room);
	formData.append('file', file, filename);

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

	// TODO messing with the textarea value kills undo

	// make sure the message content ends with whitespace
	if (/\S$/.test($content.value)) {
		$content.value += "\n";
	}

	$content.value += markdown;
	message_changed();
}

// admin functions -----------------------------------------------------------

function setup_admin() {
	// if first component of room path split on commas contains username,
	// or user is a global admin, then user is an admin here
	const components = room.split('/');
	const top_dir = components[0];
	admin = global_admins.includes(user) || top_dir.split(',').includes(user);
	if (admin)
		document.body.classList.add('admin');
	else
		document.body.classList.remove('admin');
}

async function clear(ev, op) {
	if (!op)
		op = "clear";

	console.log("clear", op);

	let confirm_message = "";
	if (op === "clear")
		confirm_message = "Clear the chat?\nThis cannot be undone.";
	else if (op === "rotate")
		confirm_message = "Save and clear the first have of the chat?";
	else if (op === "archive")
		confirm_message = "Save and clear the chat?";
	else
		throw new Error("invalid op: " + op);

	if (!confirm(confirm_message))
		return;

	ev.preventDefault();
	const formData = new FormData();
	formData.append('room', room);
	formData.append('op', op);

	const error = async (error_message) => {
		console.error(error_message);
		await flash($id(op), 'error');
	};

	const response = await fetch('/x/clear', {
		method: 'POST',
		body: formData,
	});

	if (!response.ok) {
		await error(`${op} failed`);
		return;
	}

	const data = await response.json();

	if (data.error) {
		await error(data.error);
		return;
	}

	set_controls();

	// TODO should clear immediately for other users too, not just the current user
	// reload_messages();
}

async function rotate(ev) {
	await clear(ev, "rotate");
}

async function archive(ev) {
	await clear(ev, "archive");
}

async function undo(ev) {
	console.log("undo", op);

	ev.preventDefault();
	const formData = new FormData();
	formData.append('room', room);

	const error = async (error_message) => {
		console.error(error_message);
		await flash($id("undo"), 'error');
	};

	const response = await fetch('/x/undo', {
		method: 'POST',
		body: formData,
	});

	if (!response.ok) {
		await error(`undo failed`);
		return;
	}

	const data = await response.json();

	if (data.error) {
		await error(data.error);
		return;
	}

	// TODO should clear immediately for other users too, not just the current user
	// reload_messages();
}

// input controls ------------------------------------------------------------

function set_controls(id) {
	$('#inputrow > .controls:not(.hidden)').classList.add('hidden');
	$id(id || "input_main").classList.remove('hidden');
}

// main ----------------------------------------------------------------------

function chat_main() {
	set_debug(DEBUG);
	user = authChat();
	load_user_styles();
	on_hash_change();

	$on($id('send'), 'click', send);
	$on($id('add'), 'click', () => set_controls('input_add'));
	$on($id('edit'), 'click', () => set_controls('input_edit'));

	$on($id('undo'), 'click', undo);
	$on($id('clear'), 'click', clear);
	$on($id('archive'), 'click', archive);
	$on($id('rotate'), 'click', rotate);
	$on($id('edit_cancel'), 'click', () => set_controls());

	$on($id('file'), 'click', file_clicked);
	$on($id('files'), 'change', files_changed);
	$on($id('add_cancel'), 'click', () => set_controls());

	$on($content, 'keydown', message_keydown);
	$on($content, 'input', message_changed);
	message_changed();
	$on($room, 'keypress', room_keypress);
	$content.focus();
	$on($room, 'change', () => set_room());
	$on(window, 'hashchange', on_hash_change);
	keyboard_shortcuts();
	$on(window, 'message', handle_message);
	$on($id('resizer'), 'mousedown', initDrag);
	$on($id('resizer'), 'touchstart', initDrag);

	register_service_worker();
	notify_main();
	record_main();
}
