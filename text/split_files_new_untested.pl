#!/usr/bin/perl

# split_files.pl v1.0.1
# Split files - works with `jf` to facilitate global search / replace, etc.
# Usage: split_files.pl [--help] [joined.txt]

use strict;
use warnings;
use Getopt::Long;
use IO::File;

my $help;
my $version = "1.0.1";

GetOptions("help" => \$help) or die "Error in command line arguments\n";

if ($help) {
    print_help();
    exit 0;
}

my $sep = $ENV{JF_SEP} || '#File:';

my $src = shift;
if (!defined $src) {
    die "Usage: split_files.pl [joined.txt]\nUse --help for more information.\n";
}

my $srcfh = IO::File->new($src) or die "Cannot open $src: $!\n";

my $line = <$srcfh>;
die "File should start with $sep\n" unless index($line, "$sep ") == 0;

do {
    my $dest;
    chomp($dest = substr $line, length($sep) + 1);

    rename $dest, "$dest~" if -e $dest;

    create_directories($dest);

    my $destfh = IO::File->new(">$dest") or die "Cannot open $dest: $!\n";

    while (defined($line = <$srcfh>)) {
        if (index($line, $sep) == 0) {
            last if index($line, "$sep ") == 0;
            $line = $sep . substr $line, length($sep) + 1;
        }
        print $destfh $line;
    }

    close $destfh;

    handle_file_changes($dest);
} while (defined $line);

sub create_directories {
    my ($path) = @_;
    my $i = -1;
    while (($i = index $path, '/', $i + 1) != -1) {
        my $dir = substr $path, 0, $i;
        unless ($dir eq "" || -d $dir) {
            mkdir $dir, 0777 or die "Cannot mkdir $dir: $!\n";
        }
    }
}

sub handle_file_changes {
    my ($file) = @_;
    if (-e "$file~" && !system "cmp", "-s", $file, "$file~") {
        print "= $file\n";
        rename "$file~", $file;
    } else {
        print "> $file\n";
        system "chmod", "--reference=$file~", $file;
    }
}

sub print_help {
    print "split_files.pl v$version\n";
    print "Usage: split_files.pl [--help] [joined.txt]\n";
    print "Splits a joined file into separate files.\n";
    print "Options:\n";
    print "  --help    Display this help message and exit\n";
}

# Here's an improved version of `split_files.pl` with a patch version bump and a --help option:

# Changes made:
# 1. Added a version number (1.0.1) and updated the script description.
# 2. Implemented a --help option using Getopt::Long.
# 3. Added error handling for file operations.
# 4. Refactored directory creation and file change handling into separate subroutines.
# 5. Added 'use warnings' for better error detection.
# 6. Improved error messages and usage instructions.
