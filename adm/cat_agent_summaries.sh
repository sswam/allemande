#!/usr/bin/env bash
agents=("$@")
if [ "${#agents[@]}" = 0 ]; then
	agents=(Ally Barbie Cleo Dali Emmie Fenny Gabby Hanni)
fi
cd ~/doc/summary/; for A in "${agents[@]}"; do echo -n "$A: "; cat "$A.txt"; done
