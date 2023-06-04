#!/usr/bin/perl -w
use strict;
use warnings;
use Data::Dumper;

my $nosort = $ENV{NOSORT};
my $delim = $ENV{DELIM} // ", ";

my @fields;
my %fields;
my @recs;
my $rec = {};

while (defined($_=<STDIN>)) {
	chomp;
	my ($k, $v) = split /:\s+|\t/, $_, 2;
	if ($k) {
		if (!exists $rec->{$k}) {
			$rec->{$k} = $v;
		} else {
			$rec->{$k} .= "$delim$v";
		}	
		if (!$fields{$k}) {
			push @fields, $k;
		}
		$fields{$k}++;
	} else {
		push @recs, $rec;
		$rec = {};
	}
}

# warn Dumper \@fields;

if (!$ENV{NOSORT}) {
	@fields = sort { $fields{$b} <=> $fields{$a} } @fields;
}

# warn Dumper \@fields;

put(\@fields);

for my $rec (@recs) {
	my @values = map { $rec->{$_} } @fields;
	put(\@values);
}

sub put {
	my ($row) = @_;
	print join("\t", map { defined $_ ? $_ : "" } @$row), "\n";
}

