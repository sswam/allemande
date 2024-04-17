#!/bin/bash -u
qe curl "$1" | htmlsplit | sed -n '/<title/,$p' | sed -n '2{p;q}' | de
