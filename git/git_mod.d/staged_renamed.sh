#!/bin/sh
git diff --cached --name-status --diff-filter=R | awk '{print $2"\t"$3}'
