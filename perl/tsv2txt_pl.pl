#!/usr/bin/perl -w

# [-m] [-g N] [-h] [-v] [format_options ...]
# Converts TSV (Tab-Separated Values) to formatted text
# Supports multiple tables in input with the -m option

use strict;
use warnings;
use Getopt::Long;
use Pod::Usage;

our $VERSION = '1.1.5';

my %options = (
    multi_table => 0,
    gap => 2,
    help => 0,
    version => 0,
);

sub tsv2txt {
    my @args = @_;
    if (@args && ref($args[-1]) eq 'HASH') {
        %options = (%options, %{ pop @args });
    }
    my @format_options = @args;

    foreach my $opt (@format_options) {
        $opt ||= "-";
        $opt .= $opt =~ /\./ ? "f" : "s" if $opt !~ /[a-z]$/;
        $opt = "%$opt";
    }

    my @current_chunk;
    my $rx_split = get_tsv_format();

    while (my $line = <STDIN>) {
        if ($options{multi_table} && $line !~ /$rx_split/) {
            if (@current_chunk) {
                process_chunk(\@current_chunk, $options{gap}, \@format_options);
                @current_chunk = ();
            }
            print $line;
        } else {
            push @current_chunk, $line;
        }
    }

    process_chunk(\@current_chunk, $options{gap}, \@format_options) if @current_chunk;
}

sub get_tsv_format {
    my $tsv_format = $ENV{TSV_FORMAT} || '';
    return  $tsv_format eq "spaces_ok" ? qr{\s{2,}|\t} :
            $tsv_format eq "strict"    ? qr{\t} : qr{ *\t};
}

sub process_chunk {
    my ($chunk, $gap, $options) = @_;
    my @width;
    my @rows;

    $options = [@$options];

    foreach my $line (@$chunk) {
        chomp $line;
        my @row = split get_tsv_format(), $line, -1;
        process_row(\@row, \@width, $options);
        push @rows, \@row;
    }

    adjust_options($options, \@width);
    my $format = join " "x$gap, @$options;
    print_formatted_rows(\@rows, $format, scalar @$options);
}

sub process_row {
    my ($row, $width, $options) = @_;
    for (my $i = 0; $i < @$row; $i++) {
        $row->[$i] = "[NULL]" if $row->[$i] eq "\0";
        my $length = length sprintf $options->[$i] ||= "%-s", $row->[$i];
        $width->[$i] = $length if $length > ($width->[$i] || -1);
    }
}

sub adjust_options {
    my ($options, $width) = @_;
    for (my $i = 0; $i < @$options; $i++) {
        $options->[$i] =~ /(%|[^\.0-9])([1-9])/ or
            $options->[$i] =~ s/(\.|.$)/$width->[$i].$1/e;
    }
}

sub print_formatted_rows {
    my ($rows, $format, $option_count) = @_;
    my @empty = ("") x $option_count;
    foreach my $row (@$rows) {
        my $line = sprintf $format, ((@$row, @empty)[0..$option_count-1]);
        if (@$row == 0) {
            $line = "";
        } elsif ($line =~ /^ +$/) {
            $line = " ";
        } else {
            $line =~ s/ +$//;
        }
        print "$line\n";
    }
}

sub parse_cli_options {
    GetOptions(
        'm|multi-table' => \$options{multi_table},
        'g|gap=i' => \$options{gap},
        'h|help' => \$options{help},
        'v|version' => \$options{version},
    ) or pod2usage(2);

    pod2usage(1) if $options{help};
    if ($options{version}) {
        print "tsv2txt version $VERSION\n";
        exit 0;
    }

    return (\@ARGV, \%options);
}

sub main {
    my ($args, $options) = parse_cli_options();
    tsv2txt(@$args, $options);
}

main() unless caller;

1;

__END__

=head1 NAME

tsv2txt - Convert TSV (Tab-Separated Values) to formatted text

=head1 SYNOPSIS

tsv2txt [options] [format_options]

Options:
-m, --multi-table     Support multiple tables in input
-g, --gap=N           Set gap between columns (default: 2)
-h, --help            Show this help message
-v, --version         Show version information

Format Options:
Each format option specifies how to format a column. Options are applied in order to columns.
If fewer options are provided than columns, the last option is repeated for remaining columns.

Format: [width][.precision][type]

width:      Minimum field width (optional)
precision:  Number of decimal places for floating-point values (optional)
type:       s - string (default)
            d - integer
            f - floating-point
            x - hexadecimal
            o - octal

Justification:
< - Left-justified (default for strings)
> - Right-justified (default for numbers)
^ - Centered

Examples:
10s     - String, width 10, left-justified
10.2f   - Float, width 10, 2 decimal places, right-justified
15<d    - Integer, width 15, left-justified
8^s     - String, width 8, centered

=head1 DESCRIPTION

This script converts TSV (Tab-Separated Values) input to formatted text output.
It can handle multiple tables in the input with the -m option.

=head1 AUTHOR

Your Name <your.email@example.com>

=head1 LICENSE

This is free software; you can redistribute it and/or modify it under the same terms as Perl itself.

=cut

# TODO: don't buffer if it's coming from a file, read it twice...
#       otherwise, use temp file instead of buffering in memory?

# TODO make it work with indented code (i.e. don't screw up the indent level)
