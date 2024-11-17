#!/bin/bash -eu

# [arg ...]
# Show the different hello_foo.foo example files in Allemande
cd "$ALLEMANDE_HOME"
find . -maxdepth 2 -name "hello_*.*" | perl -ne 'print if m{/hello_(\w+)\.(\1)$}'
