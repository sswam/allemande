#!/usr/bin/perl -w
use strict;
use warnings;
use Data::Dumper;
use File::Basename;
use POSIX;
use Getopt::Long;

my $max = 10;
my $verbose = 0;
my $help = 0;

sub usage {
    my $prog = basename($0);
    print <<End;
$prog - run jobs in parallel

usage: $prog < commands.sh

option    descrition          default
-n num    max jobs at once    10
-v        verbose             off
-h        help
End
    exit(0);
}

GetOptions(
    "num=i" => \$max,
    "verbose" => \$verbose,
    "help" => \$help,
)
    or usage();
usage() if $help;


local $|=1;

our $count = 0;
our $status = 0;
our $job = 1;
our %pid_to_job_cmd;

sub wait1 {
    my $kid;
    do {
        $kid = waitpid(-1, 0);
    } until $kid > 0;
    --$count;
    my $my_status;
    if (WIFEXITED($?)) {
        $my_status ||= WEXITSTATUS($?);
    } elsif (WIFSIGNALED($?)) {
        $my_status ||= 128+WTERMSIG($?);
    }
    $status ||= $my_status;
    my ($job, $cmd) = @{$pid_to_job_cmd{$kid}};
    warn sprintf("%-5d %d: %s\n", $my_status, $job, $cmd) if $verbose;
}

while (my $cmd = <STDIN>) {
    chomp $cmd;
    next if $cmd eq "";
    while ($count >= $max) {
        wait1();
    }
    my $kid = fork();
    die "fork failed: $!" if !defined $kid;
    if ($kid == 0) {
        exec $cmd;
        die "exec failed: $cmd";
    }
    $pid_to_job_cmd{$kid} = [$job, $cmd];
    warn "start $job: $cmd\n" if $verbose;
    ++$count;
    ++$job;
}
while ($count > 0) {
    wait1();
}

exit($status);
