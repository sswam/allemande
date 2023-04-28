#!/usr/bin/perl -p
# Filter text to make it more suitable for speech synthesis.

use strict;
use warnings;
our %letter_by_letter;

# TODO The list of acronyms should be in a separate file, and it's not yet comprehensive to say the least!
# We need some heuristic for whether an acronym is pronounceable or not.

BEGIN {
	$| = 1;
	%letter_by_letter = map { $_ => 1} qw(
		AI
		PCI
		PCMCIA
	);
}
sub to_letters {
	my ($word) = @_;
	$word =~ s/(.)/$1./g;
	return $word;
}
s/–/.../g;
s/\x{7e9}/'/g;
s/[^\0-~]//g;    # filter out emojis; but \x7e9 is closing single-quote / "smart" apostrophe
#s{\bThalia\b}{<phoneme ph="təˈliːə">Thalia</phoneme>}g;
s{\bThalia\b}{Thalia}g;
s/\b([A-Z]{2,})\b/$letter_by_letter{$1} ? to_letters($1) : ucfirst(lc $1)/ge;
