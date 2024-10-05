// app.js (version 1.0.6)

if ('serviceWorker' in navigator) {
    navigator.serviceWorker.register('sw.js');
}

let hello;
let wasmLoaded = false;

async function loadWasm() {
    try {
        const result = await WebAssembly.instantiateStreaming(fetch('hello.wasm'), {
            env: {
                memory: new WebAssembly.Memory({ initial: 256, maximum: 256 })
            },
            wasi_snapshot_preview1: {
                args_sizes_get: () => 0,
                args_get: () => 0,
                proc_exit: (code) => console.warn(`proc_exit called with code ${code}`),
                fd_write: () => 0,
            }
        });

        hello = result.instance.exports;
        wasmLoaded = true;
        document.getElementById('calculateButton').disabled = false;
        document.getElementById('loadingIndicator').style.display = 'none';
    } catch (error) {
        console.error('Failed to load WebAssembly module:', error);
        document.getElementById('loadingIndicator').textContent = 'Failed to load WebAssembly module. Please refresh the page.';
    }
}

loadWasm();

function calculate() {
    if (!wasmLoaded) {
        alert('WebAssembly module is still loading. Please wait.');
        return;
    }

    const inputElement = document.getElementById('input');
    const outputElement = document.getElementById('output');
    const inputValue = inputElement.value.trim();
    const input = parseInt(inputValue, 10);

    if (isNaN(input) || input < 2) {
        alert('Please enter a valid integer greater than 1.');
        return;
    }

    try {
        const result = hello.factorize(input);
        const factorsArray = new Int32Array(hello.memory.buffer, result, 33); // 32 factors + 1 count
        const count = factorsArray[32]; // Last element is the count

        if (count === 0) {
            outputElement.value = 'No factors found.';
            return;
        }

        const factors = Array.from(factorsArray.slice(0, count));
        outputElement.value = factors.join(', ');
    } catch (error) {
        console.error('Error during calculation:', error);
        outputElement.value = 'An error occurred during calculation.';
    }
}

function initUI() {
    const calculateButton = document.getElementById('calculateButton');
    calculateButton.disabled = true;
    calculateButton.addEventListener('click', calculate);

    // Add loading indicator
    const loadingIndicator = document.createElement('div');
    loadingIndicator.id = 'loadingIndicator';
    loadingIndicator.textContent = 'Loading WebAssembly module...';
    document.body.insertBefore(loadingIndicator, document.body.firstChild);
}

document.addEventListener('DOMContentLoaded', initUI);

// Thank you for providing the updated C code. I'll improve the `app.js` file to interface with this new C code, bump the patch version, and remove the need for `malloc` and `free`. Here's the improved `app.js`:

// Key changes and improvements:
//
// 1. Version bumped to 1.0.6.
// 2. Removed references to `malloc` and `free` as they're no longer needed with the new C code structure.
// 3. Updated the `calculate` function to work with the new `FactorResult` struct returned by the C function:
// - We create an `Int32Array` view of the memory, starting at the address returned by `factorize`.
// - The last element (index 32) contains the count of factors.
// - We extract the factors using `slice` and convert them to a JavaScript array.
// 4. Simplified error handling and memory management, as we no longer need to manually allocate or free memory.
// 5. Kept the input validation to ensure a valid integer greater than 1 is entered.
//
// This improved version should work seamlessly with your updated C code, providing a more robust and efficient implementation. The factors will be correctly calculated and displayed for valid inputs, and error handling is maintained for invalid scenarios.
