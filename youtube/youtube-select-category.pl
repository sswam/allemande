#!/usr/bin/perl -wn

# YouTube Select Category

use strict;
use warnings;
use Data::Dumper;

our $place;
our @place_words;
our @all_cats;
our @okay_random_cats;
our %map_title_to_url;

BEGIN {
	($place) = @ARGV;
	@ARGV = ();
	@place_words = split /\s+/, $place;
	@all_cats = qw(SEE DO LEARN EAT_AND_DRINK GETTING_THERE STAY IN_THE_AREA EVENTS ACCESSIBILITY LOCAL_GROUPS WARNINGS);
	@okay_random_cats = qw(SEE DO LEARN IN_THE_AREA EVENTS LOCAL_GROUPS WARNINGS);
	open(my $fh, "<", "YOUTUBE/SELECT_YOUTUBE.txt");
	while (<$fh>) {
		chomp;
		my @cols = split /\t/, $_;
		my ($num, $title, $url, $thumb) = @cols;
		$title =~ s/\s*[|].*//;
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
$title =~ s/\s*[|].*//;
my @cats = split /,\s*/, $cats;

my $cat = undef;

my $url = $map_title_to_url{$title};

if (!defined $url) {
	warn "*** Title not found in map_title_to_url: $title\n";
	next;
}

if ($url !~ m{^https://www\.youtube\.com/watch\?v=}) {
	next;
}

my $irrelevant = 0;
for my $word (@place_words) {
	# TODO stemming?
	if ($title !~ /\Q$word\E/) {
		warn "Skipping seemingly irrelevant video: $title  vs  @place_words\n";
		$irrelevant = 1;
		last;
	}
}
if ($irrelevant) {
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
