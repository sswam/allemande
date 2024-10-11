#!/bin/bash -eu
# file.py version
# Add a version to a Python program
file=$1 version=$2
ed "$file" <<END
$
?^import \|^from
a

__version__ = "$version"
.
w
q
END
