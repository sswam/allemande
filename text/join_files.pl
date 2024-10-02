#!/usr/bin/perl
# `jf' utility
# join files - works with `sf' to facilitate global search / replace, etc.
# Usage: jf [joined.txt] [files...]

use strict;

my $sep = $ENV{JF_SEP} || '#File:';
#my $sep = '!)@(#*$&%^';

use IO::File;

my $dest = shift;
if ( !defined $dest ) {
    die "usage: jf all.txt [file1.txt ...]\nsee:   sf\n";
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

my $destfh = new IO::File(">$dest")
  or die "cannot open $dest";

while ( my $src = shift @src ) {
    chomp $src;
    if ( -T $src ) {
        print "processing textfile $src\n";

        # we only want to munge text files, not binary
        my $srcfh = new IO::File($src)
          or die "cannot open $src";
        print $destfh $sep, ' ', $src, "\n";
        while ( my $line = <$srcfh> ) {
            if ( index( $line, $sep ) == 0 ) {
                substr $line, length($sep), 0, '-'; #insert a - after it to distinguish from a separator, which has a space
            }
            unless ( substr( $line, length($line) - 1 ) eq "\n" ) {

                # oh no, doesn't end in a newline
                print "Oh no, doesn't end in a newline!\n";
                $line .= "\n";
            }
            print $destfh $line;
        }
    }
    elsif ( -d $src ) {
        print "reading directory $src\n";
        opendir DIR, $src;
        push @src,
          map { "$src/$_" } grep { not( $_ eq '.' or $_ eq '..' ) } readdir DIR;
    }
    else {
        print "ignoring $src\n";
    }
}

close $destfh;
