

class TokenStoppingCriteria(transformers.StoppingCriteria):
    """
    Custom stopping criteria for text generation.

    This stopping criteria stops the generation when any of the specified stop tokens or stop texts are encountered.
    It can handle single or multiple stop tokens or texts.

    **Usage:**
    stopping_criteria = TokenStoppingCriteria(tokenizer, stop_texts=["\n"])
    stopping_criteria = TokenStoppingCriteria(tokenizer, stop_texts=["\n\n"])
    stopping_criteria = TokenStoppingCriteria(tokenizer, stop_texts=["\n", ".", "?", "!"])

    **Args:**
        tokenizer (PreTrainedTokenizer): The tokenizer used for encoding the stop texts.
        stop_texts (list of str): List of strings to stop generation.

    **Returns:**
        bool: `True` if the stop condition is met, `False` otherwise.
    """

    def __init__(self, tokenizer: transformers.PreTrainedTokenizer, stop_texts: list):
        if not isinstance(stop_texts, list):
            raise ValueError("stop_texts must be a list of strings.")
        if not all(isinstance(text, str) for text in stop_texts):
            raise ValueError("All elements in stop_texts must be strings.")

        self.tokenizer = tokenizer
        self.stop_texts = stop_texts
        self.stop_tokens = [
            tokenizer.encode(text, add_special_tokens=False) for text in stop_texts
        ]

    def __call__(self, input_ids: torch.LongTensor, scores: torch.FloatTensor, **kwargs) -> bool:
        """
        Checks if the stopping condition is met for any sequence in the batch.

        **Args:**
            input_ids (torch.LongTensor): Tensor of input IDs of shape `(batch_size, sequence_length)`.
            scores (torch.FloatTensor): Prediction scores (not used here).

        **Returns:**
            bool: `True` if the stopping condition is met, `False` otherwise.
        """
        batch_size, sequence_length = input_ids.shape

        # Determine the maximum length of stop tokens
        max_token_len = max(len(t) for t in self.stop_tokens) if self.stop_tokens else 0

        for i in range(batch_size):
            sequence = input_ids[i]
            for stop_token in self.stop_tokens:
                token_len = len(stop_token)
                if token_len > sequence_length:
                    continue  # Sequence too short for this stop token
                if sequence[-token_len:].tolist() == stop_token:
                    logger.debug(f"Stop token found: {stop_token} in {sequence}")
                    return True
            # Check for stop_texts in decoded text
            # Decode only the last few tokens to improve efficiency
            decode_len = min(sequence_length, max_token_len * 2)  # Adjust factor as needed
            decoded_sequence = self.tokenizer.decode(sequence[-decode_len:], skip_special_tokens=True)
            for stop_text in self.stop_texts:
                if decoded_sequence.endswith(stop_text):
                    logger.debug(f"Stop text found: {stop_text!r} in {decoded_sequence!r}")
                    return True
        return False

