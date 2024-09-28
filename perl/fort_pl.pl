#!/usr/bin/perl
$n = 1;
while (<STDIN>) {
	if (int rand($n) == 0) {
		$x = $_;
	}
	++$n;
}
if (defined $x) {
	print $x;
}
