#!/usr/bin/env python3
import argparse
import sys
from pathlib import Path
from typing import List, Optional
import torch
from diffusers import DiffusionPipeline


def merge_loras(
    output_dir: Path,
    base_model_path: Path,
    lora_paths: List[Path],
    lora_weights: Optional[List[float]] = None,
) -> None:
    """
    Fuses multiple LoRA adapters permanently into a base diffusion pipeline 
    and exports a standalone checkpoint. Can be imported as a library function.
    """
    if lora_weights is None:
        lora_weights = [1.0] * len(lora_paths)
        
    if len(lora_paths) != len(lora_weights):
        raise ValueError("The number of LoRA paths must match the number of weights.")

    print(f"--> Loading base model from: {base_model_path}")
    dtype = torch.bfloat16 if torch.cuda.is_bf16_supported() else torch.float16
    
    # Load the base model pipeline
    pipe = DiffusionPipeline.from_pretrained(
        str(base_model_path), 
        torch_dtype=dtype,
        low_cpu_mem_usage=True
    )

    adapter_names = []
    
    # Load each LoRA layer systematically into the pipeline context
    for i, path in enumerate(lora_paths):
        name = f"adapter_{i}"
        adapter_names.append(name)
        print(f"--> Registering adapter [{name}] (weight: {lora_weights[i]}) from: {path}")
        
        # Diffusers accommodates directory paths or explicit single weight files
        if path.is_dir():
            pipe.load_lora_weights(str(path), adapter_name=name)
        else:
            pipe.load_lora_weights(
                str(path.parent), 
                weight_name=path.name, 
                adapter_name=name
            )

    print("--> Blending adapter configurations into pipeline namespace...")
    pipe.set_adapters(adapter_names, adapter_weights=lora_weights)
    
    print("--> Fusing LoRA weights permanently into the base model tensors...")
    pipe.fuse_lora(lora_scale=1.0)
    
    print("--> Purging independent adapter weights from memory tracking...")
    pipe.unload_lora_weights()

    print(f"--> Saving unified, un-adapted pipeline asset to: {output_dir}")
    output_dir.mkdir(parents=True, exist_ok=True)
    pipe.save_pretrained(str(output_dir))
    print("--> Merge complete!")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="CLI tool to permanently bake multiple LoRAs into an image generation pipeline."
    )
    parser.add_argument(
        "output_dir", 
        type=Path, 
        help="Path where the finalized, unified model directory will be saved."
    )
    parser.add_argument(
        "base_model", 
        type=Path, 
        help="Path or HuggingFace ID of the unquantized base diffusion model."
    )
    parser.add_argument(
        "loras", 
        nargs="+", 
        help="Paths to LoRA files/folders. Append optional scales using a colon syntax (e.g., path/to/lora.safetensors:0.55)"
    )

    args = parser.parse_args()

    parsed_paths: List[Path] = []
    parsed_weights: List[float] = []

    # Parse path and modifier scale string logic
    for lora_arg in args.loras:
        if ":" in lora_arg:
            # Handle Windows absolute paths with drive letters cleanly (e.g., C:\path:0.5)
            parts = lora_arg.rsplit(":", 1)
            # Ensure the split part is actually intended as a float numeric weight
            try:
                weight = float(parts[1])
                path_str = parts[0]
            except ValueError:
                path_str = lora_arg
                weight = 1.0
        else:
            path_str = lora_arg
            weight = 1.0

        lora_path = Path(path_str)
        if not lora_path.exists():
            print(f"Error: LoRA input target not found at '{lora_path}'", file=sys.stderr)
            sys.exit(1)
            
        parsed_paths.append(lora_path)
        parsed_weights.append(weight)

    try:
        merge_loras(
            output_dir=args.output_dir,
            base_model_path=args.base_model,
            lora_paths=parsed_paths,
            lora_weights=parsed_weights
        )
    except Exception as e:
        print(f"Execution Error during merge phase: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
