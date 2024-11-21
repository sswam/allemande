#!/usr/bin/perl -n
# guess_columns: guess the column positions of a file

chomp;
s/ /\0/g;
$all |= $_;

END {
	$_ = $all;

	tr/\0/x/c;
	tr/\0/ /;
	print "$_\n";
	1 while s/x  /xx /g;
	print "$_\n";
	$pos = 1;
	while ($_ ne "") {
		if (s/^( +)//) {
			$pos += length($1);
		} elsif (s/^(x+)//) {
			$len = length($1);
			$end = $pos+$len;
			$out .= "$pos-$end,";
			$pos += $len;
		}
	}
	$out =~ s/,$//;
	print "$out\n";
	$out =~ s/\d+$//;
	print "$out\n";
}
