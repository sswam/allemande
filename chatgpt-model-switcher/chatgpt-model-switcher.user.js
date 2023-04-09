// ==UserScript==
// @name         ChatGPT Model Switcher
// @namespace    https://ucm.dev/
// @version      0.9
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
	{
		"name": "text-davinci-002-render-sha",
		"label": "Default (GPT-3.5)"
	},
	{
		"name": "text-davinci-002-render-paid",
		"label": "Legacy (GPT-3.5)"
	},
	{
		"name": "gpt-4",
		"label": "GPT-4"
	}
]

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
	chatGPTModelSelect: '#__next button[data-headlessui-state]',
};

const IDS = {
	switcher: 'chatgpt-model-switcher',
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

	// Make sure the model switcher exists in the UI
	const modelSwitcher = $id(IDS.switcher);
	if (!modelSwitcher) return originalRequest;

	// Update the model parameter based on the selected option in the UI
	requestData.model = modelSwitcher.value;

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
		const newModel = $id(IDS.switcher).value;
		const newModelLabel = MODELS.find((model) => model.name === newModel).label;
		element.textContent = MESSAGES.modelChanged + newModelLabel;
	}
};

// Synchronize the custom model switcher with the original model selector.
// Update the custom model switcher's value to match the currently selected
// model in the original model selector.
const syncCustomModelSwitcher = () => {
	const chatGPTModelSelect = $(SELECTORS.chatGPTModelSelect);
	const modelLabel = chatGPTModelSelect.innerText.split("\n")[1];
	const customModelSwitcher = $id(IDS.switcher);

	for (const model of MODELS) {
		if (model.label !== modelLabel) continue;
		customModelSwitcher.value = model.name;
		break;
	}
};

// Initialize the model switcher: Add it to the chat interface, watch the
// original model selector, and watch for the model unavailable message.
const initModelSwitcher = () => {
	if ($id(IDS.switcher)) return;

	const buttons = $(SELECTORS.buttons);

	// Create the model switcher
	const modelSwitcher = $create('select');
	modelSwitcher.id = IDS.switcher;
	modelSwitcher.classList.add('btn', 'flex', 'gap-2', 'justify-center', 'btn-neutral');
	for (const model of MODELS) {
		const option = $create('option');
		option.value = model.name;
		option.textContent = model.label;
		modelSwitcher.appendChild(option);
	}

	// Add the model switcher to the button bar
	buttons.appendChild(modelSwitcher);

	// Initialize a MutationObserver to watch the messages container
	for (const element of $$(SELECTORS.messagesContainer)) {
		new MutationObserver(replaceModelUnavailableMessage).observe(element, { childList: true, subtree: true });
	}
};

let chatGPTModelSelectObserver = null;

// Watch ChatGPT's model selector
const watchChatGPTModelSelect = () => {
	if (chatGPTModelSelectObserver) return;
	const chatGPTModelSelect = $(SELECTORS.chatGPTModelSelect);
	chatGPTModelSelectObserver = new MutationObserver(syncCustomModelSwitcher)
	chatGPTModelSelectObserver.observe(chatGPTModelSelect, { childList: true, characterData: true, subtree: true });
}

// Check if the chat interface has been loaded, and call the
// initModelSwitcher function when it is detected.
const chatInterfaceChanged = (mutationsList, observer) => {
	if ($(SELECTORS.buttons) && $(SELECTORS.messagesContainer)) {
		initModelSwitcher();
	}
	if ($(SELECTORS.chatGPTModelSelect)) {
		watchChatGPTModelSelect();
	}
};

// Observe mutations to the body element, and call the
// initModelSwitcher function when the chat interface is detected.
new MutationObserver(chatInterfaceChanged).observe(document.body, { childList: true, subtree: true });

})();
