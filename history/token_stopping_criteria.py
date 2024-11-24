class TokenStoppingCriteria(transformers.StoppingCriteria):
    def __init__(self, tokenizer, stop_tokens):
        self.tokenizer = tokenizer
        self.stop_tokens = [tokenizer.encode(token, add_special_tokens=False) for token in stop_tokens]

    def __call__(self, input_ids: torch.LongTensor, scores: torch.FloatTensor, **kwargs) -> bool:
        for stop_token in self.stop_tokens:
            if input_ids[0][-len(stop_token):].tolist() == stop_token:
                return True
        return False


class TokenStoppingCriteriaRegexp(transformers.StoppingCriteria):
    def __init__(self, tokenizer, patterns, window_size=32):
        self.tokenizer = tokenizer
        self.patterns = [re.compile(pattern) for pattern in patterns]
        self.window_size = window_size

    def __call__(self, input_ids: torch.LongTensor, scores: torch.FloatTensor, **kwargs) -> bool:
        # Get the last window_size tokens and decode them
        last_tokens = input_ids[0][-self.window_size:].tolist()
        text = self.tokenizer.decode(last_tokens)

        # Check if any of the patterns match
        lines = text.split('\n')
        last_line = lines[-1] if lines else ""

        for pattern in self.patterns:
            # If it's a newline pattern, check directly
            if pattern.pattern == "\n" and text.endswith("\n"):
                return True
            # For other patterns, check against the last line
            elif pattern.search(last_line):
                return True

        return False
