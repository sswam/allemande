#!/bin/bash -eu

main() {
	for file; do
		if grep "^system_bottom:" < "$file"; then
			fix system_bottom
		fi
		if grep "^system_top:" < "$file"; then
			fix system_top
		fi
	done
}

fix() {
	field=$1
	cat "$file" | yaml-extract-field "$field" | tee "$field.old.txt"
	< "$field.old.txt" process -m=flasho "Please rewrite in first person, without changing anything else. The format must be identical including the YAML header and any punctuation. Output between \`\`\`" | ted 's/.*?^```(yaml)?\n//sm; s/^```.*//sm' | tee "$field.new.txt"
	< "$file" yaml-replace-field "$field" "$(<$field.new.txt)" | tee "$file.new"
	cp "$file.new" "$file" ; rm "$file.new"
}

main "$@"
