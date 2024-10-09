
I want to work with llama models and others in safetensors format. Can you show me what a custom inference loop might look like using pytorch? Or should we hack transformers instead?

This isn't directly supported by the Hugging Face Transformers library. You'd need to implement custom logic to:

1. Detect repeated sequences in the output
2. Backtrack to a previous state
3. Temporarily adjust the temperature
4. Continue generation

You can achieve this by:

1. Using the `generate()` method with `return_dict_in_generate=True` to access intermediate states
2. Implementing your own sequence detection and backtracking logic
3. Creating a custom stopping criteria to interrupt generation when needed
4. Resuming generation with adjusted parameters

While possible, it's complex and may require significant custom code. Consider building a custom inference loop for more control.

You're right that building a custom inference loop can provide more control and flexibility, especially for advanced techniques like the one you described. Here's an example of what a custom inference loop might look like using PyTorch for a LLaMA-style model in safetensors format:

```python
import torch
from safetensors import safe_open
from transformers import AutoTokenizer, LlamaForCausalLM, LlamaConfig

# Load the model and tokenizer
model_path = "path/to/your/model.safetensors"
config = LlamaConfig.from_pretrained("path/to/config.json")
tokenizer = AutoTokenizer.from_pretrained("path/to/tokenizer")

# Load the model weights
model = LlamaForCausalLM(config)
with safe_open(model_path, framework="pt", device="cuda") as f:
    for k in f.keys():
        model.state_dict()[k].copy_(f.get_tensor(k))

model.to("cuda")
model.eval()

# Inference function
def generate(prompt, max_length=100, temperature=0.7, top_k=50, top_p=0.9):
    input_ids = tokenizer.encode(prompt, return_tensors="pt").to("cuda")
    past_key_values = None
    output_ids = input_ids.clone()

    for _ in range(max_length):
        with torch.no_grad():
            if past_key_values is None:
                outputs = model(input_ids=output_ids)
            else:
                outputs = model(input_ids=output_ids[:, -1:], past_key_values=past_key_values)

            logits = outputs.logits[:, -1, :] / temperature
            past_key_values = outputs.past_key_values

            # Apply top-k and top-p filtering
            top_k_logits, top_k_indices = torch.topk(logits, top_k)
            probs = torch.softmax(top_k_logits, dim=-1)
            cumulative_probs = torch.cumsum(probs, dim=-1)
            top_p_mask = cumulative_probs <= top_p
            top_p_mask[..., -1] = True
            filtered_logits = top_k_logits * top_p_mask.float()

            # Sample from the filtered distribution
            next_token = torch.multinomial(torch.softmax(filtered_logits, dim=-1), num_samples=1)
            next_token = top_k_indices.gather(-1, next_token)

            output_ids = torch.cat([output_ids, next_token], dim=-1)

            # Check for end of generation
            if next_token.item() == tokenizer.eos_token_id:
                break

    return tokenizer.decode(output_ids[0], skip_special_tokens=True)

# Example usage
prompt = "Once upon a time"
generated_text = generate(prompt)
print(generated_text)
```

This custom inference loop allows you to:

1. Load a model from safetensors format
2. Implement your own generation logic
3. Apply temperature scaling, top-k, and top-p filtering
4. Control the generation process step by step

You can extend this basic loop to implement more advanced features like:

- Detecting repeated sequences
- Backtracking to previous states
- Dynamically adjusting parameters during generation
- Implementing custom stopping criteria

While this approach gives you more control, it also requires more work to implement and maintain. The trade-off is between flexibility and ease of use. If you need very specific behavior that's not easily achievable with the Hugging Face Transformers library, a custom inference loop might be the way to go. Otherwise, you might consider extending the Transformers library's generation functions to suit your needs.

