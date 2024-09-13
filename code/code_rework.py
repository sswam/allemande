#!/usr/bin/env python3

import os
import sys
from pathlib import Path

import llm
from markdown_code import extract_code_from_markdown
from cat_named import cat_named


def get_new_name(file_path):
    path = Path(file_path)
    new_name = f"{path.stem}.new{path.suffix}"
    return path.with_name(new_name)

def code_rework(prompt, files):
    input_content = cat_named(files)

    # Use the first file in the list for the prompt
    main_file = files[0]
    prompt = f"Please rework `{main_file}`. {prompt}"
    response = llm.query(prompt + "\n\n" + input_content)

    processed_response = extract_code_from_markdown(response, comment_prefix='#')

    new_file = get_new_name(main_file)
    with open(new_file, 'w') as ostream:
        ostream.write(processed_response)
    print(new_file)

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: code_rework.py <prompt> <file> [additional files...]")
        sys.exit(1)

    prompt = sys.argv[1]
    files = sys.argv[2:]
    code_rework(prompt, files)
