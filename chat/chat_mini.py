#!/usr/bin/env python3-allemande

""" Use an LLM for text generation. """

import os

os.environ["USE_TF"] = "0"
os.environ["USE_TORCH"] = "1"

import sys
import logging
from typing import TextIO

import torch
import transformers  # type: ignore
from argh import arg

from ally import main

__version__ = "0.1.2"

os.environ["HF_HUB_OFFLINE"] = "1"

logger = main.get_logger()


default_local_model = "default"
default_model = str(main.resource(f"models/llm/{default_local_model}"))


@arg("--model", help="model")
def generate_text(
    istream: TextIO = sys.stdin,
    ostream: TextIO = sys.stdout,
    model: str = default_model,
) -> None:
    """
    Generate text using a locally downloaded LLM model.
    """

    get, put = main.io(istream, ostream)

    pipeline = transformers.pipeline(
        "text-generation",
        model=model,
        model_kwargs={"torch_dtype": torch.bfloat16},
        device_map="auto",
        max_new_tokens=500,
        truncation=True,
        #         temperature=0.7,
        #         top_k=50,
        #         top_p=0.9,
    )

    while (prompt := get()) is not None:
        result = pipeline(prompt)
        put(result[0]["generated_text"])


if __name__ == "__main__":
    main.run(generate_text)
