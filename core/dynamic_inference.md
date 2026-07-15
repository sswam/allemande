## Editing Generated Tokens Mid-Generation

Yes, this is absolutely possible! Here's a breakdown of each approach:

---

## 1. llama_cpp_python

This has the best native support for what you want via **direct KV cache manipulation**.

```python
from llama_cpp import Llama
import ctypes

llm = Llama(model_path="model.gguf", n_ctx=4096)

# Generate some tokens
prompt = "The quick brown fox"
tokens = llm.tokenize(prompt.encode())

# Evaluate tokens to fill KV cache
llm.eval(tokens)

# Get current state - you can save/restore this!
state = llm.save_state()

# Generate a few tokens
generated = []
for _ in range(10):
    token = llm.sample()          # sample next token
    generated.append(token)
    llm.eval([token])

print("Generated:", llm.detokenize(generated))

# --- OPTION 1: Remove generated tokens ---
# Simply restore state to before generation
llm.load_state(state)
# Now continue from original position with modifications

# --- OPTION 2: Remove N tokens from end ---
# llama_cpp exposes n_tokens count
n_to_remove = 3
llm.n_tokens -= n_to_remove   # rewind KV cache pointer
# WARNING: check llama_cpp version; attribute name may vary

# --- OPTION 3: Add extra tokens and continue ---
extra_text = " jumping over"
extra_tokens = llm.tokenize(extra_text.encode(), add_bos=False)
llm.eval(extra_tokens)

# Continue generation from new context
more_tokens = []
for _ in range(20):
    token = llm.sample()
    if token == llm.token_eos():
        break
    more_tokens.append(token)
    llm.eval([token])

print("Continued:", llm.detokenize(more_tokens))
```

### Rewinding with low-level API

```python
# More robust: use the underlying context directly
import llama_cpp

# After generating, rewind by adjusting token count
# This is the key insight - KV cache entries remain but pointer moves back
def rewind_tokens(llm: Llama, n: int):
    """Remove last n tokens from KV cache"""
    llm._ctx.kv_cache_seq_rm(
        seq_id=0,
        p0=llm.n_tokens - n,  # start position
        p1=llm.n_tokens,       # end position  
    )
    llm.n_tokens -= n

def insert_tokens_and_continue(llm: Llama, text: str, max_new: int = 50):
    """Insert text at current position and continue"""
    tokens = llm.tokenize(text.encode(), add_bos=False)
    llm.eval(tokens)
    
    result = []
    for _ in range(max_new):
        token = llm.sample()
        if token == llm.token_eos():
            break
        result.append(token)
        llm.eval([token])
    
    return llm.detokenize(result).decode()
```

---

## 2. HuggingFace Transformers

Transformers supports this via **`past_key_values` / `DynamicCache`** manipulation.

```python
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, DynamicCache

model_name = "meta-llama/Llama-3.2-1B"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(
    model_name, 
    torch_dtype=torch.bfloat16,
    device_map="auto"
)

def generate_with_editable_cache(
    model, tokenizer, prompt: str, n_tokens: int = 10
) -> tuple[list[int], DynamicCache]:
    """Generate tokens, returning them and the cache"""
    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
    input_ids = inputs["input_ids"]
    
    cache = DynamicCache()
    generated_ids = []
    
    current_ids = input_ids
    past_len = 0
    
    for _ in range(n_tokens):
        with torch.no_grad():
            outputs = model(
                input_ids=current_ids,
                past_key_values=cache,
                use_cache=True,
            )
        
        cache = outputs.past_key_values  # updated cache
        next_token = outputs.logits[:, -1, :].argmax(dim=-1, keepdim=True)
        generated_ids.append(next_token.item())
        current_ids = next_token  # only feed new token next iteration
    
    return generated_ids, cache


def remove_tokens_from_cache(cache: DynamicCache, n: int) -> DynamicCache:
    """Remove last n tokens from a DynamicCache"""
    new_cache = DynamicCache()
    for layer_idx in range(len(cache.key_cache)):
        # Shape: [batch, heads, seq_len, head_dim]
        new_cache.key_cache.append(cache.key_cache[layer_idx][:, :, :-n, :])
        new_cache.value_cache.append(cache.value_cache[layer_idx][:, :, :-n, :])
    return new_cache


def insert_text_into_cache(
    model, tokenizer, cache: DynamicCache, 
    text: str, current_token_count: int
) -> tuple[torch.Tensor, DynamicCache]:
    """Insert tokens into cache at current position"""
    extra_ids = tokenizer(text, return_tensors="pt", add_special_tokens=False)
    extra_ids = extra_ids["input_ids"].to(model.device)
    
    # Feed extra tokens through model to update cache
    with torch.no_grad():
        outputs = model(
            input_ids=extra_ids,
            past_key_values=cache,
            use_cache=True,
        )
    
    # Return last token id (for continuing) and updated cache
    last_token = outputs.logits[:, -1:, :].argmax(dim=-1)
    return last_token, outputs.past_key_values


# --- Usage ---
prompt = "The quick brown fox"
generated_ids, cache = generate_with_editable_cache(model, tokenizer, prompt, n_tokens=10)
print("Initial:", tokenizer.decode(generated_ids))

# Remove last 3 tokens
cache_rewound = remove_tokens_from_cache(cache, n=3)
adjusted_ids = generated_ids[:-3]

# Insert different text and continue
last_token, cache_modified = insert_text_into_cache(
    model, tokenizer, cache_rewound,
    text=" leaping gracefully",
    current_token_count=len(adjusted_ids)
)

# Continue generation from modified context
more_ids = []
current = last_token
for _ in range(20):
    with torch.no_grad():
        outputs = model(
            input_ids=current,
            past_key_values=cache_modified,
            use_cache=True,
        )
    cache_modified = outputs.past_key_values
    next_tok = outputs.logits[:, -1, :].argmax(dim=-1, keepdim=True)
    tok_id = next_tok.item()
    if tok_id == tokenizer.eos_token_id:
        break
    more_ids.append(tok_id)
    current = next_tok

print("After edit:", tokenizer.decode(more_ids))
```

---

## 3. Optimized Custom Loop for Your Codebase

Here's how to integrate this into your existing architecture:

```python
from dataclasses import dataclass, field
from typing import Optional
import torch
from llama_cpp import Llama

@dataclass  
class GenerationState:
    """Holds resumable generation state"""
    tokens: list[int] = field(default_factory=list)
    # For gguf: we rely on llm.n_tokens as the KV cache position
    # For transformers: we hold the cache object
    cache: Optional[object] = None  


class EditableGGUFSession:
    """
    Wraps LlamaCpp to support mid-generation token editing.
    Maintains explicit token list alongside KV cache.
    """
    
    def __init__(self, llm: Llama):
        self.llm = llm
        self.tokens: list[int] = []
        self._state_stack: list = []
    
    def reset(self):
        """Clear all context"""
        self.llm.reset()
        self.tokens = []
    
    def eval_text(self, text: str, add_bos: bool = True) -> "EditableGGUFSession":
        """Tokenize and evaluate text into KV cache"""
        new_tokens = self.llm.tokenize(
            text.encode(), 
            add_bos=add_bos and len(self.tokens) == 0
        )
        self.llm.eval(new_tokens)
        self.tokens.extend(new_tokens)
        return self
    
    def generate_n(self, n: int, **sample_kwargs) -> list[int]:
        """Generate n tokens, storing them"""
        generated = []
        for _ in range(n):
            token = self.llm.sample(**sample_kwargs)
            if token == self.llm.token_eos():
                break
            generated.append(token)
            self.tokens.append(token)
            self.llm.eval([token])
        return generated
    
    def push_state(self):
        """Save current state to stack"""
        self._state_stack.append((
            self.llm.save_state(),
            self.tokens.copy()
        ))
        return self
    
    def pop_state(self):
        """Restore last saved state"""
        if not self._state_stack:
            raise RuntimeError("No saved states")
        llm_state, tokens = self._state_stack.pop()
        self.llm.load_state(llm_state)
        self.tokens = tokens
        return self
    
    def remove_last_n_tokens(self, n: int) -> "EditableGGUFSession":
        """
        Remove last n generated tokens from KV cache.
        Uses seq_rm for efficient removal without full re-eval.
        """
        if n > len(self.tokens):
            raise ValueError(f"Cannot remove {n} tokens, only have {len(self.tokens)}")
        
        new_len = len(self.tokens) - n
        
        # Remove from KV cache using low-level API
        self.llm._ctx.kv_cache_seq_rm(
            seq_id=0,
            p0=new_len,
            p1=len(self.tokens),
        )
        self.llm.n_tokens = new_len  # rewind pointer
        self.tokens = self.tokens[:new_len]
        return self
    
    def insert_text(self, text: str) -> "EditableGGUFSession":
        """Insert text at current position (after any removal)"""
        return self.eval_text(text, add_bos=False)
    
    def current_text(self) -> str:
        """Decode all current tokens"""
        return self.llm.detokenize(self.tokens).decode("utf-8", errors="replace")
    
    async def stream_generate(
        self, 
        max_tokens: int = 512,
        stop_strings: list[str] | None = None,
        **sample_kwargs
    ):
        """Async generator yielding text chunks"""
        stop_strings = stop_strings or []
        buffer = ""
        
        for _ in range(max_tokens):
            token = self.llm.sample(**sample_kwargs)
            
            if token == self.llm.token_eos():
                break
            
            self.tokens.append(token)
            self.llm.eval([token])
            
            chunk = self.llm.detokenize([token]).decode("utf-8", errors="replace")
            buffer += chunk
            
            stopped = False
            for stop in stop_strings:
                if stop in buffer:
                    idx = buffer.index(stop)
                    yield buffer[:idx]
                    # Rewind tokens consumed after stop
                    # (approximate - token boundaries may not align)
                    stopped = True
                    break
            
            if stopped:
                break
            
            yield chunk
            await asyncio.sleep(0)  # yield control to event loop


# Integration with your existing collect_response pattern:

async def stream_gguf_editable(
    session: EditableGGUFSession,
    prompt: str, 
    generation_kwargs: dict
) -> AsyncIterator[str]:
    """
    Drop-in replacement for stream_gguf that supports editing.
    Session persists between calls for continued generation.
    """
    generation_kwargs = generation_kwargs.copy()
    max_tokens = generation_kwargs.pop("max_new_tokens", 512)
    stop = generation_kwargs.pop("stop", [])
    
    # Only re-eval prompt if it's different from current context
    current = session.current_text()
    if not prompt.startswith(current):
        session.reset()
        session.eval_text(prompt)
    else:
        # Context is prefix of prompt - just eval the new suffix
        suffix = prompt[len(current):]
        if suffix:
            session.eval_text(suffix, add_bos=False)
    
    # Sample kwargs from generation_kwargs
    sample_kwargs = {}
    for k in ["temperature", "top_p", "top_k", "repeat_penalty"]:
        if k in generation_kwargs:
            sample_kwargs[k] = generation_kwargs[k]
    
    async for chunk in session.stream_generate(
        max_tokens=max_tokens,
        stop_strings=stop if isinstance(stop, list) else [stop],
        **sample_kwargs
    ):
        yield chunk
```

### Example: Retry with edited context

```python
async def generate_with_retry_edit(session: EditableGGUFSession):
    """
    Generate, inspect output, remove bad tokens, insert correction, continue.
    This is the key use case you described.
    """
    prompt = "Once upon a time, a wizard named"
    session.eval_text(prompt)
    
    # Generate 20 tokens
    gen1 = session.generate_n(20)
    text1 = session.llm.detokenize(gen1).decode()
    print(f"Generated: {text1!r}")
    
    # Decide we don't like the last 5 tokens
    session.remove_last_n_tokens(5)
    
    # Insert a correction/steering text
    session.insert_text(" Aldric, who was wise and")
    
    # Continue generation from corrected context
    gen2 = session.generate_n(30)
    text2 = session.llm.detokenize(gen2).decode()
    print(f"Continued: {text2!r}")
    
    print(f"Full text: {session.current_text()!r}")
```

---

## Key Takeaways

| Feature | llama_cpp_python | HuggingFace | Notes |
|---|---|---|---|
| Remove tokens | `kv_cache_seq_rm` + adjust `n_tokens` | Slice `past_key_values` tensors | gguf is more efficient |
| Add tokens | `eval([tokens])` | Run forward pass with cache | Both work well |
| Save/restore | `save_state()` / `load_state()` | Copy cache tensors | gguf state includes sampling state |
| Efficiency | O(1) removal via seq_rm | O(layers) tensor slicing | Both avoid re-computation |

The **`kv_cache_seq_rm`** method in llama_cpp is the most efficient - it invalidates specific cache positions without copying. For your use case, I'd recommend building on `EditableGGUFSession` above and integrating it as a stateful object held alongside your `LlamaCpp` instance in `GGUFModel`.
