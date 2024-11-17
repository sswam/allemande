#!/bin/bash
# nt: name-terminal: set the terminal title
echo -n $'\x1b]0;'"${*:- }"$'\x07'
