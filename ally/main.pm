package ally::main;

use strict;
use warnings;
use v5.30;
use Exporter qw(import);
use Log::Log4perl; # qw(:easy);
use IO::Handle;

our $VERSION = "0.1.3";

our @EXPORT_OK = qw(setup_logging get_logger io);

sub setup_logging {
    my ($module_name) = @_;

    my $log_level = $ENV{uc($module_name) . '_LOG_LEVEL'} // 'WARN';

    my $log_config = qq{
        log4perl.rootLogger              = $log_level, Screen, File

        log4perl.appender.Screen         = Log::Log4perl::Appender::Screen
        log4perl.appender.Screen.stderr  = 0
        log4perl.appender.Screen.layout  = PatternLayout
        log4perl.appender.Screen.layout.ConversionPattern = %m%n

        log4perl.appender.File           = Log::Log4perl::Appender::File
        log4perl.appender.File.filename  = $ENV{HOME}/.logs/$module_name.log
        log4perl.appender.File.mode      = append
        log4perl.appender.File.layout    = PatternLayout
        log4perl.appender.File.layout.ConversionPattern = %d %p %m%n
    };

    Log::Log4perl->init(\$log_config);
}

sub get_logger {
    return Log::Log4perl->get_logger();
}

sub io {
    my ($input, $output) = @_;

    $input  //= \*STDIN;
    $output //= \*STDOUT;

    my $is_tty = -t $input && -t $output;

    my $put = sub {
        my ($message, %opts) = @_;
        my $end = $opts{end} // "\n";
        print $output $message . $end;
    };

    my $get = sub {
        my ($prompt) = @_;
        $prompt //= ': ';
        if ($is_tty) {
            print $output $prompt;
            $output->flush();
            return scalar <$input>;
        } else {
            return scalar <$input>;
        }
    };

    return ($get, $put);
}

1;
