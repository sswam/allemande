#!/usr/bin/perl -w

use strict;
use Getopt::Long qw(:config no_ignore_case);
# use Relation::Tools qw(header In Or And Sub);
use Data::Dumper;
$Data::Dumper::Terse=1;

my $progname = "process";

my ($mapping, $escaping, $escaping_before, $escaping_after, $filter, $add,
	$insert, $delete, $out, $rename, $group, $group_init, $group_agg,
	$group_first, $group_test, $var_global, $var_agg, $var_agg_init,
	$noprint, $noloop, $debug, $help);

GetOptions(
	'mapping=s' => \$mapping,
	'e|escaping' => \$escaping,
	'eb|escaping-before:s' => \$escaping_before,
	'ea|escaping-after:s' => \$escaping_after,
	'filter' => \$filter,
	'add=s' => \$add,
	'insert=s' => \$insert,
	'd|delete=s' => \$delete,
	'out=s' => \$out,
	'rename=s' => \$rename,
	'g|group=s' => \$group,
	'gi|group-initializer=s' => \$group_init,
	'ga|group-aggregate=s' => \$group_agg,
	'gf|group-first=s' => \$group_first,
	'gt|group-test=s' => \$group_test,
	'v|var-global=s' => \$var_global,
	'va|var-aggregate=s' => \$var_agg,
	'vai|var-aggregate-initial=s' => \$var_agg_init,
	'P|noprint' => \$noprint,
	'L|noloop' => \$noloop,
	'D|debug' => \$debug,
	'help' => \$help,
	) and @ARGV == 0
	or help(1);

$help and help(0);

sub help {
	my $out = $_[0] ? \*STDERR : \*STDOUT;
	print $out <<End;
syntax: $progname [options] < input > output
-m  --mapping code           - the mapping
-e  --escaping               - unescape and escape tab, nl, \\, nul, null
-eb --escaping-before [code] - unescape (before processing) only
-ea --escaping-after [code]  - escape (after processing) only
-f  --filter                 - filter lines (mapping should have a boolean value)
-a  --add 'a b'              - add fields a and b (at the end)
-i  --insert 'a b'           - insert fields a and b (at the beginning)
-d  --delete 'c d'           - delete fields c and d
-o  --out 'e f'              - output fields e and f only
-r  --rename 'A:a B:b'   - rename fields A to a and B to b in output
-g  --group 'q r'            - group by fields q and r (should be sorted already)
-gi --group-initializer code - run this at the start of each group
-ga --group-aggregate code   - run this for each element of the group
-gf --group-first code       - run this instead of group-aggregate for first element
-gt --group-test expr        - specify a custom test for a group
-v  --var-global 'm n'       - declare global varibales
-va --var-agg 's c'          - declare aggregate variables
-P  --noprint                - do not automatically print rows
-L  --noloop                 - do not automatically loop over all rows (implies -n)
-D  --debug                  - print the perl program constructed on stderr
-h  --help                   - this help

Random notes (to be put in a manpage one day):

You can use "pr" in the program to print extra rows, and "rd" to read extra
rows.

??? For each group field "foo", there is an output field "_foo" which is
renamed to "foo" on output.  This might be important to know if you are using a
custom group test, mapping group fields, or wanting to rename a group field.
End
	exit $_[0];
}

$noprint ||= $noloop;

my $line;
chomp($line = <STDIN>);
my @in_fields = split /\t/, $line, -1;
my @in_fields_esc = escape_fields(@in_fields);
# chomp($line = <STDIN>);
# $line =~ /^[\t-]*$/ or
# 	die "invalid table format - missing --- line\n";

sub splitspc {
	return defined $_[0] ? [split /\s+/, $_[0]] : [];
}

my @group_fields;
my @group_out_fields;
@group_fields = @{splitspc($group)};
if (@{Sub(\@group_fields, \@in_fields)}) {
	die "group fields must appear in the input\n";
}
@group_out_fields = map "_$_", @group_fields;

my @out_fields = @{splitspc($out)};
unless (@out_fields) {
	if ($group) {
		@out_fields = @group_fields;
	} else {
		@out_fields = @in_fields;
	}
}
@out_fields = @{Or(\@out_fields, splitspc($add))};
@out_fields = @{Or(splitspc($insert), \@out_fields)};
@out_fields = @{Sub(\@out_fields, splitspc($delete))};
my @out_fields_esc = escape_fields(@out_fields);

my @var_global = @{splitspc($var_global)};
my @var_agg = @{splitspc($var_agg)};

if ($group) {
	for (@out_fields) {
		if (In($_, \@group_fields)) {
			$_ = "_$_";
		}
	}
}

my @global_fields = @{Or(\@in_fields_esc, \@out_fields_esc, \@var_global, \@var_agg, \@group_out_fields)};

sub varlist {
	join ', ', map "\$$_", @_;
}

my $global_fields = join ' ', map "\$$_", @global_fields;
my $in_fields = varlist(@in_fields_esc);
my $out_fields = varlist(@out_fields_esc);
my $group_fields = varlist(@group_fields);
my $group_out_fields = varlist(@group_out_fields);

my %rename;

if ($group) {
	$var_agg_init = Dumper $var_agg_init;
	if (!@var_agg) {
		@var_agg = @{Sub(\@out_fields_esc, \@in_fields_esc)};
	}
	if (!$group_test) {
		$group_test = join " && ",
			map { "\$$_ eq \$_$_" } @group_fields;
	}
	$group_init = $group_init ? "{$group_init}" : '';
	for (reverse @var_agg) {
		$group_init = qq%
			\$$_ = $var_agg_init;
			$group_init
		%;
	}
	$group_init .= "($group_out_fields) = ($group_fields);";
	$group_agg = $group_agg ? "{$group_agg}" : '';  # accumulate with a delimiter by default?
	$group_first = $group_first ? "{$group_first}" : $group_agg;

	for (@group_fields) {
		$rename{"_$_"} = $_;
	}
}

if ($rename) {
	my @list = split /[:\s]/, $rename;
	while (my ($k, $v) = splice @list, 0, 2) {
		if (In($k, \@group_fields)) {
			$k = "_$k";
		}
		$rename{$k} = $v;
	}
}

my $program = $mapping ? "{$mapping}" : '';

if ($filter) {
	$program = qq%
		\$_PRINT = do {$program};
	%
}

if ($escaping || defined $escaping_before && $escaping_before eq "") {
	$escaping_before = q%
		if ($_ eq "\\\\") {
			undef $_;
		} else {
			s/([^\\\\]|^)((?:\\\\\\\\)*)\\\\0/$1$2\\0/g;
			s/([^\\\\]|^)((?:\\\\\\\\)*)\\\\n/$1$2\\n/g;
			s/([^\\\\]|^)((?:\\\\\\\\)*)\\\\t/$1$2\\t/g;
			s/\\\\\\\\/\\\\/g;
		}
	%;
}
if ($escaping || defined $escaping_after && $escaping_after eq "") {
	$escaping_after = q%
		if (defined $_) {
			s/\\\\/\\\\\\\\/g;
			s/\\t/\\\\t/g;
			s/\\n/\\\\n/g;
			s/\\0/\\\\0/g;
		} else {
			$_ = "\\\\";
		}
	%;
}
for ($escaping_before, $escaping_after) {
	if ($_) {
		$_ = qq%
			for (\@row) {
				$_
			}
		%;
	} else {
		$_ = "";
	}
}
if (! $noprint) {
	if ($filter) {
		$program .= q%
			$_PRINT and pr;
		%
	} else {
		$program .= q%
			pr;
		%
	}
}

if (! $noloop && ! $group) {
	$program = qq%
		while (defined (rd)) {
			$program
		}
	%
}

if ($group) {
	$program = qq%
		rd;
		$group_init
		$group_first
		while (defined (rd)) {
			if ($group_test) {
				$group_agg
			} else {
				$program
				$group_init
				$group_first
			}
		}
		$program
	%
}

$program = qq%
	my \@row;
	use vars qw/$global_fields/;
	sub rd {
		my \$line = <STDIN>;
		if (defined \$line) {
			chomp \$line;
			\@row = split /\\t/, \$line, -1;
			$escaping_before
			($in_fields) = \@row;
		}
		return \$line;
	}
	sub pr {
		\@row = ($out_fields);
		$escaping_after
		print join "\\t", \@row;
		print "\\n";
	}
	{
		$program
	}
%;

if ($filter) {
	$program = qq%
		my \$_PRINT;
		$program
	%;
}

for (@out_fields) {
	$_ = $rename{$_} || $_;
}

$debug and print STDERR "\n$program\n";

header(@out_fields);
eval $program;
if ($@) {
	die "program error: $@\n";
}

# --- from L.pm

sub In {
	my ($e, $l) = @_;
	$l eq "the universe!" and
		return 1;
	for (@$l) {
		$_ eq $e and
			return 1;
	}
	return 0;
}

sub Or {
	if (@_ == 2) {
		my ($l1, $l2) = @_;
		$l1 eq "the universe!" || $l2 eq "the universe!" and
			return "the universe!";
		my @ret = @$l1;
		for (@$l2) {
			In($_, $l1) or
				push @ret, $_;
		}
		return \@ret;
	}
	if (@_ > 2) { return Or(Or(shift, shift), @_); }
	if (@_ == 1) { return [@{$_[0]}] }
	if (@_ == 0) { return [] }
}

sub And {
	if (@_ == 2) {
		my ($l1, $l2) = @_;
		$l1 eq "the universe!" and
			return $l2;
		$l2 eq "the universe!" and
			return $l1;
		my @ret;
		for (@$l1) {
			In($_, $l2) and
				push @ret, $_;
		}
		return \@ret;
	}
	if (@_ > 2) { return And(And(shift, shift), @_); }
	if (@_ == 1) { return [@{$_[0]}] }
	if (@_ == 0) { return "the universe!" }
}

sub Sub {
	my ($l1, $l2) = @_;
	$l1 eq "the universe!" and
		die "sorry can't sub from the universe yet!";
	$l2 eq "the universe!" and
		return [];
	my @ret;
	for (@$l1) {
		In($_, $l2) or
			push @ret, $_;
	}
	return \@ret;
}

sub header {
	my @fields = @_;
	print join "\t", @fields;
	print "\n";
# 	print join "\t", map {my $a = $_; $a=~s/./-/g; $a} @fields;
# 	print "\n";
}

sub escape_fields {
	my (@fields) = @_;
	for (@fields) {
		s/[^\w_]/_/g;
		s/^/_/ if /^\d/;
	}
	return @fields;
}
