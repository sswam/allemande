#!/usr/bin/env perl

use strict;
use warnings;
use Test::More;
use File::Temp qw/ tempdir /;
use File::Spec;
use File::Basename qw(basename);

# Path to the script being tested
my $script = './join_files.pl';

# Create a temporary directory for test files
my $temp_dir = tempdir( CLEANUP => 1 );

# Test cases
my @tests = (
    {
        name => 'Basic join',
        files => [
            ['file1.txt', "Hello\nWorld\n"],
            ['file2.txt', "Foo\nBar\n"],
        ],
        expected => "#File: file1.txt\nHello\nWorld\n#File: file2.txt\nFoo\nBar\n",
    },
    {
        name => 'Join empty files',
        files => [
            ['empty1.txt', ''],
            ['empty2.txt', ''],
        ],
        expected => "#File: empty1.txt\n#File: empty2.txt\n",
    },
    {
        name => 'Join files with different line endings',
        files => [
            ['unix.txt', "Unix\nStyle\n"],
            ['windows.txt', "Windows\r\nStyle\r\n"],
        ],
        expected => "#File: unix.txt\nUnix\nStyle\n#File: windows.txt\nWindows\r\nStyle\r\n",
    },
);

# Count the number of tests
plan tests => scalar @tests;

# Run tests
for my $test (@tests) {
    # Create test files
    my @file_paths;
    for my $file (@{$test->{files}}) {
        my $file_path = File::Spec->catfile($temp_dir, $file->[0]);
        open my $fh, '>', $file_path or die "Could not open file '$file_path': $!";
        print $fh $file->[1];
        close $fh;
        push @file_paths, $file_path;
    }

    # Create output file path
    my $output_file = File::Spec->catfile($temp_dir, 'output.txt');

    # Run the script
    system($^X, $script, $output_file, @file_paths);

    # Read the output file
    open my $fh, '<', $output_file or die "Could not open file '$output_file': $!";
    my $output = do { local $/; <$fh> };
    close $fh;

    # Replace full paths with basenames in the output
    $output =~ s/#File: \Q$temp_dir\E\/(.*?)(\n|$)/#File: $1$2/g;

    # Check the result
    is($output, $test->{expected}, $test->{name});
}

done_testing();
