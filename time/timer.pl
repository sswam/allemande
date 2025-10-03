#!/usr/bin/env perl

use strict;
use warnings;
use autodie;
use v5.30;
use utf8;
use open         qw(:std :utf8);
use Getopt::Long qw(GetOptions);
# use Pod::Usage   qw(pod2usage);
# use FindBin      qw($RealBin);
use Time::HiRes  qw(time sleep);
use IPC::Run3;
use IO::Handle;
# use lib "$RealBin/lib";
# use ally::main qw(setup_logging get_logger);

our $VERSION = '0.1.2';

# Set up command-line options
my %opts = (
    message  => '',
    m        => '',
    progress => 0,
    p        => 0,
    help     => 0,
);

GetOptions(
    'message|m=s' => \$opts{message},
    'progress|p'  => \$opts{progress},
    'help|h'      => \$opts{help},
) or pod2usage(2);

pod2usage(-exitval => 0, -output => \*STDOUT, -noperldoc => 1, -verbose => 2) if $opts{help};

# Set up logging
# setup_logging('timer');
# my $logger = get_logger();

# Main function
sub timer {
    my $duration = shift @ARGV;

    if (!defined $duration || $duration eq '') {
        die "duration required\n";
    }

    my $message = $opts{message} || "Timer finished!";

    if ($opts{progress} && $duration ne '' && -t STDOUT) {
        # Show progress indicator using precise timing
        my $start_time = time();

        for (my $i = $duration; $i > 0; $i--) {
            printf "\r%d ", $i;
            STDOUT->flush();

            # Calculate when the next second should be
            my $next_second_time = $start_time + ($duration - $i + 1);
            my $sleep_duration = $next_second_time - time();

            # Sleep until the next exact second point
            if ($sleep_duration > 0) {
                sleep($sleep_duration);
            }
        }
        print "\n";
    } else {
        # No progress, just sleep for the duration
        sleep($duration);
    }

    # Call notify with the message
    run3 ['notify', $message], undef, undef, undef;
}

# Run the main function
timer();

__END__

=head1 NAME

timer.pl - Wait for given duration, then show notification

=head1 SYNOPSIS

timer.pl [options] <duration> [command...]

Options:
--message, -m MESSAGE  Show custom message when time is up
--progress, -p         Show progress indicator
--help, -h             Show this help message

Arguments:
duration               Duration to wait (e.g., 10, 10s, 60)
command                Optional command to run after timer (not yet implemented)

=head1 DESCRIPTION

This script waits for the given duration and then shows a notification.
If stdout is a terminal, it displays a progress indicator with precise
second-by-second countdown using Time::HiRes for accurate timing.

=head1 EXAMPLES

timer.pl 10
timer.pl 30s
timer.pl --message "Tea is ready!" 180

=cut
