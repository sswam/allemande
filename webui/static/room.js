// status indicator ----------------------------------------------------------

const timeout_seconds = 60;

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

function online() {
	clearTimeout(timeout);
	timeout = setTimeout(offline, 1000 * timeout_seconds);
	const status = get_status_element();
	status.innerText = '🔵';
}

function offline() {
	const status = get_status_element();
	status.innerText = '🔴';
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
//	console.log("scrolled");
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

new MutationObserver(messages_scrolled).observe($('html'), { childList: true, subtree: true });

$on(window, 'scroll', messages_scrolled);
