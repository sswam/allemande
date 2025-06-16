const browserAPI = (typeof browser !== 'undefined' ? browser : chrome);

document.getElementById('clickme').addEventListener('click', () => {
	alert('Hello, world!');
});
