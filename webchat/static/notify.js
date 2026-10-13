// Handle notification permissions -------------------------------------------

let icons;

async function notify_clicked() {
	const permission = await Notification.requestPermission();
	if (permission !== 'granted') {
		console.error('Permission to display notifications was denied');
		document.getElementById('notify').textContent = 'notify -';
		return;
	}

	const registration = await navigator.serviceWorker.ready;
	const subscription = await registration.pushManager.subscribe({
		userVisibleOnly: true,
		applicationServerKey: ALLYCHAT_WEBPUSH_VAPID_PUBLIC_KEY,
	});

	console.log('Subscribed to push notifications:', subscription);

	// Send subscription to server
	await fetch('/x/subscribe', {
		method: 'POST',
		headers: {
			'Content-Type': 'application/json',
		},
		body: JSON.stringify({
			subscription: subscription,
			room: room,
		})
	});

	document.getElementById('notify').textContent = 'notify +';
}

function notify_check_support() {
	return 'serviceWorker' in navigator && 'PushManager' in window;
}

function notify_show_status(room) {
	const status = 0;   // TODO!  off / me / all
	const status_text = ["off", "me", "all"][status];
	const extra_text = ["", " - when mentioned", " - on any message"][status];
	const icon = "notify_" + status_text;
	const text = "notify: " + status_text + extra_text;
	const $notify = $id('notify');
	$notify.innerHTML = icons[icon];
	setTitle($notify, text);
}

// TODO will need a list of all watched pages somewhere, text file sounds good, to edit

function notify_main(_icons) {
	icons = _icons;
	if (!notify_check_support()) {
		console.error('This browser does not support push notifications');
		$id('notify').classList.add('hidden');
		return;
	}
	$on($id('notify'), 'click', notify_clicked);
	notify_show_status(null);  // FIXME
}

// TODO check if permission already granted / subscription already exists
// TODO if already subscribed, we need to just pass the room name
// TODO enable to unsubscribe from a room
// TODO enable to cancel subscription entirely
// TODO possibly a UI to manage subscriptions
// TODO possibly a UI to manage notification settings

// TODO what happens if I create a subscription, then it gets lost during debugging?
