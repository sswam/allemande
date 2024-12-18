// Handle notification permissions -------------------------------------------

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

function notify_main() {
	if (!notify_check_support()) {
		console.error('This browser does not support push notifications');
		$id('notify').classList.add('hidden');
		return;
	}
	$on($id('notify'), 'click', notify_clicked);
}

// TODO check if permission already granted / subscription already exists
// TODO if already subscribed, we need to just pass the room name
// TODO enable to unsubscribe from a room
// TODO enable to cancel subscription entirely
// TODO possibly a UI to manage subscriptions
// TODO possibly a UI to manage notification settings

// TODO what happens if I create a subscription, then it gets lost during debugging?
