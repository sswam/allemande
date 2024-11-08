#!/usr/bin/env python3-allemande

"""
Document code files using AI-generated documentation.
"""

import os
import sys
from typing import TextIO
from io import StringIO

from argh import arg
import llm
import cat_named

from ally import main, text

__version__ = "1.0.8"

logger = main.get_logger()

def document_file(file: str, deps: set[str], prompt: str, model: str, pass_type: str) -> None:
    """Document a single file."""
    logger.info(f"Documenting: {file} ({pass_type})")

    content = [
        f"File: {file}",
        "Dependencies:",
        *([f"- {dep}" for dep in deps] if deps else ["None"]),
        "Content:",
    ]

    try:
        cat_named_output = cat_named.cat_named([file] + [f"{dep}.md" for dep in deps], missing_ok=True)
        content.append(cat_named_output)
    except Exception as e:
        logger.error(f"Error getting file content: {e}")
        content.append("Error: Unable to get file content")

    full_content = "\n".join(content)

    try:
        istream = StringIO(full_content)
        documented = llm.process(prompt, istream=istream, model=model)
        with open(f"{file}.md", "w") as f:
            f.write(documented)
        print(documented)
    except Exception as e:
        logger.error(f"Error documenting {file}: {e}")

    print()

@arg('--prompt', help='Custom prompt for documentation')
@arg('--model', help='AI model to use for documentation')
def code_doc(
    istream: TextIO = sys.stdin,
    ostream: TextIO = sys.stdout,
    prompt: str = "",
    model: str = ""
) -> None:
    """Document code files using dependencies from stdin."""
    get, put = main.io(istream, ostream)

    prompt = text.squeeze(f"""Please document this code file / module completely but very concisely in markdown.
    Emphasise recording the public API with signatures, a few examples, and concise descriptions.
    Provide a heading being the pathname to the module, a short description of the module as a whole,
    and a compact cheat-sheet for using the modules's public API. {prompt}""")

    dep_data = get().strip().split('\n')
    files_with_deps = [line.split('\t') for line in dep_data if line]

    for line in files_with_deps:
        file = line[1]
        deps = set(line[2:])
        document_file(file, deps, prompt, model, "Documentation Pass")

if __name__ == "__main__":
    main.run(code_doc)

