#!/usr/bin/perl
use strict;
use warnings;
use Test::More;
use File::Temp qw/ tempdir /;
use File::Slurp qw/ write_file read_file /;

my $script = './split_files.pl';

# Test 1: Check if the script runs without arguments
my $output = `$script 2>&1`;
like($output, qr/Usage:/, 'Script shows usage when run without arguments');

# Test 2: Check --help option
$output = `$script --help`;
like($output, qr/Usage:.*Options:/s, '--help option displays help message');

# Test 3: Test actual file splitting
my $tempdir = tempdir( CLEANUP => 1 );
my $joined_file = "$tempdir/joined.txt";
my $content = <<EOF;
#File: $tempdir/file1.txt
Content of file1
#File: $tempdir/file2.txt
Content of file2
EOF

write_file($joined_file, $content);

system($script, $joined_file);

ok(-f "$tempdir/file1.txt", 'file1.txt was created');
ok(-f "$tempdir/file2.txt", 'file2.txt was created');

is(read_file("$tempdir/file1.txt"), "Content of file1\n", 'file1.txt has correct content');
is(read_file("$tempdir/file2.txt"), "Content of file2\n", 'file2.txt has correct content');

done_testing();
