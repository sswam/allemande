#!/usr/bin/perl

# `jf' utility version 1.0.1
# join files - works with `sf' to facilitate global search / replace, etc.
# Usage: jf [--help] [joined.txt] [files...]

use strict;
use warnings;
use Getopt::Long;
use IO::File;

my $help;
my $sep = $ENV{JF_SEP} || '#File:';

GetOptions( 'help' => \$help ) or die "Error in command line arguments\n";

if ($help) {
    print_help();
    exit 0;
}

my $dest = shift;
if ( !defined $dest ) {
    die "usage: jf [--help] all.txt [file1.txt ...]\nsee:   sf\n";
}

my @src = @ARGV;

if (
    -e $dest
    && (  !-f _
        || -s _ && index( IO::File->new($dest)->getline(), "$sep " ) != 0 )
  )
{
    die "would clobber: $dest\n";
}

my $destfh = IO::File->new(">$dest") or die "cannot open $dest: $!";

while ( my $src = shift @src ) {
    chomp $src;
    if ( -T $src ) {
        print "processing textfile $src\n";
        my $srcfh = IO::File->new($src) or die "cannot open $src: $!";
        print $destfh $sep, ' ', $src, "\n";
        while ( my $line = <$srcfh> ) {
            if ( index( $line, $sep ) == 0 ) {
                substr $line, length($sep), 0, '-';
            }
            unless ( substr( $line, length($line) - 1 ) eq "\n" ) {
                print "Warning: $src doesn't end in a newline\n";
                $line .= "\n";
            }
            print $destfh $line;
        }
        $srcfh->close;
    }
    elsif ( -d $src ) {
        print "reading directory $src\n";
        opendir my $dir, $src or die "cannot open directory $src: $!";
        push @src,
          map { "$src/$_" } grep { $_ ne '.' && $_ ne '..' } readdir $dir;
        closedir $dir;
    }
    else {
        print "ignoring $src\n";
    }
}

$destfh->close;

sub print_help {
    print <<EOH;
jf (join files) utility version 1.0.1
Usage: jf [--help] [joined.txt] [files...]

Options:
  --help    Show this help message and exit

Description:
  jf joins multiple files into a single file, adding a separator line
  before each file's content. It works with 'sf' to facilitate global
  search and replace operations.

Environment:
  JF_SEP    Set a custom separator (default: '#File:')

See also: sf
EOH
}
