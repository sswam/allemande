#!/usr/bin/env bash

# Generate age estimation programs
# Uses models from Hugging Face
# Outputs detected info in TSV format

age-estimators() {
	input_file= i=age-estimation-google.txt  # Input file with model information
	output_dir= o=.                          # Output directory for generated scripts
	force= f=                                # Force overwrite of existing files

	eval "$(ally)"

	if [ ! -f "$input_file" ]; then
		die "Input file not found: $input_file"
	fi

	confirm "Generate age estimation programs?"

	grep -v -i civit "$input_file" | while IFS=$'\t' read -r model_name model_repo url; do
		output_file="$output_dir/${model_name}.py"

		if [ -f "$output_file" ] && [ "$force" != 1 ]; then
			printf >&2 "File already exists, skipping: %s\n" "$output_file"
			continue
		fi

		create -s=0 -m=prof "$output_file" "Please write a script using $model_repo from huggingface. Usage would be Image pathnames on stdin, one per line, output detected info on stdout in TSV, with the filename in the right-most column of output. TSV header is not necessary. Refer to the example script for code style and try to follow it closely. Relevant URL: $url" age_estimate_civitai.py
	done
}

if [ "${BASH_SOURCE[0]}" = "$0" ]; then
	age-estimators "$@"
fi

# version: 0.1.1
