#!/usr/bin/perl
# `sf' utility
# split files - works with `jf' to facilitate global search / replace, etc.
# Usage: sf [joined.txt]

use strict;

my $sep = $ENV{JF_SEP} || '#File:';
#my $sep = '!)@(#*$&%^';

use IO::File;

my $src = shift;
if (!defined $src) {
    die "usage: sf all.txt\nsee:   jf\n";
}

my $srcfh = new IO::File("$src")
	or die "cannot open $src\n";

my $line = <$srcfh>;
die "file should start with $sep\n" unless index($line, "$sep ") == 0;

do {
	my $dest;
	chomp ($dest = substr $line, length($sep)+1);

	rename $dest, "$dest~" if -e $dest;

	my $i = -1;
	while (($i = index $dest, '/', $i+1) != -1) {
		my $dir = substr $dest, 0, $i;
		unless ($dir eq "" || -d $dir) {
			mkdir $dir, 0777
				or die "cannot mkdir $dir\n";
#			print "making directory $dir\n";
		}
	}

	my $destfh = new IO::File(">$dest")
		or die "cannot open $dest\n";

	while (defined ($line = <$srcfh>)) {
		if (index($line, $sep) == 0) {
			last if index($line, "$sep ") == 0;
			$line = substr $line, length($sep) + 1;
		}
		print $destfh $line;
	}

	close $destfh;

	# undo the change if there was none
	if (-e "$dest~" && ! system "cmp", "-s", $dest, "$dest~") {
		print "= $dest\n";
		rename "$dest~", $dest;
	} else {
		print "> $dest\n";
		system "chmod", "--reference=$dest~", $dest;
	}
} while (defined $line);
