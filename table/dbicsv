#!/usr/bin/perl -w

# dbicsv - run an SQL query, return CSV data

use strict;
use warnings;
use utf8;
use open ':utf8';
use Data::Dumper;

use DBI;
use Text::CSV;
# use Text::TSV;  # copied inline
use Getopt::Long;
use File::Basename;
use File::Slurp 'slurp';
use Encode;

sub usage {
    my $prog = basename($0);
    return "Usage: $prog [options] sql-query [param ...]" . <<'End';

Runs an SQL query, returns CSV data.

  option     description            default

  -dbms ?    DBMS, determines DSN   $DB_DBMS || InterBase
  -dsn ?     DBI data source name   $DB_DSN || (from DBMS)
  -db ?      database name          $DB_NAME
  -user ?    database user          $DB_USER || $ISC_USER || "sysdba"
  -pass ?    database password      $DB_PASS || $ISC_PASSWORD || "sysdba"
  -host ?    database hostname      $DB_HOST
  -port ?    database port          $DB_PORT
  -sql ?     sql query file         expects SQL query on command line

  -in        input data from stdin  $DB_IN
  -ins       insert data            $DB_INS
  -pre       run SQL beforehand
  -head ?    column head = -|O|I|IO $DB_HEAD || IO
  -rollback  rollback, not commit   $DB_ROLLBACK
  -dates ?   date format            $DB_DATES || 'ISO' (%Y-%m-%d)
  -times ?   time format            $DB_TIMES || 'ISO' (%H:%M:%S.%f)
  -stamps ?  datetime format        $DB_STAMPS || 'ISO' (%Y-%m-%d %H:%M:%S.%f)
  -quoty ?   quote all non-NULL     1
  -error ?   e.g.: -error=id,error  $DB_ERROR
  -errall    put error row when ok  $DB_ERRALL
  -tsv       use TSV file format    $DB_TSV
  -timeout   connect timeout (secs) $DB_TIMEOUT
  -keep      keep input fields      0

  -debug     show more info         $DB_DEBUG
  -echo      echo input to stderr   $DB_ECHO
  -help      show this message
End
}

our $dbms_dsn_map = {
    interbase  => 'DBI:InterBase:dbname=$db;host=$host;port=$port;ib_dialect=3',
    firebird   => 'DBI:Firebird:dbname=$db;host=$host;port=$port;ib_dialect=3',
    mysql      => 'DBI:mysql:database=$db;host=$host;port=$port',
    postgresql => 'DBI:Pg:dbname=$db;host=$host;port=$port',
    sybase     => 'DBI:Sybase:database=$db;host=$host;port=$port',
};

our @drivers = DBI->available_drivers(1);

our $dbms     = $ENV{DB_DBMS}   || (grep({$_ eq "Firebird"} @drivers) ? "Firebird" : "InterBase");
our $dsn      = $ENV{DB_DSN};
our $db       = $ENV{DB_NAME}   || $ENV{DB_ALIAS} || "";
our $user     = $ENV{DB_USER}   || $ENV{ISC_USER} || "sysdba";
our $pass     = $ENV{DB_PASS}   || $ENV{DB_PASSWORD} || $ENV{ISC_PASSWORD} || "sysdba";
our $host     = $ENV{DB_HOST}   || "";
our $port     = $ENV{DB_PORT}   || "";
our $in       = $ENV{DB_IN}     || 0;
our $ins      = $ENV{DB_INS}    || 0;
our $head     = $ENV{DB_HEAD}   || 'IO';
our $rollback = $ENV{DB_ROLLBACK}  || 0;
our $dates    = $ENV{DB_DATES}  || 'ISO';
our $times    = $ENV{DB_TIMES}  || 'ISO';
our $stamps   = $ENV{DB_STAMPS} || 'ISO';
our $quoty    = exists $ENV{DB_QUOTY} ? $ENV{DB_QUOTY} : 1;
our $debug    = $ENV{DB_DEBUG}  || 0;
our $echo     = $ENV{DB_ECHO}   || 0;
our $error    = $ENV{DB_ERROR}  || "";
our $errall   = $ENV{DB_ERRALL} || 0;
our $use_tsv  = $ENV{DB_TSV}    || 0;
our $timeout  = $ENV{DB_TIMEOUT} || 0;
our $keep     = 0;
our $sql_pre  = '';
our $sql_file = "";
our $help;

sub debug {
    return if !$debug;
    my ($k, @v) = @_;    
    local $Data::Dumper::Indent = 0;
    my $v = Dumper(\@v);
    $v =~ s/.*?\[//;
    $v =~ s/\];$//;
    warn "$k: $v\n";
}

sub sym_name {
    my ($field_name) = @_;
    my $sym_name = $field_name;
    $sym_name =~ s/[^a-z0-9_]/_/gi;
    $sym_name =~ s/^([0-9])/_$1/;
    return $sym_name;
}

sub split_opt_list {
    my ($s) = @_;
    return [] if !defined $s || $s eq "";
    return [split /\s*,\s*/, $s];
}

sub timeout {
    my ($secs, $fn) = @_;
    if ($secs == 0) {
        return $fn->();
    }

    use POSIX ':signal_h';
     
    my $mask = POSIX::SigSet->new(SIGALRM);
    my $action = POSIX::SigAction->new(
        sub { die "database timeout\n" },
        $mask,
    );
    my $oldaction = POSIX::SigAction->new();
    sigaction(SIGALRM, $action, $oldaction);
    my $v;
    eval {
        alarm($secs);
        $v = $fn->();
    };
    alarm(0);
    sigaction(SIGALRM, $oldaction);
    if ($@) {
        die $@;
    }
    return $v;
}

sub main {
    GetOptions(
        "dbms=s"   => \$dbms,
        "dsn=s"    => \$dsn,
        "db=s"     => \$db,
        "user=s"   => \$user,
        "pass=s"   => \$pass,
        "host=s"   => \$host,
        "port=s"   => \$port,
        "in"       => \$in,
        "ins"      => \$ins,
        "head=s"   => \$head,
        "rollback" => \$rollback,
        "help"     => \$help,
        "debug"    => \$debug,
        "sql=s"    => \$sql_file,
        "dates=s"  => \$dates,
        "times=s"  => \$times,
        "stamps=s" => \$stamps,
        "quoty=s"  => \$quoty,
        "echo"     => \$echo,
        "error=s"  => \$error,
        "errall"   => \$errall,
        "tsv"      => \$use_tsv,
        "pre=s"    => \$sql_pre,
        "timeout=s" => \$timeout,
        "keep"     => \$keep,
    )
        or die "failed: GetOptions";

    if ($help) { print usage; exit(0); }

    my $query;
    if ($sql_file) {
        $query = slurp($sql_file);
    } else {
        $query = shift @ARGV;
    }
    if (!defined $query) { die usage; }

    my @params = @ARGV;

    if ($in and @params) {
        die "do not use -in with params on the command line";
    }
    if ($ins and !@params) {
        $in = 1;
    }

    # Strip comments at start of lines (would have to parse to strip comments starting mid-line).
    # This avoids trouble with named_bind_vars that are commented out.
    $query =~ s/^\s*--.*//gm;

    my $add_insert_names_values = 0;
    my $add_bind_markers = 0;
    if ($query !~ /\s/) {
        if ($ins) {
            $query = "insert into $query";
            $add_insert_names_values = 1;
        } else {
            $query = "select * from $query";
            $add_bind_markers = 1;
        }
    }

    my $rx_quoted = qr{(?:[^"']|"(?:[^"\\]|\\.)*"|'(?:[^'\\]|\\.)*')};

    my $error_vars = split_opt_list($error);
    my @error_vars_slice;

    my @named_bind_vars;
    my @named_bind_slice;
    my $add_named_bind_var = sub {
        my ($pre, $name) = @_;
        $name =~ s/\A\{|}\z//g;
        push @named_bind_vars, $name;
        return $pre."?";
    };
    $query =~ s/\G($rx_quoted*?(?:\A|[^a-z0-9_\$"']))\$(\w+|{.*?})/$add_named_bind_var->($1, $2)/gsie;
    debug "named_bind_vars", \@named_bind_vars;
    debug "query", $query;

    if ($host eq "" && $db =~ /:/) {
        ($host, $db) = split /:/, $db, 2;
    }

    if ($dsn) {
        ($dbms) = $dsn =~ /^DBI:(\w+)/i;
        $dbms ||= "unknown";
    } else {
        $dsn = $dbms_dsn_map->{lc $dbms}
            or die "unknown DBMS: $dbms, known are: @{[sort keys %$dbms_dsn_map]}.\nyou can set a DSN instead";
    }

    if ($dsn =~ s{\$db}{$db}) {
        if (!$db) {
            die "no database name was specified, use -db or -dsn";
        }
    }
    $dsn =~ s{\$host}{$host};
    $dsn =~ s{\$port}{$port};
    $dsn =~ s{\w+=(;|$)}{}g;
    $dsn =~ s{;$}{};

    debug "dsn", $dsn;

    my $dbh;
    timeout($timeout, sub {
        $dbh = DBI->connect($dsn, $user, $pass, { PrintError => 0, RaiseError => 1, AutoCommit => 0 });
    });

    # date / time formats
    # use ISO with milliseconds by default, to be sane and avoid losing data
    # TODO make sure other DBMSs are configured for this also
    if ($dbms =~ /^(interbase|firebird)$/i) {
        $dbh->{ib_dateformat} = $dates;
        $dbh->{ib_timeformat} = $times;
        $dbh->{ib_timestampformat} = $stamps ? $stamps : $dates eq 'ISO' ? 'ISO' : "$dates $times";
    } elsif ($dbms =~ /^sybase$/i) {
        if ($dates ne 'ISO' or $times ne 'ISO' or $stamps ne 'ISO') {
            warn "using ISO date/time format";
        }
        $dbh->syb_date_fmt('ISO');
    }

    if ($sql_pre) {
        $dbh->do($sql_pre);
    }

    my $csv;
    if ($use_tsv) {
        $csv = Text::TSV->new;
    } else {
        $csv = Text::CSV->new({ binary => 1, always_quote => $quoty, blank_is_undef => $quoty })
            or die "Cannot use CSV: ".Text::CSV->error_diag;
        $csv->eol("\n");
    }
    my $out = \*STDOUT;
    binmode($out, ":utf8");
    if ($in) {
        $in = \*STDIN;
        binmode($in, ":utf8");
    }

    my $sth;
    my $row_in = \@params;
    my $first = 1;
    my $first_error = 1;
    my $in_names;

    if ($in && $head =~ /I/) {
        $in_names = $csv->getline($in);
        if ($echo) {
            $csv->print(\*STDERR, $in_names);
        }
        if (!$in_names || grep {!defined} @$in_names) {
            die "bad input, bad or missing table header\n";
        }
        $_ = sym_name(lc($_)) for @$in_names;
        my %ix = map { $in_names->[$_] => $_ } 0..$#$in_names;
        my $fail = 0;
        for my $k (@named_bind_vars) {
            my $i = $ix{lc $k};
            if (!defined $i) {
                warn "missing column: $k\n";
                $fail = 1;
            }
            push @named_bind_slice, $i;
        }
        for my $k (@$error_vars) {
            my $i = $ix{lc $k};
            if ($k eq "error") {
                $i = -1;
            }
            if (!defined $i) {
                warn "missing column: $k\n";
                $fail = 1;
            }
            push @error_vars_slice, $i;
        }
        exit 1 if $fail;

        if ($add_insert_names_values) {
            my $n = @$in_names;
            $query .= "(". join(", ", @$in_names) .") VALUES (". join(", ", ("?") x $n) .")";
        }
    }

    while(1) {
        if ($in) {
            $row_in = $csv->getline($in);
            if (!$row_in) {
                $csv->eof or die $csv->error_diag();
                last;
            }
        }

        if ($first) {
            my $n = @$row_in;
            if ($add_bind_markers && $n) {
                $query .= "(". join(", ", ("?") x $n) .")";
            }
            debug "query", $query;
            $sth = $dbh->prepare($query);
            if (!$in_names) {
                $in_names = [map { "_$_" } 0..$n-1];
            }
        }

#        debug "input", @$row_in;

        my $row_bind = $row_in;
        if (@named_bind_slice) {
            $row_bind = [ @$row_in[@named_bind_slice] ];
#            debug "sliced", @$row_bind;
        }

        if ($echo && $in) {
            $csv->print(\*STDERR, $row_in);
        }

        eval {
            $sth->execute(@$row_bind);
        };

        my $error_message = $@;

        my $have_output = $sth->{NAME} && @{$sth->{NAME}};
        if ($have_output && $first && $head =~ /O/) {
            my $out_names = $sth->{NAME};
            if ($keep) {
                $out_names = [@$in_names, @$out_names];
            }
            $csv->print($out, $out_names)
                or die "failed: \$csv->print: $!";
        }

        if (!$error_message && $have_output) {
            while (1) {
                my $row_out = eval {
                    $sth->fetchrow_arrayref;
                };
                $error_message = $@;
                if ($error_message) {
                    $sth->finish;
                    last;
                }
                last if !$row_out;
                for (@$row_out) {
                    $_ = decode('utf8', $_);
                }
                if ($keep) {
                    $row_out = [@$row_in, @$row_out];
                }
                $csv->print($out, $row_out)
                    or die "failed: \$csv->print: $!";
            }
        }

        if ($error_message || $errall) {
            chomp $error_message;
            if (@$error_vars) {
                my @row_with_error = (@$row_in, $error_message||"");
                my $row_err = [@row_with_error[@error_vars_slice]];
                if ($first_error) {
                    $csv->print(\*STDERR, $error_vars);
                    $first_error = 0;
                }
                $csv->print(\*STDERR, $row_err);
            } else {
                warn "$@\n";
                if ($in) {
                    $csv->print(\*STDERR, $row_in);
                }
                die "\n";
            }
        }

        if (!$in) {
            last;
        }
        $first = 0;
    }

    close $out
        or die "failed: close: $!";

    if ($sth) {
        $sth->finish;  # for Sybase stored procs
        if ($rollback) {
            $dbh->rollback;
        } else {
            $dbh->commit;
        }
    }

    $dbh->disconnect;
}

main;

# TODO:
# 
# - use ISO date/time format by default for all drivers
# - other data formats: TSV, key:value; and perhaps: xls, xlsx, json, html, printf
#   - separate converters for this?
# - preserve delimiters and comments from input stream in output stream (how to format a comment?)
# - port to C using libdbi
#
# - -null option to show NULL in a special way ?
# - option to specify date and time formats?
# - -conf option to load config from a file
#     check for .dbconf in parent dirs?


package Text::TSV;
use strict;
use warnings;

sub new {
    my ($pkg) = @_;
    return bless { eol=>"\n", eof=>0 }, $pkg;
}

sub print {
    my ($self, $out, $f) = @_;
    my $line = join("\t", map { escape_tsv($_) } @$f) . $self->{eol};
    my $ok = print $out $line;
    if (!$ok) {
        $self->{error} = $!;
    }
    return $ok;
}

sub getline {
    my ($self, $in) = @_;
    my $old_err = $!;
    undef $!;
    my $line = <$in>;
    if (!defined $line && $!) {
        $self->{error} = $!;
        return undef;
    }
    $! = $old_err;
    if (!defined $line) {
        $self->{eof} = 1;
        return undef;
    }
    $line =~ s/\r?\n\z//s;
    my @f = map { unescape_tsv($_) } split /\t/, $line, -1;
    return \@f;
}

sub eof {
    my ($self) = @_;
    return $self->{eof};
}

sub eol {
    my ($self, $eol) = @_;
    $self->{eol} = $eol;
    return;
}

sub error_diag {
    my ($self) = @_;
    return $self->{error};
}

my %tsv_escape_map = (
    "\\" => "\\",
    "\t" => "t",
    "\n" => "n",
    "\r" => "r",
    "\0" => "0",
);
my %tsv_unescape_map = map { $tsv_escape_map{$_} => $_ } keys %tsv_escape_map;

sub escape_tsv {
        my $v = shift;
        return "\\" unless defined $v;
        for ($v) {
                s/([\\\t\n\r\0])/"\\".$tsv_escape_map{$1}/gse;
        }
        return $v;
}

sub unescape_tsv {
    my $v = shift;
    return undef if $v eq "\\";
    for ($v) {
        s/\\(.)/$tsv_unescape_map{$1}/gse;
    }
    return $v;
}

1
