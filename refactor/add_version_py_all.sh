#!/bin/bash -eu
# version
# Add versions to all python files
version=$1
git ls-files | grep '\.py$' | xa grep -L __version__ | while read F; do ./add_version_py.sh "$F" "$version"; done
