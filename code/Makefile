all: lang.rec pop.txt rules.txt

.SECONDARY:

lang.rec: languages.rec
	<$< grep -E -e '^$$' -e '^(name|extension|shebang):' >$@

pop.pdf:
	curl "$$(search -l -m 1 "practice of programming type:pdf" | kut 2)" > $@
%.txt: %.pdf
	pdf2txt $< >$@
rules.txt: pop.txt
	<$< sed -n '/^Style/,/Index/p' | head -n -2 | strip-lines | grep -v -e '^[0-9]*$$' -e 'COLLECTED RULES' | sed 's/^[^ ]*$$/\n## &\n/; s/^[^ #\n]/- &/;' | tail -n +2 >$@
