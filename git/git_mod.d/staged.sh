#!/bin/sh
git diff --cached --name-status | kut-perl -o 1 | tr '\t' '\n'
