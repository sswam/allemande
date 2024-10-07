#!/bin/bash -eu
# paste-markdown: paste HTML from clipboard, convert to markdown
# TODO: split up into smaller scripts, can be used separately

xclip -selection clipboard -o -t text/html |
tee paste.html |
# < paste.html \
htmldebloater -i -t |
htmlsplit |
perl -pe 's/&nbsp;|\xa0/ /g' |
tidy -indent -wrap 0 -quiet -omit -f /dev/null |
grep -v -e '^<!DOCTYPE ' -e '^<meta' -e '^<title' |
pandoc -f html -t markdown --wrap=preserve |
grep -v -e '^</*div>$' |
perl -e '
	use utf8;
	binmode STDIN, ":utf8";
	binmode STDOUT, ":utf8";

	$_ = join "", <>;
	s{```{=html}
<!-- -->
```
}{}g;
	s/\xa0/ /g;       # non-breaking space
	s/\x{fffd}//g;    # replacement character

	# Copilot suggested to strip out many other
	# characters, but I do not want to yet until
	# I see the need. For example:
	# s/\x{200b}//g;  # zero-width space

	s/\n{3,}/\n\n/g;  # multiple blank lines
	s/ {2,}/ /g;      # multiple spaces
	s/\A\n+//;        # leading blank lines
	s/\n*\z/\n/;      # trailing blank lines

	print;
' \

# | cat
# | xclip -selection clipboard -i
