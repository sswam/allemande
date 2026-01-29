#!/bin/bash
m="$1"
shift
git add "$@"
git commit -m "$m" "$@"
