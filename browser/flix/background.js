const browserAPI = (typeof browser !== 'undefined' ? browser : chrome);

const minutesFromNow = 1;

browserAPI.alarms.create('openURL', {
	when: Date.now() + (minutesFromNow * 60 * 1000)
});

browserAPI.alarms.onAlarm.addListener((alarm) => {
	if (alarm.name === 'openURL') {
		browserAPI.tabs.create({ url: 'https://chat.allemande.ai' });
	}
});
