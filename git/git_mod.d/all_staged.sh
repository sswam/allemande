#!/bin/sh
git diff --cached --name-status | awk '{print $2 (NF==3 ? "\t"$3 : "")}'
