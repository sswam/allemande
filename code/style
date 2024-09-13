#!/usr/bin/env python

import sys
import os
from pathlib import Path

home = Path(os.environ["ALLEMANDE_HOME"])

def main():
    files = sys.argv[1:]

    if not files:
        print("No files provided.", file=sys.stderr)
        sys.exit(1)

    extension_to_language = {
        'sh': 'bash',
        'py': 'python'
    }

    extensions = []

    for file in files:
        if "." in file:
            _, ext = os.path.splitext(file)
            ext = ext.lstrip('.')
        else:
            ext = "sh"

        if ext not in extension_to_language:
            print(f"Unsupported program file extension: {file}", file=sys.stderr)
            sys.exit(1)

        if ext not in extensions:
            extensions.append(ext)

    for ext in extensions:
        lang = extension_to_language[ext]
        hello_script = home / lang / f"hello.{ext}"
        print(hello_script)


    # TODO: Implement the improvement process
    # "Please improve the quality of this program, fixing the code style to match the 'hello' sample."

if __name__ == "__main__":
    main()
