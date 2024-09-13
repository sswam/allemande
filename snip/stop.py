To make the model stop generating when it produces "\n\n", you'll need to modify the generation process rather than the model loading. The model loading code you've provided is correct for initializing the model, but the stopping condition needs to be implemented in the text generation step.

Here's an example of how you can implement this using the `StoppingCriteria` class from the `transformers` library:

```python
import transformers
import torch
from transformers import StoppingCriteria, StoppingCriteriaList

# First, load the model as you've shown
model = transformers.LlamaForCausalLM.from_pretrained(
    model_path,
    device_map=device_map,
    torch_dtype=torch.float16,
    max_memory = { 0: "24GB" },
    low_cpu_mem_usage=True,
    cache_dir="cache"
).cuda()

# Create a custom stopping criteria
class DoubleNewlineStoppingCriteria(StoppingCriteria):
    def __init__(self, tokenizer):
        self.tokenizer = tokenizer

    def __call__(self, input_ids: torch.LongTensor, scores: torch.FloatTensor, **kwargs) -> bool:
        if input_ids.shape[-1] < 2:
            return False
        last_tokens = input_ids[0][-2:].tolist()
        return self.tokenizer.decode(last_tokens) == "\n\n"

# Initialize the tokenizer
tokenizer = transformers.LlamaTokenizer.from_pretrained(model_path)

# Create an instance of the stopping criteria
stopping_criteria = DoubleNewlineStoppingCriteria(tokenizer)

# When generating text, use the stopping criteria
input_text = "Your input text here"
input_ids = tokenizer.encode(input_text, return_tensors="pt").to(model.device)

output = model.generate(
    input_ids,
    max_length=100,
    stopping_criteria=StoppingCriteriaList([stopping_criteria]),
    # Other generation parameters as needed
)

generated_text = tokenizer.decode(output[0], skip_special_tokens=True)
print(generated_text)
```

This code does the following:

1. Loads the model as you originally specified.
2. Defines a custom `DoubleNewlineStoppingCriteria` class that checks for "\n\n" in the generated text.
3. Initializes the tokenizer.
4. Creates an instance of the stopping criteria.
5. When generating text, it uses this stopping criteria in the `generate` method.

This approach will stop the text generation as soon as "\n\n" is generated. Note that you may need to adjust the tokenizer initialization depending on your specific model and requirements.


