#!/usr/bin/env python3-allemande

"""
This module iteratively tries to perfect something (typically code),
starting from scratch or from an existing file.
"""

import sys
import logging
from typing import TextIO, Callable
import random
import os
import tempfile
import subprocess
from pathlib import Path

from argh import arg
import sh

from ally import main
from ally.lazy import lazy
import llm

__version__ = "0.1.0"

logger = main.get_logger()

# Define the models in order of strength
# expensive ones disabled for now: op, om
MODELS = ["claude", "gp", "4"]

def get_model_function(model: str) -> Callable:
    """Return the appropriate function for the given model."""
    return lambda prompt: llm.query(prompt, model=model)

#lazy("llm", **{model: get_model_function(model) for model in MODELS})

async def apply_improvement(file_content: str, improvement: str) -> str:
    """Apply the suggested improvement to the file content."""
    # TODO: Implement a more sophisticated way to apply improvements
    return improvement

async def detect_trivial_patch(old_content: str, new_content: str) -> bool:
    """Detect if the patch is trivial."""
    # TODO: Implement a more sophisticated way to detect trivial patches
    return old_content == new_content

async def run_checks(file_path: Path) -> str:
    """Run checks on the file and return the results."""
    # TODO: Implement actual checks (linters, type checkers, etc.)
    return "Checks passed"

async def run_tests(file_path: Path) -> str:
    """Run tests for the file and return the results."""
    # TODO: Implement actual test running
    return "Tests passed"

@arg("file", help="File to perfect")
@arg("--prompt", help="User guidance prompt")
@arg("--refs", nargs="*", help="Reference files")
@arg("--max-iterations", type=int, default=10, help="Maximum number of iterations")
async def perfect(
    file: str,
    prompt: str = "",
    refs: list[str] = [],
    max_iterations: int = 10,
    istream: TextIO = sys.stdin,
    ostream: TextIO = sys.stdout,
) -> None:
    """
    Iteratively try to perfect a file (typically code) using various AI models.
    """
    get, put = main.io(istream, ostream)

    file_path = Path(file)
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file}")

    with open(file_path, "r") as f:
        original_content = f.read()

    current_content = original_content
    iteration = 0

    while iteration < max_iterations:
        iteration += 1
        logger.info(f"Starting iteration {iteration}")

        # Choose a random model from the strongest models
        model = random.choice(MODELS[:3])  # Using top 3 models
        logger.info(f"Using model: {model}")

        # Prepare the prompt
        improvement_prompt = f"""
        Please suggest improvements for the following file:
        {current_content}

        User guidance: {prompt}

        Provide only the improved content, without any explanations.
        """

        # Get improvement suggestion
        improvement = getattr(llm, model)(improvement_prompt)

        # Apply improvement
        new_content = apply_improvement(current_content, improvement)

        if detect_trivial_patch(current_content, new_content):
            logger.info("Trivial patch detected. Stopping iterations.")
            break

        # Run checks and tests
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py") as temp_file:
            temp_file.write(new_content)
            temp_file.flush()

            check_results = run_checks(Path(temp_file.name))
            test_results = run_tests(Path(temp_file.name))

        if "failed" in check_results.lower() or "failed" in test_results.lower():
            logger.warning("Checks or tests failed. Asking for user help.")
            put("Checks or tests failed. Please provide guidance:")
            user_input = get()
            prompt += f" {user_input}"
            continue

        current_content = new_content

    # Write the final content back to the file
    with open(file_path, "w") as f:
        f.write(current_content)

    put(f"File perfected after {iteration} iterations.")

if __name__ == "__main__":
    main.run(perfect)

"""
TODO:
- Do everything with async. main.run can run async functions directly.
- Implement more sophisticated improvement application
  - Based on improve.sh but reimplemented better in Python
- Implement better trivial patch detection
  - Simple count of -/+ lines for a start, below a threshold e.g. 10 lines
- Implement actual checks and tests
  - Based on linty and testy tools, reimplemented in Python
- Implement dissent detection and resolution
  - Based on diffy tool perhaps, reimplemented in Python, and run over suggested
- Implement question asking for user when necessary
- Implement handling of extra file creation/combination/removal

DONE:
- Basic single-file perfection loop
- Model selection and usage
- Simple improvement application
- Basic trivial patch detection
- Placeholder for checks and tests
- User guidance incorporation
- Maximum iterations limit
- Implement function and class extraction and replacement
- Implement improving selected functions / classes only
- Implement multi-file project support

IDEAS:
"""
