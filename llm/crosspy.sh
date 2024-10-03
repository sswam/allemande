#!/usr/bin/env bash

# [input files]
# Cross-pollinate the provided files

crosspy() {
	local model= m=''				# LLM model
	local exemplar_file="exemplar.$$"	# Output file for exemplar script
	local improve_tool="improve"	# Tool for improving scripts
	local prompt=''				 # Custom prompt

	eval "$(ally)"  # this magickally handles options, brings in die and warn, etc

	# Collect input files
	local input_files=("$@")

	# Step 1: Create exemplar script
	create_exemplar "${input_files[@]}"

	# Step 2: Update other scripts based on exemplar
	update_scripts "${input_files[@]}"
}

create_exemplar() {
	local input_files=("$@")

	warn "Creating exemplar script..."
	cat-named -p -b "${input_files[@]}" |
		combo -m="$model" -p="Create a small 'exemplar' script, including comments with a list of ideas,
local idioms, and best practices. ${prompt}" >"$exemplar_file"

	warn "Exemplar script created: $exemplar_file"
}

update_scripts() {
	local input_files=("$@")

	warn "Updating scripts based on exemplar..."
	for file in "${input_files[@]}"; do
		warn "Improving $file..."
		"$improve_tool" -m="$model" -p="$prompt" "$file" "$exemplar_file"
	done
}

if [ "${BASH_SOURCE[0]}" = "$0" ]; then
	crosspy "$@"
fi

# version: 0.1.1
