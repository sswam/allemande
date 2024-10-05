#!/usr/bin/env python3

"""
This module generates a file in the style of provided reference files or authors.
"""

import sys
import logging
from typing import TextIO
import os
import subprocess

from argh import arg
import sh

from ally import main
from ally.lazy import lazy
import llm

__version__ = "0.1.1"

logger = main.get_logger()


def get_comment_style(ext: str) -> str:
    """Get the comment style for a given file extension."""
    # TODO: Implement a more comprehensive mapping of file extensions to comment styles
    comment_styles = {
        "py": "#",
        "sh": "#",
        "js": "//",
        "cpp": "//",
        "c": "//",
        "java": "//",
        "md": "",
    }
    return comment_styles.get(ext, "#")


def prepare_prompt(ofile: str, prompt: str, refs: list[str]) -> str:
    """Prepare the prompt for the AI."""
    prompt2 = f"Please write `{ofile}` in the style of {prompt}"
    if refs:
        if prompt:
            prompt2 += " and"
        prompt2 += " the provided reference files."
    return prompt2


def process_input(refs: list[str]) -> str:
    """Process input from stdin and reference files."""
    # TODO: Implement cat_named.py functionality
    input_data = sys.stdin.read()
    for ref in refs:
        with open(ref, 'r') as f:
            input_data += f.read()
    return input_data if input_data else ":)"


@arg("ofile", help="Output file name")
@arg("refs", nargs="*", help="Reference files")
@arg("--prompt", "-p", help="Extra prompt")
@arg("--model", "-m", help="LLM model")
@arg("--style", "-s", default=0, help="Also refer to hello_$ext.$ext for style")
@arg("--edit", "-e", default=1, help="Edit the output file")
def alla(
    ofile: str,
    *refs: str,
    prompt: str = "",
    model: str = "",
    style: int = 0,
    edit: int = 1,
    istream: TextIO = sys.stdin,
    ostream: TextIO = sys.stdout,
) -> None:
    """
    Generate a file in the style of provided reference files or authors.
    """
    if not ofile:
        raise ValueError("Output file name is required")

    if os.path.exists(ofile):
        raise FileExistsError(f"Output file already exists: {ofile}")

    ext = ofile.split('.')[-1] if '.' in ofile else "sh"
    comment_char = get_comment_style(ext)

    refs = list(refs)
    if style and os.path.exists(f"hello_{ext}.{ext}"):
        refs.append(f"hello_{ext}.{ext}")

    prompt2 = prepare_prompt(ofile, prompt, refs)
    input_data = process_input(refs)

    response = llm.query(input_data, prompt=prompt2, model=model)

    with open(ofile, 'w') as f:
        if comment_char and ext != "md":
            # TODO: Implement markdown_code.py functionality
            f.write(f"{comment_char} {response}\n")
        else:
            f.write(response)

    if ext != "md":
        os.chmod(ofile, 0o755)

    if edit:
        editor = os.environ.get('EDITOR', 'vim')
        subprocess.call([editor, ofile])


if __name__ == "__main__":
    main.run(alla)
