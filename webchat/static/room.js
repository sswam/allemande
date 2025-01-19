// status indicator ----------------------------------------------------------

const timeout_seconds = 60;

const CHAT_URL = location.protocol + "//" + location.host.replace(/^rooms\b/, "chat")

let timeout;

function get_status_element() {
	let status = $id('allemande_status');
	if (!status) {
		status = $create('div');
		status.id = 'allemande_status';
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
	document.body.addEventListener('mouseenter', reload, { once: true });
}

function clear() {
	$("div.messages").innerHTML = '';
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

// Keep certain keys in the messages iframe, send others up to the chat window
const keysToKeep = ["Control", "Shift", "Alt", "Meta", "ArrowUp", "ArrowDown", "ArrowLeft", "ArrowRight", "Home", "End", "PageUp", "PageDown"];
const ctrlKeysToKeep = ["c", "a", "f"];

function relay_event(ev) {
	// console.log("relay_event", ev);
	if (keysToKeep.includes(ev.key) || (ev.ctrlKey && ctrlKeysToKeep.includes(ev.key))) {
		return;
	}
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
	ev.preventDefault();
}

function keyboard_shortcuts() {
	// Mousetrap.bind('esc', change_room);
	// handle any keypress
	$on(document, 'keypress', relay_event);
	$on(document, 'keydown', relay_event);
}

keyboard_shortcuts();

// embeds --------------------------------------------------------------------

// when we click an image of class thumb, we convert it to an embed

// embed = `<iframe width="280" height="157" src="https://www.youtube.com/embed/{video_id}" title="{title_enc}" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" allowfullscreen></iframe>`

function embed_click($thumb) {
	const $embed = $thumb.parentNode;
	let iframe_html;
	if ($embed.dataset.site == "youtube") {
		iframe_html = `<iframe width="280" height="157" src="https://www.youtube.com/embed/${$embed.dataset.videoid}?autoplay=1" title="${$thumb.alt}" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share; fullscreen" allowfullscreen></iframe>`;
	} else if ($embed.dataset.site == "pornhub") {
		iframe_html = `<iframe src="https://www.pornhub.com/embed/${$embed.dataset.videoid}" frameborder="0" width="280" height="157" scrolling="no" allowfullscreen></iframe>`;
	}
	// replace $thumb element with iframe_html
	if (iframe_html == undefined) {
		return;
	}
	const $node = document.createElement('div');
	$node.innerHTML = iframe_html;
	$embed.replaceChild($node.firstChild, $thumb);
	$node.remove();
}

function click(ev) {
	if (ev.target.classList.contains('thumb') && ev.button == 0) {
		embed_click(ev.target);
		return;
	}
	console.log("ev.button", ev.button);
	// check for img tag, and browse to the src
	if (ev.target.tagName == 'IMG') {
		if (ev.shiftKey) {
			window.open(ev.target.src, '_blank');
		} else if (ev.ctrlKey || ev.metaKey || ev.button === 1) {
			window.open(ev.target.src, '_blank').focus();
		} else {
			window.top.location.href = ev.target.src;
		}
		return;
	}
}

$on(document, 'click', click);
$on(document, 'auxclick', click);
