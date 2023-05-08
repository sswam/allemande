var $head = $('head');
var $room = $id('room');
var $content = $id('content');
var $messages = $id('messages');
var $form = $id('form');
var $title = $('title');

var room;
var user;
var admin;
var data_raw = '';

const ROOMS_URL = location.protocol + "//" + location.host.replace(/^chat\b/, "rooms")
const MAX_ROOM_NUMBER = 1e3; // 1e12;
const DEFAULT_ROOM = 'chat';


// send a message ------------------------------------------------------------

async function send(ev) {
	ev.preventDefault();
	// TODO upload attachments

	var formData = new FormData($form);
	var message = $content.value;
	$content.value = "";
//        var filenames = $('#filenames').val();
//	var attached = $('#attached').val();
//	var old_files = clear_attachments();

	// use DOM fetch instead of jquery

	const response = await fetch('/x/post', {
		method: 'POST',
		body: formData,
	});

	const data = await response.json();

	if (data.error) {
		alert(data.error);
		return;
	}

//	console.log(data);

	// scroll_to_bottom();

//	$.ajax({
//		url: '/x/chat',
//		type: 'POST',
//		data: formData,
//                async: true,
//                cache: false,
//                contentType: false,
//                processData: false,
//		success: function(data) {
//			var length = +data;
//			if (length < data_raw.length) {
//				clear_messages_box();
//			}
//			poll();
//		},
//	}).fail(function(xhr, textStatus, errorThrown) {
//        	console.log(errorThrown, textStatus, xhr.responseText);
//		alert("failed: send")
//		$content.val(message);
//		$('#filenames').val(filenames);
//		$('#attached').val(attached);
//		$('#files').replaceWith($(old_files));
//	});
}

function clear() {
}


// handle enter key press ----------------------------------------------------

function message_keypress(ev) {
        if (ev.keyCode == 13 && !ev.shiftKey) {
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


// change room ---------------------------------------------------------------

function clear_messages_box() {
	console.log("clearing messages box");
	$messages.src = "about:blank";  // This doesn't always work in Firefox
	data_raw = '';
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
	who();
	const room_stream_url = ROOMS_URL + "/stream/"+room+".html";
	console.log("setting $messages.src to", room_stream_url);
	$messages.src = room_stream_url;
}


// user info and settings ----------------------------------------------------

function load_user_styles() {
	const $style = $id('user_styles');
	if ($style) { $remove($style); }
	const $link = $create('link');
	$link.id = 'user_styles';
	$link.rel = 'stylesheet';
	$link.type = 'text/css';
	$link.href = '/users/'+user+'/styles.css';
	$head.append($link);
}

async function who() {
	const response = await fetch('/x/whoami', {
		method: 'POST',
		headers: {
			"Content-Type": "application/json",
		},
		body: JSON.stringify({
			room: room,
		}),
	});
	const data = await response.json();
	user = data.user;
	admin = data.admin;
	if (admin) {
		for (const $e of $$(".admin")) {
			$e.style.display = "block";
		}
	}
	load_user_styles();
}

// hash change ---------------------------------------------------------------

let new_hash;
let new_title;

function query_to_title(query) {
	return query;
}

function set_title_hash(query) {
	console.log("setting title hash", query);
	new_hash = '#'+query.replace(/ /g, '+');
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
	var query = hash.replace(/\+|%20/g, ' ');
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
	set_room("-");
//	$room.focus();
//	$room.value = "";
//	room = "";
//	clear_messages_box();
}

function change_room() {
	console.log("changing room");
	if ($room === document.activeElement) {
		leave_room();
	} else {
		$room.focus();
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
	Mousetrap.bind("esc", change_room);
	Mousetrap.bind("ctrl+.", room_next);
	Mousetrap.bind("ctrl+,", room_prev);
	Mousetrap.bind("ctrl+/", room_random);
	Mousetrap.bind("ctrl+'", () => room_set_number(""));
	Mousetrap.bind("ctrl+;", change_room);
}

// handle messages -----------------------------------------------------------

function handle_message(ev) {
	console.log("handle_message", ev);
	if (ev.origin != ROOMS_URL) {
		console.log("ignoring message from", ev.origin);
		return;
	}
//	if (ev.data.type == "change_room") {
//		change_room();
//	}
	$content.focus();
	console.log("dispatching", ev.data.type, "event");
	if (ev.data.type == "keypress" || ev.data.type == "keydown") {
		// can we simulate this same keypress on this document?
		// ev.data.key, ev.data.ctrlKey, ev.data.altKey, ev.data.shiftKey;
		document.dispatchEvent(new KeyboardEvent(ev.type, ev.data));
	}
}

// main ----------------------------------------------------------------------

function main() {
	$on($id('send'), 'click', send);
//	$on($id('clear'), 'click', clear);
	$on($content, 'keypress', message_keypress);
	$on($room, 'keypress', room_keypress);
	$content.focus();
	$on($room, 'change', () => set_room());
	$on(window, 'hashchange', on_hash_change);
	on_hash_change();
//	$on($messages, 'scroll', messages_scrolled);
	setup_file_input_label();
//	$on($('label.attach > button'), 'click', attach_clicked);
	push_notifications();
	// scroll_to_bottom();
	keyboard_shortcuts();
	$on(window, 'message', handle_message);
}

main();
