#!/usr/bin/env python3-allemande

"""
This module provides a chat interface using a pre-trained language model.
It allows users to interact with an AI in a conversational manner.
"""

import os
import multiprocessing

os.environ["HF_HUB_OFFLINE"] = "1"

import logging
from typing import Callable

from ally import main
from ally.lazy import lazy

lazy("torch")
# from safetensors import safe_open
lazy("transformers", "PreTrainedTokenizerFast", "LlamaForCausalLM", "LlamaConfig") #, DynamicCache  # type: ignore

__version__ = "0.1.3"

logger = main.get_logger()


model = None
tokenizer = None


def setup_model():
    global model, tokenizer

    if model:
        return

    # Set the number of threads for PyTorch
    cuda = True

    if not cuda:
        num_cores = multiprocessing.cpu_count()
        torch.set_num_threads(num_cores)

    # Load the model and tokenizer
    model_name: str = "default"
    model_path: str = str(main.resource(f"models/llm/{model_name}"))
    #config = LlamaConfig.from_pretrained(f"{model_path}/config.json", repo_type="local")
    model = LlamaForCausalLM.from_pretrained(model_path)
    tokenizer = PreTrainedTokenizerFast.from_pretrained(model_path)

    # Load the model weights
    # with safe_open(model_path, framework="pt", device="cuda") as f:  # type: ignore
    #     for k in f.keys():
    #         model.state_dict()[k].copy_(f.get_tensor(k))

    if cuda:
        model = model.to(torch.bfloat16).to("cuda")
    #with torch.cuda.amp.autocast(dtype=torch.bfloat16):
    #    output = model(input)


    # model.to("cuda")
    # model.eval()


# Inference function
def generate(put: Callable, prompt: str, max_length: int = 1000, temperature: float = 1.2, top_k: int = 50, top_p: float = 0.9) -> str:
    input_ids = tokenizer.encode(prompt, return_tensors="pt")
    if cuda:
        input_ids = input_ids.to("cuda")
    output_ids = input_ids.clone()

    for i in range(max_length):
        outputs = model(input_ids=output_ids)

        logits = outputs.logits[:, -1, :]

        if temperature != 1.0:
            logits /= temperature

        # Start with the original logits
        filtered_logits = logits

        # Apply top-k filtering if top_k != 0
        if top_k > 0:
            top_k = min(top_k, logits.size(-1))  # Safety check
            # select the top-k logits and their indices
            top_k_logits, top_k_indices = torch.topk(filtered_logits, k=top_k)
            # create a new tensor filled with `-inf`
            filtered_logits = torch.full_like(filtered_logits, float('-inf'))
            # scatter the top-k logits back into their original positions
            filtered_logits.scatter_(-1, top_k_indices, top_k_logits)

        # Apply top-p filtering if top_p < 1.0
        if top_p < 1.0:
            # Sort the logits in descending order.
            sorted_logits, sorted_indices = torch.sort(filtered_logits, descending=True)
            # Compute the cumulative probabilities.
            cumulative_probs = torch.cumsum(torch.softmax(sorted_logits, dim=-1), dim=-1)
            # Create a mask for tokens to remove (those with cumulative probability above the top-p threshold).
            sorted_indices_to_remove = cumulative_probs > top_p
            # Shift the indices to the right to keep the first token above the threshold
            sorted_indices_to_remove[..., 1:] = sorted_indices_to_remove[..., :-1].clone()
            sorted_indices_to_remove[..., 0] = 0

            # Set the logits of tokens to be removed to `-inf`.
            indices_to_remove = sorted_indices[sorted_indices_to_remove]
            filtered_logits[0, indices_to_remove] = float('-inf')

        # Sample from the filtered distribution
        next_token = torch.multinomial(torch.softmax(filtered_logits, dim=-1), num_samples=1)

        output_ids = torch.cat([output_ids, next_token], dim=-1)

        # Check for end of generation
        if next_token.squeeze().item() == tokenizer.eos_token_id:
            break

        next_token_str = tokenizer.decode(next_token[0], skip_special_tokens=True)

        if put(next_token_str):
            break
    else:
        put("\n")

    # return tokenizer.decode(output_ids[0], skip_special_tokens=True)


def chat(get: Callable, put: Callable, history: list[str]) -> None:
    while True:
        user_input = get("Sam: ")
        if user_input is None:
            break
#        put("Ally:")
        try:
            response = generate(put, "".join(history))
        except KeyboardInterrupt:
            pass


def chat_interface(get: Callable, put: Callable, file: str) -> None:
    """Run the chat interface."""
    get2, put2 = get, put

    if file:
        with open(file) as f:
            history = f.readlines()
            for line in history:
                put2(line, end="", flush=True)
    else:
        history = []

    setup_model()

    def get(prompt: str) -> str:
        nonlocal history
        user_input = get2(prompt="", placeholder=prompt)
        if user_input is None:
            return None
        if user_input:
            history.append(user_input + "\n")
        if file:
            with open(file, "a") as f:
                f.write(user_input + "\n")
        return user_input

    def put(text: str, **kwargs) -> bool:
        nonlocal history
        stop = "\n" in text
        if stop:
            text = text[: text.index("\n") + 1]
        history.append(text)
        put2(text, end="", flush=True, **kwargs)
        if file:
            with open(file, "a") as f:
                f.write(text)
        return stop

    with torch.no_grad():
        chat(get, put, history)


def setup_args(parser):
    """Set up command-line arguments."""
    parser.description = "Chat interface using a pre-trained language model."
    parser.add_argument(
        "--file",
        type=str,
        default=None,
        help="Path to a file containing the chat history.",
    )


if __name__ == "__main__":
    main.go(chat_interface, setup_args)
