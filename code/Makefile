all: lang.txt

lang.txt: languages.txt
	<$< grep -E -e '^$$' -e '^(name|extension|shebang):' >$@

.SECONDARY:
