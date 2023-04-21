// Utility functions, by Github Copilot.

const $ = (selector) => document.querySelector(selector);
const $$ = (selector) => document.querySelectorAll(selector);
const $id = (id) => document.getElementById(id);
const $create = (element) => document.createElement(element);
const $text = (text) => document.createTextNode(text);
const $attr = (element, attribute, value) => element.setAttribute(attribute, value);
const $append = (parent, child) => parent.appendChild(child);
const $remove = (element) => element.parentNode.removeChild(element);
const $replace = (oldElement, newElement) => oldElement.parentNode.replaceChild(newElement, oldElement);
const $empty = (element) => element.innerHTML = '';
const $on = (element, event, handler) => element.addEventListener(event, handler);
const $off = (element, event, handler) => element.removeEventListener(event, handler);
const $dispatch = (element, event) => element.dispatchEvent(new Event(event));
const $animate = (element, animation, callback) => {
	element.classList.add('animated', animation);
	element.addEventListener('animationend', () => {
		element.classList.remove('animated', animation);
		if (callback) callback();
	});
}
const $wait = (time) => new Promise((resolve) => setTimeout(resolve, time));
const $waitUntil = (condition, time) => new Promise((resolve) => {
	const interval = setInterval(() => {
		if (condition()) {
			clearInterval(interval);
			resolve();
		}
	}, time);
});
const $waitUntilElement = (selector, time) => $waitUntil(() => $(selector), time);
const $waitUntilElementRemoved = (selector, time) => $waitUntil(() => !$(selector), time);
const $waitUntilElementVisible = (selector, time) => $waitUntil(() => $(selector).offsetWidth > 0 && $(selector).offsetHeight > 0, time);
const $waitUntilElementHidden = (selector, time) => $waitUntil(() => $(selector).offsetWidth === 0 && $(selector).offsetHeight === 0, time);
const $waitUntilElementText = (selector, text, time) => $waitUntil(() => $(selector).innerText === text, time);
const $waitUntilElementAttribute = (selector, attribute, value, time) => $waitUntil(() => $(selector).getAttribute(attribute) === value, time);
