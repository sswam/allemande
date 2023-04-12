#!/usr/bin/env python3

# Based on: https://github.com/oobabooga/text-generation-webui/blob/main/convert-to-safetensors.py

import sys
import argh
from pathlib import Path

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

def convert_llm_to_safetensors(model, output=None, max_shard_size="2GB", bf16=False):
	"""Converts a transformers model to safetensors format and shards it."""

	path = Path(model)
	model_name = path.name

	print(f"Loading {model_name}...", file=sys.stderr)
	model = AutoModelForCausalLM.from_pretrained(path, low_cpu_mem_usage=True, torch_dtype=torch.bfloat16 if bf16 else torch.float16)
	tokenizer = AutoTokenizer.from_pretrained(path)

	out_folder = output or Path(f"models/{model_name}_safetensors")
	print(f"Saving the converted model to {out_folder} with a maximum shard size of {max_shard_size}...", file=sys.stderr)
	model.save_pretrained(out_folder, max_shard_size=max_shard_size, safe_serialization=True)
	tokenizer.save_pretrained(out_folder)

if __name__ == '__main__':
	argh.dispatch_command(convert_llm_to_safetensors)
