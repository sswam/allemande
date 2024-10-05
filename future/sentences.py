import nltk
from nltk.tokenize import sent_tokenize
import re

nltk.download('punkt')

def add_sentence_spans(text):
	sentences = sent_tokenize(text)
	result = text
	for sentence in sentences:
		escaped = re.escape(sentence)
		result = re.sub(f"(?<!<span class=\"sentence\">){escaped}(?!</span>)",
						f"<span class=\"sentence\">{sentence}</span>",
						result)
	return result

# Example usage
text = "Hello, Mr. Bean! How are you today? It's a nice day, isn't it?"
print(add_sentence_spans(text))

This Python version uses NLTK's `sent_tokenize` function, which is also very reliable for sentence segmentation. You would need to install NLTK (`pip install nltk`) and download the 'punkt' tokenizer data before using this script.
