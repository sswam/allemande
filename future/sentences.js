/**
* Wraps each sentence in the input text with a span element.
* @param {string} text - The input text to process.
* @returns {string} The text with sentences wrapped in span elements.
* @version 1.0.1
*/
function addSentenceSpans(text) {
	// Parse the text using natural language processing
	const doc = nlp(text);

	// Get sentences directly using the sentences() method
	const sentences = doc.sentences();

	let result = '';
	let lastIndex = 0;

	sentences.forEach((sentence) => {
		const { start, end } = sentence.offset();
		result += text.slice(lastIndex, start);
		result += `<span class="sentence">${text.slice(start, end)}</span>`;
		lastIndex = end;
	});

	// Add any remaining text
	if (lastIndex < text.length) {
		result += text.slice(lastIndex);
	}

	return result;
}

// Example usage
const text = "This is a sentence. Here's another one. You all know that Mr. Bean is funny.";
const result = addSentenceSpans(text);
console.log(result);
