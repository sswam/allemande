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

// const ROOMS_URL = "https://rooms-local.ucm.dev";
const ROOMS_URL = "//" + location.host.replace("chat", "rooms")


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
	$messages.src = "about:blank";
	data_raw = '';
}

function set_room() {
	clear_messages_box();
	room = $room.value;
	if (!room)
		return;
	set_title_hash(room);
	who();
	$messages.src = ROOMS_URL + "/stream/"+room+".html";
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
	let new_title = $title.innerText;
	new_title = new_title.replace(/.* - |^/, '');
	if (query != '') {
		new_title = query + ' - ' + new_title;
	}
	return new_title;
}

function set_title_hash(query) {
	new_hash = '#'+query.replace(/ /g, '+');
	new_title = query_to_title(query);
	location.hash = new_hash;
	$title.innerText = new_title;
}

function on_hash_change() {
	$title.innerText = query_to_title(hash_to_query(location.hash));
	let h = location.hash;
	if (h == "" || h == "#") {
		h = "#chat";
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


// main ----------------------------------------------------------------------

function main() {
	$on($id('send'), 'click', send);
//	$on($id('clear'), 'click', clear);
	$on($content, 'keypress', message_keypress);
	$on($room, 'keypress', room_keypress);
	$content.focus();
	$on($room, 'change', set_room);
	$on(window, 'hashchange', on_hash_change);
	on_hash_change();
//	$on($messages, 'scroll', messages_scrolled);
	setup_file_input_label();
//	$on($('label.attach > button'), 'click', attach_clicked);
	push_notifications();
	// scroll_to_bottom();
}

main();
