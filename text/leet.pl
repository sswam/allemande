#!/usr/bin/env perl

# a leetspeak encoder/decoder with additional obfuscation features

use strict;
use warnings;
use v5.30;
use utf8;
use open qw(:std :utf8);
use Getopt::Long qw(GetOptions);
use Pod::Usage qw(pod2usage);
use FindBin qw($RealBin);
use lib "$RealBin/lib";
use ally::main qw(setup_logging get_logger io);

our $VERSION = '1.0.0';

# Set up command-line options
my %opts = (
    mode => 'encode',
    double_prob => 0,
    vowel_remove_prob => 0,
    leet_prob => 1,
    star_prob => 0,
    extra => 0,
    light => 0,
    help => 0,
);

# Leet speak mapping
my %leet_map = (
    'a' => '4', 'b' => '8', 'e' => '3', 'g' => '6', 'i' => '1',
    'o' => '0', 's' => '5', 't' => '7', 'z' => '2',
);

sub all_options {
    $opts{double_prob} = 0.1;
    $opts{vowel_remove_prob} = 0.05;
    $opts{leet_prob} = 0.5;
    $opts{star_prob} = 0.05;
    $opts{extra} = 1;
};

GetOptions(
    'mode=s'    => \$opts{mode},
    'decode|d'  => sub { $opts{mode} = 'decode' },
    'double=f'  => \$opts{double_prob},
    'vowel=f'   => \$opts{vowel_remove_prob},
    'leet=f'    => \$opts{leet_prob},
    'star=f'    => \$opts{star_prob},
    'extra|x'   => \$opts{extra},
    'all|a'     => \&all_options,
    'light|l'   => \$opts{light},
    'help|h'    => \$opts{help},
) or pod2usage(2);

pod2usage(1) if $opts{help};

# Set up logging
setup_logging('1337');
my $logger = get_logger();

if ($opts{light}) {
    %leet_map = (
        'a' => '4', 'e' => '3', 'i' => '/',
        'o' => '0', 'u' => 'v',
    );
};

if ($opts{extra}) {
    %leet_map = (
        %leet_map,
        'c' => '(', 'd' => '|)', 'f' => '|=', 'j' => '_|', 'k' => '|<',
        'n' => '|\\|', 'q' => '9', 'r' => '|2', 'u' => '|_|', 'v' => '\\/',
        'w' => '\\/\\/', 'x' => '><', 'y' => '`/',
    );
}

our %reverse_map = reverse %leet_map;

# Main function
sub leet_convert {
    my ($input, $output) = @_;

    my ($get, $put) = io($input, $output);

    while (my $line = $get->()) {
        chomp $line;
        my $result = ($opts{mode} eq 'encode') ? encode($line) : decode($line);
        $put->($result);
    }
}

sub encode {
    my ($text) = @_;
    $logger->info("Encoding: $text");

    $text = lc $text;

    $text =~ s{([a-z])}{rand() < $opts{leet_prob} ? ($leet_map{$1} // $1) : $1}ge;

    # Additional obfuscations
    $text = double_letters($text) if $opts{double_prob} > 0;
    $text = remove_vowels($text) if $opts{vowel_remove_prob} > 0;
    $text = apply_star_obfuscation($text) if $opts{star_prob} > 0;

    return $text;
}

sub decode {
    my ($text) = @_;
    $logger->info("Decoding: $text");
    my $pattern = join '|', map quotemeta, sort { length($b) <=> length($a) } keys %reverse_map;
    $text =~ s/($pattern)/$reverse_map{$1}/g;
    return $text;
}

sub double_letters {
    my ($text) = @_;
    $text =~ s/([a-z0-9])/$1 . (rand() < $opts{double_prob} ? $1 : '')/ge;
    return $text;
}

sub remove_vowels {
    my ($text) = @_;
    $text =~ s/([aeiou])/rand() < $opts{vowel_remove_prob} ? '' : $1/ge;
    return $text;
}

sub apply_star_obfuscation {
    my ($text) = @_;
    $text =~ s/([aeiou])/rand() < $opts{star_prob} ? '*' : $1/ge;
    return $text;
}

# Run the main function
leet_convert(\*STDIN, \*STDOUT);

__END__

=head1 NAME

1337.pl - A leetspeak encoder/decoder with additional obfuscation features

=head1 SYNOPSIS

1337.pl [options]

 Options:
   --mode MODE       'encode' or 'decode' (default: encode)
   -d, --decode      Decode leetspeak text
   -a, --all         Apply all obfuscations
   --double PROB     Probability of doubling letters (0-1)
   --vowel PROB      Probability of removing vowels (0-1)
   --leet PROB       Probability of applying leetspeak (0-1)
   --star PROB       Probability of replacing vowels with asterisks (0-1)
   --extra, -x       Enable extra leetspeak characters (encodes only)
   --light, -l       Use a lighter set of leetspeak characters
   --help            Show this help message

=head1 DESCRIPTION

This script converts text to and from leetspeak. It can also apply additional
obfuscations like randomly doubling letters or removing vowels.

=cut

# This script, `1337.pl`, implements a leetspeak encoder/decoder with the following features:
#
# 1. It can encode regular text to leetspeak or decode leetspeak back to regular text.
# 2. It has an option to randomly double letters with a specified probability.
# 3. It has an option to randomly remove vowels with a specified probability.
# 4. It follows the structure and style of `hello.pl`, including logging, command-line option parsing, and documentation.
#
# To use the script:
#
# - For basic encoding: `echo "Hello World" | ./1337.pl`
# - For decoding: `echo "H3110 W0r1d" | ./1337.pl --mode decode`
# - To add letter doubling: `echo "Hello World" | ./1337.pl --double 0.3`
# - To remove vowels: `echo "Hello World" | ./1337.pl --vowel 0.5`
#
# You can combine options as needed. The script reads from STDIN and writes to STDOUT, allowing it to be used in pipelines or with file redirection.
