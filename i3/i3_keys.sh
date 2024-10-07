#!/bin/bash
# i3_keys - Generate a list of all possible key combinations for i3wm
# and output the unbound ones to stdout and unbound.txt

# Exit on error, and don't overwrite files
set -eu -o pipefail

# Extract bound keys from i3 config
grep "^bindsym\s" ~/.config/i3/config | sed -r 's/bindsym\s+//' > i3-keys-bindings.txt
sed -r 's/ .*//' < i3-keys-bindings.txt > i3-keys-bound.txt

# Define all possible keys and mods

keys=({a..z} {0..9} F{1..12})
mods='$mod $mod+Shift $mod+Control $mod+Alt'

# Generate all possible combinations
combinations=""
for mod in $mods; do
	for key in "${keys[@]}"; do
		combinations+="$mod+$key"$'\n'
	done
done

# Save unbound combinations to unbound.txt and output to stdout
echo -n "$combinations" | grep -v -F -f i3-keys-bound.txt | tee i3-keys-unbound.txt
