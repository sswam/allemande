package ally::main;

use strict;
use warnings;
use v5.30;
use Exporter qw(import);
use Log::Log4perl;
use IO::Handle;
use Term::ReadLine;
use IO::Interactive qw(is_interactive);
use File::Basename  qw(basename);
use File::Spec;

our $VERSION = "0.1.9";

our @EXPORT_OK = qw(setup_logging get_logger io);

# Shared variables for the io function
our $TERM;
our $HISTORY_FILE;

sub setup_logging {
    my ($module_name) = @_;

    die "Module name is required" unless defined $module_name;

    my $log_level = $ENV{ uc($module_name) . '_LOG_LEVEL' } // 'WARN';
    my $log_dir   = "$ENV{HOME}/.logs";
    mkdir $log_dir unless -d $log_dir;

    my $log_config = qq{
        log4perl.rootLogger              = $log_level, Screen, File

        log4perl.appender.Screen         = Log::Log4perl::Appender::Screen
        log4perl.appender.Screen.stderr  = 1
        log4perl.appender.Screen.layout  = PatternLayout
        log4perl.appender.Screen.layout.ConversionPattern = %m%n

        log4perl.appender.File           = Log::Log4perl::Appender::File
        log4perl.appender.File.filename  = $log_dir/$module_name.log
        log4perl.appender.File.mode      = append
        log4perl.appender.File.layout    = PatternLayout
        log4perl.appender.File.layout.ConversionPattern = %d %p %m%n
    };

    Log::Log4perl->init( \$log_config );
}

sub get_logger {
    return Log::Log4perl->get_logger();
}

sub io {
    my ( $input, $output ) = @_;

    $input  //= \*STDIN;
    $output //= \*STDOUT;

    my $is_interactive = is_interactive();

    if ($is_interactive) {
        $TERM = Term::ReadLine->new('ally');
        $HISTORY_FILE =
        File::Spec->catfile( $ENV{HOME}, "." . basename($0) . "_history" );

        $TERM->ReadHistory($HISTORY_FILE) if -f $HISTORY_FILE;

        END {
            $TERM->WriteHistory($HISTORY_FILE) if defined $TERM;
        }
    }

    return (
        sub {    # get
            my ($prompt) = @_;
            return $is_interactive
            ? do {
                my $line = $TERM->readline( $prompt // ': ' );
                $TERM->add_history($line) if defined($line) && length($line);
                $line;
            }
            : scalar <$input>;
        },
        sub {    # put
            print $output $_[0];
        }
    );
}

1;
