#!/bin/bash -eu

# configuration ---------------------------------------------------------------

whisper_cpp_dir="/opt/whisper.cpp"
models_dir="$whisper_cpp_dir/models"


# process arguments -----------------------------------------------------------

# NOTE: we require the input file to be the last argument

# convert e.g. "--model large" to "--model models/ggml-large.bin"

# convert these output format options:

#  --output_format {txt,vtt,srt,tsv,json,all}, -f {txt,vtt,srt,tsv,json,all}
#     format of the output file; if not specified, all
#     available formats will be produced (default: all)

# --output_dir OUTPUT_DIR

# to these ones:

#  -otxt,     --output-txt        [false  ] output result in a text file
#  -ovtt,     --output-vtt        [false  ] output result in a vtt file
#  -osrt,     --output-srt        [false  ] output result in a srt file
#  -owts,     --output-words      [false  ] output script for generating karaoke video

args=()
model=""
language=en
have_format=0
output_dir="."

while [[ $# -gt 0 ]]; do
	if [[ "$1" == "--model" ]]; then
		model="$2"
		args+=("$1" "$models_dir/ggml-$2.bin")
		shift 2
	elif [[ "$1" == "--language" ]]; then
		language="$2"
		args+=("$1" "$2")
		shift 2
	# convert output format options: e.g. --output_format txt,vtt,srt,tsv,json
	elif [[ "$1" == "--output_format" || "$1" == "-f" ]]; then
		have_format=1
		shift
		for format in ${1//,/ }; do
			case "$format" in
				txt) args+=("-otxt") ;;
				vtt) args+=("-ovtt") ;;
				srt) args+=("-osrt") ;;
				all) args+=("-otxt" "-ovtt" "-osrt") ;;
				*) echo "error: unknown output format '$format'" >&2; exit 1 ;;
			esac
		done
	# detect the output directory option
	elif [[ "$1" == "--output_dir" ]]; then
		output_dir="$2"
		mkdir -p "$output_dir"
		shift 2
	else
		args+=("$1")
		shift
	fi
done


# convert the input file to 16 kHz wav, and use absolute path -----------------

input_file=""

if [[ "${#args[@]}" -gt 0 ]]; then
	input_file="${args[-1]}"
	input_file_name="$(basename "$input_file")"
	input_file_dir="$(dirname "$input_file")"

	# use sox or ffmpeg to convert to 16 kHz wav
	input_file_16k="$output_dir/${input_file_name%.*}-16k.tmp.wav"

	if [ ! -e "$input_file_16k" ]; then
		if command -v sox >/dev/null 2>&1; then
			sox "$input_file" -r 16000 -c 1 -b 16 "$input_file_16k"
		elif command -v ffmpeg >/dev/null 2>&1; then
			ffmpeg -i "$input_file" -ar 16000 -ac 1 "$input_file_16k"
		else
			echo "error: whisper.cpp wrapper requires sox or ffmpeg to convert audio to 16 kHz wav" >&2
			exit 1
		fi
	fi

	# Get the full path to the input file.
	# input_file_16k="$(realpath "$input_file_16k")"

	# update args to use the 16 kHz wav file
	args[-1]="$input_file_16k"
fi


# if no output format is specified, use all -----------------------------------

if [[ "$have_format" -eq 0 ]]; then
	args+=("-otxt" "-ovtt" "-osrt")
fi


# if no model is specified, use the default model ----------------------------

if [[ -z "$model" ]]; then
	model="base.en"
	args+=("--model" "$models_dir/ggml-$model.bin")
fi


# warn about using a suboptimal model -----------------------------------------

# if a language is specified and the specified model has a variant for that language
if [ -n "$language" -a -n "$model" -a -f "$models_dir/ggml-$model.$language.bin" ]; then
	echo "warning: suggest to use the '$model.language' variant of the '$model' model" >&2
fi


# run whisper.cpp -------------------------------------------------------------

# cd "$whisper_cpp_dir"
"$whisper_cpp_dir/whisper" "${args[@]}"


# rename any output files -----------------------------------------------------

if [[ -n "$input_file_16k" ]]; then
	for format in txt vtt srt; do
		if [[ -f "$input_file_16k.$format" ]]; then
			mv "$input_file_16k.$format" "$output_dir/${input_file_name%.*}.$format"
		fi
	done
fi

# remove the temporary file on success
v rm -vf '$input_file_16k'
