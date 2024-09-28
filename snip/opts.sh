
	local script_name=$(basename "$0")
	printf "%s " "$script_name"

	local line in_func=0 blanks=0 skip_blank_lines=0
	while IFS= read -r line; do
		# Skip shebang line
		if [[ $line == \#\!* ]]; then
			skip_blank_lines=1
			continue
		fi

		# Skip unindented function declaration, like:  hello() {
		if [[ "$line" =~ ^[[:alnum:]_]+\(\)[[:space:]]*\{ ]]; then
			continue
		fi

		# Remove indent
		line=${line#[[:space:]]*}

		is_blank=0
		if [ "$line" = "" ]; then
			is_blank=1
		fi

		# Remove 'local ' from start of line
		line=${line/#local /}

		# Remove '# ' from the line
		line="${line/\# }"

		# Replace literal '$0' in lines with the value of $script_name
		line="${line//\$0 /$script_name }"

		# Add dashes for -f or --foo and , for arrays
		line=$(
			echo "$line" |
			perl -pe '
				sub commas {
					local $_ = shift;
					if (/,/) {
						return q{"} . quotemeta($_) . q{"};
					}
					s/(?<!\\) /,/g;
					s/\\ / /g;
					return $_;
				}
				s{\b(\w)=\((.*?)\)}{"-$1,".commas($2)}ge;	# short array options
				s{\b(\w)=}{-$1=}g;	# short scalar options
				s{\b(\w\w+)=\((.*?)\)}{"--$1,".commas($2)}ge;	# long array options
				s{\b(\w\w+)=}{--$1=}g;	# long scalar options
			'
		)

		# Stop before the ". opts" line
		if [[ "$line" =~ ^[:space:]*\.\ opts ]]; then
			break
		fi

		# Skip other ". " lines
		if [[ "$line" =~ ^[:space:]*\.\  ]]; then
			continue
		fi

		# avoid trailing blank lines
		if [ "$is_blank" = 1 ]; then
			blanks=$((blanks+1))
			continue
		fi

		# check if we have some blank lines, and squeeze them
		if [ $blanks -gt 0 ] && [ $skip_blank_lines -eq 0 ]; then
			echo
		fi
		blanks=0
		skip_blank_lines=0

		# echo the cleaned-up line, for usage
		echo "$line"
	done < "$0" |
	tsv2txt -m 2>/dev/null || cat

