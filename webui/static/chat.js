// const $ = (selector) => document.querySelector(selector);
const $id = (id) => document.getElementById(id);
const $on = (element, event, handler) => element.addEventListener(event, handler);

var $room = $id('room');
var $message  = $id('message');
//
//function main() {
//	$on($id('send'), 'click', send);
//	$on($id('clear'), 'click', clear);
//	$on($message, 'keypress', message_keypress);
//	$on($room, 'keypress', room_keypress);
//	$message.focus();
//	$on($room, 'change', room_change);
//	$on(window, 'hashchange', on_hash_change);
//	on_hash_change();
//}

// $on(window, 'load', main);
