// status indicator ----------------------------------------------------------

const timeout_seconds = 60;

const CHAT_URL = location.protocol + "//" + location.host.replace(/^rooms\b/, "chat")

let timeout;

function get_status_element() {
	let status = $id('status');
	if (!status) {
		status = $create('div');
		status.id = 'status';
		$append(document.lastChild, status);
	}
	return status;
}

function reload() {
	window.location.reload();
}

function online() {
	clearTimeout(timeout);
	timeout = setTimeout(offline, 1000 * timeout_seconds);
	const status = get_status_element();
//	status.innerText = '🔵';
	status.innerText = '';
}

function offline() {
	const status = get_status_element();
	status.innerText = '🔴';
	document.addEventListener('mouseenter', reload)
}

function ready_state_change() {
	if (document.readyState !== 'loading') {
		offline();
	}
}

online();

$on(document, 'readystatechange', ready_state_change);


// scrolling to the bottom ---------------------------------------------------

let messages_at_bottom = true;
let messages_height_at_last_scroll;

function is_at_bottom($e) {
//	console.log($e.scrollHeight, $e.scrollTop, $e.offsetHeight);
//	console.log($e.scrollHeight - $e.scrollTop - $e.offsetHeight);
	return (Math.abs($e.scrollHeight - $e.scrollTop - $e.offsetHeight) < 1);
}

function scroll_to_bottom() {
	var $e = $('html');
	$e.scrollTop = $e.scrollHeight;
	messages_height_at_last_scroll = $e.scrollHeight;
}

function messages_scrolled() {
	var $e = $('html');
	if (messages_at_bottom) {
		var messages_height = $e.scrollHeight;
		if (messages_height != messages_height_at_last_scroll) {
			messages_height_at_last_scroll = messages_height;
			scroll_to_bottom($e)
		}
	}
	messages_at_bottom = is_at_bottom($e);
}

function check_for_new_content(mutations) {
	let new_content = false;
	for (const mutation of mutations) {
		if (mutation.type != 'childList') {
			continue;
		}
		for (const node of mutation.addedNodes) {
			if (node.nodeType == Node.ELEMENT_NODE && node.tagName == 'DIV' && node.classList.contains('content')) {
				return true;
			}
		}
	}
	return false;
}

function mutated(mutations) {
	if (check_for_new_content(mutations)) {
		online();
	}
	messages_scrolled();
}

new MutationObserver(mutated).observe($('html'), { childList: true, subtree: true });

$on(window, 'scroll', messages_scrolled);

// keyboard shortcuts --------------------------------------------------------
// use mousetrap.js   -- Copilot suggestion <3

//function change_room() {
//	window.parent.postMessage({ type: 'change_room' }, CHAT_URL);
//	return false;
//}

function relay_event(ev) {
//	console.log("relay_event", ev);
	const copy = {
		type: ev.type,
		key: ev.key,
		code: ev.code,
		keyCode: ev.keyCode,
		ctrlKey: ev.ctrlKey,
		altKey: ev.altKey,
		shiftKey: ev.shiftKey,
		metaKey: ev.metaKey,
	};
	window.parent.postMessage(copy, CHAT_URL);
}

function keyboard_shortcuts() {
	// Mousetrap.bind('esc', change_room);
	// handle any keypress
	$on(document, 'keypress', relay_event);
	$on(document, 'keydown', relay_event);
}

keyboard_shortcuts();
