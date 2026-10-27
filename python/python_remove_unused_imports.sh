#!/bin/bash -eu
ruff check "$@" --select F401 --fix
