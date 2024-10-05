class CustomStoppingCriteria(StoppingCriteria):
    def __init__(self, tokenizer):
        self.tokenizer = tokenizer

    def __call__(self, input_ids: torch.LongTensor, scores: torch.FloatTensor, **kwargs) -> bool:
        if input_ids.shape[-1] < 2:
            return False
        last_tokens = input_ids[0][-2:].tolist()
        decoded = self.tokenizer.decode(last_tokens)
        return "\n" in decoded
        # return "\n\n" in decoded or "\n" in decoded or ": " in decoded
