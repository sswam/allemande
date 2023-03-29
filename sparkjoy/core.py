#!/usr/bin/env python3

# Electric Barbarella v2 - core

# As simple as possible...

import os, json, itertools, bisect, gc

os.environ["TRANSFORMERS_OFFLINE"] = "1"

from transformers import AutoModelForCausalLM, AutoTokenizer, AutoConfig
import transformers
import torch
from accelerate import Accelerator
import accelerate
import time
import sys
import argparse
import logging
import readline
import yaml
from math import inf
from pathlib import Path
from typing import Any, Dict

# TODO consider dynamic reloading as an alternative:
# https://docs.python.org/3/library/functools.html

# q. Do I need the model cache?
# a. Yes, because the model is loaded into GPU memory, and if you load it again, it will be loaded into a different GPU memory location, and the model will not work.
# q. But I am reworking this to be a minimal core. I imagine that the system will run one "core" process for each model, and it won't be able to use any different model.
#    So I don't think I need the model cache for this use-case.
# a. I think you are right. I will remove the model cache.
# q. On the other hand, it might be useful when using this stuff from a library or notebook or whatever, and it's not a big deal to keep it.
# a. I think you are right. I will keep the model cache.

# I can always remove it easier, it's slightly more difficult to add it back in.
# I'll do it in a wrapper function anyway.

# I'll just remove it for now, the code is still there in assistant.py (v1)
# The main thing to do for core.py is make it as simple and stable as possible.

logger = logging.getLogger(__name__)

def load_model(model_path: Path, eight_bit=False, device_map="auto"):
	if device_map == "zero":
		device_map = "balanced_low_0"

	gpu_count = torch.cuda.device_count()
	logger.info('gpu_count %r', gpu_count)

	tokenizer = transformers.LlamaTokenizer.from_pretrained(str(model_path))
	model = transformers.LlamaForCausalLM.from_pretrained(
		str(model_path),
		device_map=device_map,
		#device_map="auto",
		torch_dtype=torch.float16,
		#max_memory = {0: "14GB", 1: "14GB", 2: "14GB", 3: "14GB",4: "14GB",5: "14GB",6: "14GB",7: "14GB"},
		max_memory = {0: "20GB"},
		load_in_8bit=eight_bit,
		# load_in_8bit_threshold=0.8,
		low_cpu_mem_usage=True,
		cache_dir="cache"
	).cuda()

	model.tokenizer = tokenizer

	model_cache[model_name] = model

	return model
