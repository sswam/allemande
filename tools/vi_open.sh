#!/bin/bash -eu
# [arg ...]
exec ${EDITOR:-vi} -O "$@"
