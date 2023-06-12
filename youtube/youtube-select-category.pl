#!/usr/bin/perl -wn

# YouTube Select Category

use strict;
use warnings;

our @all_cats;
our @okay_random_cats;
our %map_title_to_url;

BEGIN {
	@all_cats = qw(SEE DO LEARN EAT_AND_DRINK GETTING_THERE STAY IN_THE_AREA EVENTS ACCESSIBILITY LOCAL_GROUPS WARNINGS);
	@okay_random_cats = qw(SEE DO LEARN IN_THE_AREA EVENTS LOCAL_GROUPS WARNINGS);
	open(my $fh, "<", "YOUTUBE/SELECT_YOUTUBE.txt");
	while (<$fh>) {
		chomp;
		my @cols = split /\t/, $_;
		my ($num, $title, $url, $thumb) = @cols;
		$url =~ s/\s//g;
		$map_title_to_url{$title} = $url;
	}
	$| = 1;
}

our %cat;

chomp;
tr/;/\t/;
my $line = $_;
my @cols = split /\t/, $line;
s/^\s*|\s*$//g for @cols;
my ($num, $title, $cats, $loc) = @cols;
my @cats = split /,\s*/, $cats;

my $cat = undef;

my $url = $map_title_to_url{$title};

if ($url !~ m{^https://www\.youtube\.com/watch\?v=}) {
	next;
}

for (@cats) {
	next if $cat{$_};
	$cat = $cat{$_} = $title;
	last;
}

if (!$cat) {
	for (@okay_random_cats) {
		next if $cat{$_};
		$cat = $cat{$_} = $title;
		last;
	}
}

if (!$cat) {
	warn "No remaining categories for: $line\n";
}

END {
	for (@all_cats) {
		my $title = $cat{$_};
		if ($title) {
			print "## ${_}_YOUTUBE_VID\n\n$map_title_to_url{$title}\n\n";
			warn "$title\n\n";
		}
	}
}
