#!/bin/sh
git rm "$@"
git commit -m "chore: renamed" "$@"
