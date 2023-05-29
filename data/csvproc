#!/usr/bin/perl -w

# csvproc - process CSV data with a small perl program

use strict;
use warnings;
use utf8;
use open ':utf8';
use Text::CSV;
# use Text::TSV;  # copied inline
use Getopt::Long;
use File::Basename;
use List::Util qw(first max maxstr min minstr reduce shuffle sum);
use List::MoreUtils qw(:all);
use Time::Piece;
use Time::Seconds;
use File::Slurp 'slurp';
use Data::Dumper;
$Data::Dumper::Terse = 1;
$Data::Dumper::Indent = 0;

our $prog = basename($0);

sub usage {
    return "Usage: $prog [options] mapping" . <<'End';

Process CSV data with a small perl program.

  option        description

  -filter       filter lines, mapping returns boolean
  -out a,b      output fields a, b (can declare new fields)
  -cut a,b      exclude fields a, b from output
  -left a,b     put fields a, b at left of output
  -right a,b    put fields a, b at right of output
  -var a,b      declare fields a, b even if not in input
  -quoty ?      quote all non-NULL (default 1)
  -map ?        perl mapping file (default expects mapping on command line)
  -group a,b    group by a, b (where sorted, or similar rows are together)
  -joinsep s    when flattening a list, join by this string (default "\n")
  -multi        do not automatically print output lines, use 'out;' to print
  -tsv          use TSV file format
  -tsvin        use TSV file format for input
  -tsvout       use TSV file format for ouput
  -debug        show debug info including the generated perl code
  -help         show this message

utility function examples:

  zero_pad($Var, 4);
  fix_date($Date);
  date($Date)
  date_diff($End, $Start)
  err('message')
End
}

our $__filter = 0;
our $out_names;
our $cut_names;
our $left_names;
our $right_names;
our $var_names;
our $quoty = exists $ENV{CSVPROC_QUOTY} ? $ENV{CSVPROC_QUOTY} : 1;
our $map_file = "";
our $group_names;
our $joinsep = "\n";
our $__multi = 0;
our $use_tsv = 0;
our $use_tsv_in = 0;
our $use_tsv_out = 0;
our $debug = $ENV{CSVPROC_DEBUG} || 0;
our $help;

our $mapping;
our $in_names;
our $program;
our $__csv_in;
our $__csv_out;
our $__out;
our $__in;

sub debug {
    return if !$debug;
    my ($k, @v) = @_;    
    local $Data::Dumper::Indent = 0;
    my $v = Dumper(\@v);
    $v =~ s/.*?\[//;
    $v =~ s/\]\z//;
    warn "$k: $v\n";
}

sub split_opt_list {
    my ($s) = @_;
    return [] if !defined $s || $s eq "";
    $s =~ s/^\s+|\s+$//g;
    return [split /\s*,\s*/, $s];
}

sub get_opts_args {
    GetOptions(
        "filter"    => \$__filter,
        "out=s"     => \$out_names,
        "cut=s"     => \$cut_names,
        "left=s"    => \$left_names,
        "right=s"   => \$right_names,
        "var=s"     => \$var_names,
        "quoty=s"   => \$quoty,
        "map=s"     => \$map_file,
        "group=s"   => \$group_names,
        "joinsep=s" => \$joinsep,
        "multi"     => \$__multi,
        "tsv"       => \$use_tsv,
        "tsvin"     => \$use_tsv_in,
        "tsvout"    => \$use_tsv_out,
        "debug"     => \$debug,
        "help"      => \$help,
    )
        or die "failed: GetOptions";

    if ($help) { print usage; exit(0); }

    if ($map_file) {
        $mapping = slurp($map_file);
    } else {
        $mapping = shift @ARGV;
    }
    if (!defined $mapping || @ARGV) { die usage; }

    for ($out_names, $cut_names, $left_names, $right_names, $var_names, $group_names) {
        $_ = split_opt_list($_) if defined $_;
    }
    $var_names ||= [];
}

sub new_csv {
    my ($is_tsv) = @_;
    my $csv;
    if ($is_tsv) {
        $csv = Text::TSV->new;
    } else {
        $csv = Text::CSV->new({ binary => 1, always_quote => $quoty, blank_is_undef => $quoty })
            or die "Cannot use CSV: ".Text::CSV->error_diag;
        $csv->eol("\n");
    }
    return $csv;
}

sub setup_input_output {
    $__csv_in = new_csv($use_tsv || $use_tsv_in);
    $__csv_out = new_csv($use_tsv || $use_tsv_out);
    $__out = \*STDOUT; binmode($__out, ":utf8");
    $__in =  \*STDIN;  binmode($__in, ":utf8");
}

sub read_header {
    $in_names = $__csv_in->getline($__in);
    if (!$in_names) {
        die "bad input, bad or missing table header\n";
    }
    for (0..$#$in_names) {
        $in_names->[$_] ||= "_" . ($_ + 1);
    }
}

sub set_out_header {
    $out_names ||= $in_names;
    $cut_names ||= [];
    for ($left_names, $right_names) {
        push @$cut_names, @$_ if $_;
    }
    if (@$cut_names) {
        $out_names = [grep { my $x = $_; !grep {$_ eq $x} @$cut_names } @$out_names];
    }
    if ($left_names) {
        unshift @$out_names, @$left_names;
    }
    if ($right_names) {
        push @$out_names, @$right_names;
    }
}

sub write_header {
    $__csv_out->print($__out, $out_names)
        or die "failed: \$__csv_out->print: $!";
}

sub sym_name {
    my ($field_name) = @_;
    my $sym_name = $field_name;
    $sym_name =~ s/[^a-z0-9_]/_/gi;
    $sym_name =~ s/^([0-9])/_$1/;
    $sym_name = "_" if $sym_name eq "";
    return $sym_name;
}

sub var_name {
    my ($field_name, $type) = @_;
    my $sym_name = sym_name($field_name);
    my $var_name = $type . $sym_name;
    return $var_name;
}

sub uniq_var_names {
    my ($field_names, $type) = @_;
    $type ||= '$';
    my $var_names = join(', ', uniq map { var_name($_, $type) } @$field_names);
    return $var_names;
}

sub split_group {
    my ($group, @ary_fields) = @_;
    for my $i (0..$#ary_fields) {
        @{$ary_fields[$i]} = map { $_->[$i] } @$group;
    }
}

sub flat_group {
    my ($group, @fields) = @_;
    for my $i (0..$#fields) {
        my @ary = map { defined $_ ? $_ : "" } map { $_->[$i] } @$group;
        if (!grep {$_ ne $ary[0]} @ary) {
            ${$fields[$i]} = $ary[0];
        } else {
            ${$fields[$i]} = join $joinsep, @ary;
        }
    }
}

sub gen_program_group {
    $program = <<'End';
our $__fail = 0;
our @__group_key;
our @__group_key_prev;
our @__group;
our (__ALL_FIELDS__);
our (__ARY_FIELDS__);
sub out {
    my $__row_out;
    if (@_) {
        $__row_out = $_[0];
    } else {
        $__row_out = [__OUT_FIELDS__];
    }
    $__csv_out->print($__out, $__row_out)
        or die "failed: \$__csv_out->print: $!";
}
while (1) {
    my $__row_in = $__csv_in->getline($__in);
    if (!$__row_in) {
        $__csv_in->eof or die $__csv_in->error_diag();
        last;
    }
    (__OUT_FIELDS__) = ();
    (__IN_FIELDS__) = @$__row_in;
    @__group_key = (__GROUP_FIELDS__);
    if (@__group && join("\0", @__group_key) ne join("\0", @__group_key_prev)) {
        split_group(\@__group, \(__ARY_FIELDS__));
        flat_group(\@__group, \(__IN_FIELDS__));
        (__GROUP_FIELDS__) = @__group_key_prev;
        my $__filter_val = do {
            __MAPPING__;
        };
        if (!$__multi && (!$__filter || $__filter_val)) {
            my $__row_out = [__OUT_FIELDS__];
            $__csv_out->print($__out, $__row_out)
                or die "failed: \$__csv_out->print: $!";
        }
        @__group = ();
        (__OUT_FIELDS__) = ();
        (__IN_FIELDS__) = @$__row_in;
        (__ARY_FIELDS__) = ();
    }
    @__group_key_prev = @__group_key;
    push @__group, $__row_in;
}
if (@__group) {
    split_group(\@__group, \(__ARY_FIELDS__));
    flat_group(\@__group, \(__IN_FIELDS__));
    (__GROUP_FIELDS__) = @__group_key_prev;
    my $__filter_val = do {
        __MAPPING__;
    };
    if (!$__multi && (!$__filter || $__filter_val)) {
        my $__row_out = [__OUT_FIELDS__];
        $__csv_out->print($__out, $__row_out)
            or die "failed: \$__csv_out->print: $!";
    }
}
#close $__out
#    or die "failed: close: $!";
die "failed\n" if $__fail;
End
    my %vars = (
        IN_FIELDS    => uniq_var_names($in_names),
        OUT_FIELDS   => uniq_var_names($out_names),
        GROUP_FIELDS => uniq_var_names($group_names),
        ARY_FIELDS   => uniq_var_names($in_names, '@'),
        ALL_FIELDS   => uniq_var_names([@$in_names, @$out_names, @$cut_names]),
        MAPPING      => $mapping,
    );
    $program =~ s/__([A-Z_]+)__/$vars{$1}/g;
    debug(program => $program);
}

sub gen_program {
    if ($group_names) {
        gen_program_group;
        return;
    }
    $program = <<'End';
our $__fail = 0;
our (__ALL_FIELDS__);
sub out {
    my $__row_out;
    if (@_) {
        $__row_out = $_[0];
    } else {
        $__row_out = [__OUT_FIELDS__];
    }
    $__csv_out->print($__out, $__row_out)
        or die "failed: \$__csv_out->print: $!";
}
while (1) {
    my $__row_in = $__csv_in->getline($__in);
    if (!$__row_in) {
        $__csv_in->eof or die $__csv_in->error_diag();
        last;
    }
    (__OUT_FIELDS__) = ();
    (__IN_FIELDS__) = @$__row_in;
    my $__filter_val = do {
        __MAPPING__;
    };
    if (!$__multi && (!$__filter || $__filter_val)) {
        my $__row_out = [__OUT_FIELDS__];
        $__csv_out->print($__out, $__row_out)
            or die "failed: \$__csv_out->print: $!";
    }
}
#close $__out
#    or die "failed: close: $!";
die "failed\n" if $__fail;
End
    my %vars = (
        IN_FIELDS    => uniq_var_names($in_names),
        OUT_FIELDS   => uniq_var_names($out_names),
        ALL_FIELDS   => uniq_var_names([@$in_names, @$out_names, @$cut_names, @$var_names]),
        MAPPING      => $mapping,
    );
    $program =~ s/__([A-Z_]+)__/$vars{$1}/g;
    debug(program => $program);
}

# utility functions for the programs:

sub zero_pad {
    my ($v, $w) = @_;
    my $fmt = "%0${w}d";
    $v = sprintf($fmt, $v);
    $_[0] = $v;
}

sub fix_date {
    for (@_) {
        s/\s+00:00(?::00(?:\.0+))//;
        if (m{^(\d{1,2})/(\d{1,2})/(\d{4})$}) {
            $_ = Time::Piece->strptime($_, "%d/%m/%Y")->ymd;
        } elsif (m{^(\d{1,2})-(\d{1,2})-(\d{2})$}) {
            $_ = Time::Piece->strptime($_, "%m-%d-%y")->ymd;
        } elsif (m{^(\d{1,2}) ([A-Z][a-z]{2}) (\d{1,4})$}) {
            $_ = Time::Piece->strptime($_, "%d %b %y")->ymd;
	}
    }
}

sub date {
    my ($s) = @_;
    return Time::Piece->strptime($s, '%Y-%m-%d');
}

sub datetime {
    my ($s) = @_;
    return Time::Piece->strptime($s, '%Y-%m-%d %H:%M:%S');
}

sub date_diff {
    my ($d1, $d0) = @_;
    for ($d0, $d1) {
        $_ = Time::Piece->strptime($_, "%Y-%m-%d");
    }
    my $days = sprintf("%.0f", ($d1-$d0)/ONE_DAY);
    return $days;
}

sub err {
    my ($msg) = @_;
    warn "$msg, at input line $.\n";
    our $__fail;
    $__fail = 1;
}

sub mean {
    return sum(@_)/@_;
}

# end of utility functions

sub run_program {
    eval $program;
    die "$@\n" if $@;
}

sub main {
    get_opts_args;
    setup_input_output;
    read_header;
    set_out_header;
    write_header;
    gen_program;
    run_program;
}

# main;


package Text::TSV;
use strict;
use warnings;

use Data::Dumper;

sub new {
    my ($pkg) = @_;
    return bless { eol=>"\n", eof=>0 }, $pkg;
}

sub print {
    my ($self, $out, $f) = @_;
    my $line = join("\t", map { escape_tsv($_) } @$f) . $self->{eol};
    my $ok = print $out $line;
    if (!$ok) {
        $self->{error} = $!;
    }
    return $ok;
}

sub getline {
    my ($self, $in) = @_;
    my $old_err = $!;
    undef $!;
    my $line = <$in>;
    if (!defined $line && $!) {
        $self->{error} = $!;
        return undef;
    }
    $! = $old_err;
    if (!defined $line) {
        $self->{eof} = 1;
        return undef;
    }
    $line =~ s/\r?\n\z//s;
    my @f = map { unescape_tsv($_) } split /\t/, $line;
    return \@f;
}

sub eof {
    my ($self) = @_;
    return $self->{eof};
}

sub eol {
    my ($self, $eol) = @_;
    $self->{eol} = $eol;
    return;
}

sub error_diag {
    my ($self) = @_;
    return $self->{error};
}

my %tsv_escape_map = (
    "\\" => "\\",
    "\t" => "t",
    "\n" => "n",
    "\r" => "r",
    "\0" => "0",
);
my %tsv_unescape_map = map { $tsv_escape_map{$_} => $_ } keys %tsv_escape_map;

sub escape_tsv {
        my $v = shift;
        return "\\" unless defined $v;
        for ($v) {
                s/([\\\t\n\r\0])/"\\".$tsv_escape_map{$1}/gse;
        }
        return $v;
}

sub unescape_tsv {
    my $v = shift;
    return undef if $v eq "\\";
    for ($v) {
        s/\\(.)/$tsv_unescape_map{$1}/gse;
    }
    return $v;
}

# 1;


package main;

main;
