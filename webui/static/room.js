// This script shows a status indicator in the chat window.

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
