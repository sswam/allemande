#!/usr/bin/env python3

"""
safetensors-convert.py: Convert a transformers model to safetensors format and shard it.
"""

import sys
from pathlib import Path
from typing import Optional

from ally import main
from ally.lazy import lazy

lazy("torch")
lazy("transformers", "AutoModelForCausalLM", "AutoTokenizer")

__version__ = "0.1.1"

logger = main.get_logger()


def convert_llm_to_safetensors(
    model: str,
    output: Optional[str] = None,
    max_shard_size: str = "2GB",
    bf16: bool = False
) -> None:
    """
    Convert a transformers model to safetensors format and shard it.

    Args:
        model: Path to the model to convert
        output: Output directory for the converted model
        max_shard_size: Maximum shard size for the converted model
        bf16: Use bfloat16 precision instead of float16
    """
    path = Path(model)
    model_name = path.name

    logger.info(f"Loading {model_name}...")
    model = AutoModelForCausalLM.from_pretrained(
        path,
        low_cpu_mem_usage=True,
        torch_dtype=torch.bfloat16 if bf16 else torch.float16
    )
    tokenizer = AutoTokenizer.from_pretrained(path)

    out_folder = output or Path(f"models/{model_name}_safetensors")
    logger.info(f"Saving the converted model to {out_folder} with a maximum shard size of {max_shard_size}...")
    model.save_pretrained(out_folder, max_shard_size=max_shard_size, safe_serialization=True)
    tokenizer.save_pretrained(out_folder)

    logger.info("Conversion completed successfully.")


if __name__ == '__main__':
    main.run(convert_llm_to_safetensors)

"""
TODO: Add support for converting multiple models in batch
FIXME: Improve error handling for invalid model paths
XXX: Consider adding option to specify custom naming for output files
"""
