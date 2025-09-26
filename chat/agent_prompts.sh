#!/bin/bash -eu
yq -r "[.system_bottom, .system_top] | .[]" | grep -v -e "^$" -e "^+$" -e "^null$"
