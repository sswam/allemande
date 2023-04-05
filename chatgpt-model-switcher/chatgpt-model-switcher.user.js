// ==UserScript==
// @name         ChatGPT Model Switcher
// @namespace    https://ucm.dev/
// @version      0.7
// @description  Switch ChatGPT model mid-chat
// @author       GPT-4, GPT-3.5, Copilot, and Sam Watkins <sam@ucm.dev>
// @match        *://chat.openai.com/*
// @grant        none
// ==/UserScript==

// This user script adds a model switcher to the OpenAI chat interface,
// allowing users to switch between different AI models when conversing.

(function () {

'use strict';

// Define various constants, such as available models,
// URLs for API calls, messages, and selectors for DOM elements.

const MODELS = [
	{ label: 'GPT-3.5', name: 'text-davinci-002-render-sha' },
	{ label: 'Legacy ChatGPT', name: 'text-davinci-002-render-paid' },
	{ label: 'GPT-4', name: 'gpt-4' },
];

const URLS = {
	conversation: 'https://chat.openai.com/backend-api/conversation',
};

const MESSAGES = {
	modelUnavailable: "The previous model used in this conversation is unavailable. " +
		"We've switched you to the latest default model",
	modelChanged: 'Now using ',
};

const SELECTORS = {
	buttons: '#__next main form > div div:nth-of-type(1)',
	messagesContainer: '.flex-col.items-center',
	modelUnavailableMessage: '.flex-col.items-center .text-center',
};

const IDS = {
	selector: 'chatgpt-model-switcher-selector',
}

// Utility functions
const $ = (selector) => document.querySelector(selector);
const $$ = (selector) => document.querySelectorAll(selector);
const $id = (id) => document.getElementById(id);
const $create = (element) => document.createElement(element);
const $text = (text) => document.createTextNode(text);

// Update the model parameter in the request body to match the
// selected model in the UI.
const updateModelParameter = (originalRequest) => {
	// Parse the request body
	const requestData = JSON.parse(originalRequest.body);

	// Make sure the request has a model parameter
	if (!requestData.model) return originalRequest;

	// Make sure the model selector exists in the UI
	const modelSelector = $id(IDS.selector);
	if (!modelSelector) return originalRequest;

	// Update the model parameter based on the selected option in the UI
	requestData.model = modelSelector.value;

	// Modify the request to include the updated model parameter
	const updatedRequest = {
		...originalRequest,
		body: JSON.stringify(requestData),
	};

	return updatedRequest;
}

// Check if the request is a conversation request.
const isConversationRequest = (requestArgs) => {
	return	requestArgs[0] &&
		requestArgs[0] === URLS.conversation &&
		requestArgs[1] &&
		requestArgs[1].method === 'POST' &&
		requestArgs[1].body;
};

// Replace the original fetch function with a new function that
// updates the model parameter in the request before sending it.
const originalFetch = window.fetch;
window.fetch = async function () {
	if (isConversationRequest(arguments)) {
		arguments[1] = updateModelParameter(arguments[1]);
	}
	return await originalFetch.apply(this, arguments);
};

// Replace the model unavailable message with a message indicating
// that the model has been changed.
const replaceModelUnavailableMessage = () => {
  for (const element of $$(SELECTORS.modelUnavailableMessage)) {
    if (element.textContent !== MESSAGES.modelUnavailable) continue;
    const newModel = $id(IDS.selector).value;
    const newModelLabel = MODELS.find((model) => model.name === newModel).label;
    element.textContent = MESSAGES.modelChanged + newModelLabel;
  }
};

// Initialize the model switcher by adding a model selector to the
// chat interface, and initializing a MutationObserver to watch for
// the model unavailable message.
const initModelSwitcher = () => {
	const buttons = $(SELECTORS.buttons);

	// Create the model selector
	const modelSelector = $create('select');
	modelSelector.id = IDS.selector;
	modelSelector.classList.add('btn', 'flex', 'gap-2', 'justify-center', 'btn-neutral');
	for (const model of MODELS) {
		const option = $create('option');
		option.value = model.name;
		option.textContent = model.label;
		modelSelector.appendChild(option);
	}

	// Add the model selector to the button bar
	buttons.appendChild(modelSelector);

	// Initialize a MutationObserver to watch the messages container
	for (const element of $$(SELECTORS.messagesContainer)) {
		new MutationObserver(replaceModelUnavailableMessage).observe(element, { childList: true, subtree: true });
	}
};

// Check if the chat interface has been loaded, and call the
// initModelSwitcher function when it is detected.
const chatInterfaceChanged = (mutationsList, observer) => {
	for (const mutation of mutationsList) {
		if (mutation.type === 'childList' && $(SELECTORS.buttons) && $(SELECTORS.messagesContainer)) {
			if (!$id(IDS.selector)) {
				initModelSwitcher();
			}
		}
	}
};

// Observe mutations to the body element, and call the
// initModelSwitcher function when the chat interface is detected.
const observeChatInterface = () => {
	const targetNode = document.body;

	const config = { childList: true, subtree: true };

	const observer = new MutationObserver(chatInterfaceChanged);
	observer.observe(targetNode, config);
};

observeChatInterface();

})();
