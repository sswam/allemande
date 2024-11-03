#!/usr/bin/env perl

use strict;
use warnings;
use autodie;
use v5.30;
use utf8;
use open         qw(:std :utf8);
use Getopt::Long qw(GetOptions);
use Pod::Usage   qw(pod2usage);
use FindBin      qw($RealBin);
use IPC::Run3;
use lib "$RealBin/lib";
use ally::main qw(setup_logging get_logger io);

our $VERSION = '1.0.0';

# Set up command-line options
my %opts = (
    name  => '',
    ai    => 0,
    model => '',
    help  => 0,
);

GetOptions(
    'name=s'  => \$opts{name},
    'ai'      => \$opts{ai},
    'model=s' => \$opts{model},
    'help|h'  => \$opts{help},
) or pod2usage(2);

pod2usage(-exitval => 0, -output => \*STDOUT, -noperldoc => 1, -verbose => 2) if $opts{help};

# Set up logging
setup_logging('hello_pl');
my $logger = get_logger();

# Main function
sub hello_pl {
    my ( $input, $output ) = @_;

    my ( $get, $put ) = io( $input, $output );

    my $say = sub {
        my ($message) = @_;
        $put->($message . "\n");
    };

    my $name = $opts{name} || 'world';

    $say->("Hello, $name");
    $say->("How are you feeling?");

    my $feeling = $get->();

    my $response;
    if (   $feeling =~ /^(lucky|unlucky|fortunate|unfortunate)$/
        || $feeling eq '' )
    {
        $logger->info("Using fortune(1)");
        $response = `fortune`;
    }
    elsif ( $opts{ai} ) {
        $logger->info("Using AI model");
        $response = reply_ai( $name, $feeling, $opts{model} );
    }
    else {
        $logger->info("Using sentiment analysis");
        $response = reply_sentiment($feeling);
    }

    $say->($response);
}

sub reply_ai {
    my ( $name, $feeling, $model ) = @_;
    my $prompt =
        "Scenario: Your character asked 'How are you feeling?' "
      . "and $name said '$feeling'. "
      . "Please reply directly without any prelude, disclaimers or explanation.";

    my $output;
    run3 [ 'llm', 'query', '-m', $model, $prompt ], \undef, \$output, \undef;
    my $response = $output;

    $response =~ s/^\s+|\s+$//g;    # Trim whitespace
    $response =~ s/^"(.*)"$/$1/;    # Remove surrounding quotes if present

    return $response;
}

sub reply_sentiment {
    my ($feeling) = @_;

    # This is a very simplistic sentiment analysis
    if ( $feeling =~ /good|great|happy|excellent/i ) {
        return "I hope you have a great day!";
    }
    elsif ( $feeling =~ /bad|sad|terrible|awful/i ) {
        return "I hope you feel better soon.";
    }
    else {
        return "Life has its ups and downs, hope yours swings up!";
    }
}

# Run the main function
hello_pl( \*STDIN, \*STDOUT );

__END__

=head1 NAME

hello.pl - An example Perl script to say hello and ask how the user is feeling

=head1 SYNOPSIS

hello.pl [options]

 Options:
   --name NAME    Name to be greeted
   --ai           Use AI to respond
   --model MODEL  Specify which AI model to use
   --help         Show this help message

=head1 DESCRIPTION

This script greets the user and asks how they're feeling. It can use different
methods to generate a response, including fortune cookies, AI, or simple
sentiment analysis.

=cut


Important Notes for AI [DO NOT COPY THEM IN YOUR OUTPUT!]:

Do not remove comments, logging or blank lines, especially not TODO, FIXME, XXX.
Do not remove ANYTHING unnecessarily. If you are 1000% sure something is wrong,
comment it out rather than removing it.

AVOID DEEP INDENTATON OR NESTING, it's better to use if/elif or a function.
If needed, we can use variables to avoid repeating parts of conditions.
This is the number one rule!

We use autodie, so be careful to avoid accidentally exiting.
Generally, if things go wrong, die rather than continuing.

If sensible and simple to do so, write tools that can process several files in one invocation.  # XXX not sure
Zero is holy! It is not an error to pass zero files to process. Just naturally do nothing in that case.

Stdout is only for normal output. Use logging for info, warning or error messages.

When writing other scripts based on this one, please do not include these notes!
