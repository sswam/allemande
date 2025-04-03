// app.js (version 0.0.10)

if ("serviceWorker" in navigator) {
	navigator.serviceWorker.register("sw.js");
}

let wasmLoaded = false;

// Module and ccall are provided by Emscripten
Module.onRuntimeInitialized = function() {
	wasmLoaded = true;
	console.log("WebAssembly module loaded");
};

function calculate() {
	if (!wasmLoaded) {
		alert("WebAssembly module is still loading. Please wait.");
		return;
	}

	const inputElement = document.getElementById("input");
	const outputElement = document.getElementById("output");
	const inputValue = inputElement.value.trim();
	const input = parseInt(inputValue, 10);

	if (isNaN(input) || input < 2) {
		alert("Please enter a valid integer greater than 1.");
		return;
	}

	let resultPtr, count, factors;

	try {
		console.log("Calling factorize with input:", input);
		// ccall is provided by Emscripten
		resultPtr = Module._malloc(33 * 4);
		Module.ccall("factorize", null, ["number", "number"], [input, resultPtr]);
		// HEAPU8 is provided by Emscripten
		const resultView = new Int32Array(Module.HEAPU8.buffer, resultPtr, 33);
		count = resultView[32]; // Last element is the count
		factors = Array.from(resultView.slice(0, count));
	} catch (error) {
		console.error("Error during calculation:", error);
		outputElement.value = "An error occurred during calculation.";
	} finally {
		if (resultPtr) {
			Module._free(resultPtr);
		}
	}

	console.log("Result count:", count);

	if (count === 0) {
		outputElement.value = "No factors found.";
		return;
	}

	console.log("Factors:", factors);
	outputElement.value = factors.join(", ");
}

function initUI() {
	const calculateButton = document.getElementById("calculateButton");
	calculateButton.addEventListener("click", calculate);

	// Add loading indicator
	const loadingIndicator = document.createElement("div");
	loadingIndicator.id = "loadingIndicator";
	loadingIndicator.textContent = "Loading WebAssembly module...";
	document.body.insertBefore(loadingIndicator, document.body.firstChild);
}

document.addEventListener("DOMContentLoaded", initUI);
