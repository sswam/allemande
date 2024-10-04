
simple_divvy() {
	local line_count=$1
	local prefix=$2
	local suffix=$3
	shift 3
	local output_files=("$@")

	if [ -n "$line_count" ]; then
		split -l "$line_count" - "${prefix:-}${output_files[0]}${suffix:-}"
	else
		local file_count=${#output_files[@]}
		split -n "$file_count" - "${prefix:-}${output_files[0]}${suffix:-}"
	fi

	# Rename split files to match output_files
	local i=0
	for file in "${prefix:-}${output_files[0]}${suffix:-}"*; do
		if [ $i -lt ${#output_files[@]} ]; then
			mv "$file" "${output_files[$i]}"
			i=$((i + 1))
		else
			break
		fi
	done
}

