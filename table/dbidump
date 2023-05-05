#!/usr/bin/perl -w

=head1 NAME

dbidump - dump a database table to a file

=head1 SYNOPSIS

dbidump [options] table

=head1 DESCRIPTION

This program dumps a database table to a file.

=head1 OPTIONS

=over 4

=item B<-h>, B<--help>

=cut

use strict;
use warnings;

our $PROGRAM = "dbidump";
our $VERSION = "2.0";
our $USAGE = "usage: $PROGRAM [general options] command [command options]";

sub version {
	print <<End;
dbidump $VERSION
Copyright (C) 1997-2004 myinternet Limited.
Copyright (C) 2004-2023 Sam Watkins.

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
End
	exit 0;
}

use vars qw($debug);

#use DBP ':all';
use DBI;
use IO::File;
use POSIX;

$debug = 0;

##### for the time being, I have copied the subs from DBP.pm into this utility to make it self-sufficient
#

sub fatal {
	print STDERR "@_\n";
	exit 1;
}

=head2 build_dsn

The idea is to build a DBI datasource specifier based on information that the
user has specified on the command line: the DBMS, user-name, password,
hostname, port.  In order for this to work properly, it needs to have built-in
support for the particular DBMS.  If it doesn't, you can still use the function,
by supplying a DBI DSN in place of the DBMS, but with a `_' instead of the
database name.  In that case, the function will substitute the database name
into the DSN.

=cut

my %dbi_drivers = map {lc $_, $_} DBI->available_drivers;

my $quote = "";

my %dbms_build_dsn = (
	Pg => sub {
		my ($database, $host, $port, $rest) = @_;
		my $ret = "dbname=$database";
		$ret .= ";host=$host" if defined $host;
		$ret .= ";port=$port" if defined $port;
		$ret .= ";$rest" if defined $rest;
		$quote = '"';
		return $ret;
	},
	mSQL => sub {
		my ($database, $host, $port, $rest) = @_;
		$host = "localhost" if !defined $host; # I think this is not needed in general, just on my dodgy setup!
		my $ret = "database=$database";
		$ret .= ";host=$host" if defined $host;
		$ret .= ";port=$port" if defined $port;
		$ret .= ";$rest" if defined $rest;
		return $ret;
	},
	mysql => sub {
		my ($database, $host, $port, $rest) = @_;
		my $ret = "database=$database";
		$ret .= ";host=$host" if defined $host;
		$ret .= ";port=$port" if defined $port;
		$ret .= ";$rest" if defined $rest;
		$quote = '`';
		return $ret;
	}
);
sub build_dsn {
        my ($dbms, $database, $host, $port) = @_;

        $host = "localhost" if defined $port && !defined $host;
        fatal "build_dsn: \$dbms and \$database are required parameters"
                if !defined $dbms || !defined $database;

        $dbms =~ s/^dbi://;
	my $rest;
        $rest = $1 if $dbms =~ s/:(.*)//;

	# be case-insensitive
	if (my $tmp = $dbi_drivers{lc $dbms}) {
		$dbms = $tmp;
	} else {
		fatal "There is no DBI driver for DBMS `$dbms'";
	}

	if (my $sub = $dbms_build_dsn{$dbms}) {
		$rest = $sub->($database, $host, $port, $rest);
	} else {
                if (defined $rest && !defined $host && !defined $port) {
                        if (defined $database && !($rest =~ s/(\_|\*|DB)/$database/)) {
                                fatal q{cannot substitute database into DSN - missing `_'.
You need to put an `_' in the DSN where the database name should be
substituted.};
                        }
		} else {
			fatal qq{The DBMS `$dbms' is not known to dbidump - you need to specify a
full DBI DSN in place of the DBMS, and put an `_' in this DSN
where the database name should be substituted.  If you need to
specify a host or port, put them directly into the DSN.};
		}
	}

	my $dsn = "dbi:$dbms:$rest";

	return ($dbms, $dsn);
}

=head2 write_sql

This function returns a function that can be used to write data to a database

=cut

sub write_sql {
	my ($dbh, $table, $fields, $numeric, $coerce_nulls, $fix_dates, $commit_every) = @_;
	my $sql = "INSERT INTO $quote$table$quote (".(join ',', map {"$quote$_$quote"} @$fields).") VALUES (".'?,'x$#$fields.'?)';
	return $commit_every ?
		sql_insert_commit_every($dbh, $sql, $numeric, $coerce_nulls, $fix_dates, $commit_every) :
		sql_insert($dbh, $sql, $numeric, $coerce_nulls, $fix_dates);
}

=head2 sql_insert

This function returns a function that can be used to write data to a database

=cut

sub sql_insert {
	my ($dbh, $sql, $numeric, $coerce_nulls, $fix_dates) = @_;
	my ($sth);

	my $n = @$numeric;
	
	$sth = $dbh->prepare($sql)
		or die "cannot prepare sql insert: ". $dbh->errstr.
		       "  $sql\n";
	return sub {
		my $row = shift;
		if (defined $row) {
			# make certain fields numeric if necessary - this is inefficient, I know
			for (my $i=0; $i<@$numeric; ++$i) {
				if ($coerce_nulls->[$i] && !defined $row->[$i])
				{
					if ($numeric->[$i]) {
						$row->[$i] = 0;
					} else {
						$row->[$i] = '';
					}
				} elsif ($numeric->[$i] && defined $row->[$i]) {
					my $new = 0 + $row->[$i];
					# bogosity to convert strings to booleans...
					if ($new == 0 && $row->[$i] !~ /^([0\.]*|false|no|n|off)$/i) {
						$new = 1;
					}
					$row->[$i] = $new;
				} elsif ($fix_dates->[$i] && defined $row->[$i]) {
					$row->[$i] = Field->fix_date($row->[$i]);
				}
			}
			if ((my $N = @$row) != $n) {
				my $S = $N == 1 ? '' : 's';
				print STDERR "\nrow has $N field$S : should have $n\n";
				return 0;
			}
			$sth->execute(@$row)
				or return 0;
		} else {
			$sth->finish;
		}
		return 1;
	}
}

=head2 sql_insert_commit_every

This function returns a function that can be used to write data to a database
and commit every N rows

=cut

sub sql_insert_commit_every {
	my ($dbh, $sql, $numeric, $coerce_nulls, $fix_dates, $commit_every) = @_;
	my $inserter = sql_insert($dbh, $sql, $numeric, $coerce_nulls, $fix_dates);
	my $count = 0;
	return sub {
		my $row = shift;
		my $success = &$inserter($row);
		$dbh->commit if (not defined $row or $success and ++$count % $commit_every == 0);
		return $success;
	}
}

=head2 read_sql

This function returns a function that can be used to read data from a database

=cut

sub read_sql {
	my ($dbh, $table) = @_;
	return sql_query($dbh, "SELECT * FROM $quote$table$quote");
}

=head2 sql_query

This function returns a function that can be used to read data from a database

=cut

sub sql_query {
	my ($dbh, $sql) = @_;
	my $sth;
	
	$sth = $dbh->prepare($sql)
		or die "cannot prepare sql query: ", $dbh->errstr,
		"  $sql\n";
	
	$sth->execute
		or die "cannot execute query: ", $dbh->errstr,
		"  $sql\n";
	
	return
		sub {
			my $row = $sth->fetchrow_arrayref;
			if (defined $row) {
				return [@{$row}];
			} else {
				undef $sth; #->finish;
				return undef;
			}
		},
        [@{$sth->{NAME}}];
}

=head2 escape_dump

This function escapes tabs to \t, newlines to \n, null to \0, \ to \\, and undef to null

=cut

# this function escapes tabs to \t, newlines to \n, null to \0, \ to \\, and undef to null
sub escape_dump {
	my $v = shift;
	return "\0" unless defined $v;
	for ($v) {
		s/\\/\\\\/g;
		s/\t/\\t/g;
		s/\n/\\n/g;
		s/\0/\\0/g;
	}
	return $v;
}

=head2 unescape_dump

This function unescapes tabs to \t, newlines to \n, null to \0, \ to \\, and undef to null

=cut

sub unescape_dump {
	my $v = shift;
	return undef if $v eq "\0";
	for ($v) {
		s/(?:(?<=[^\\])|^)((?:\\\\)*)\\0/$1\0/g;
		s/(?:(?<=[^\\])|^)((?:\\\\)*)\\n/$1\n/g;
		s/(?:(?<=[^\\])|^)((?:\\\\)*)\\t/$1\t/g;
		s/\\\\/\\/g;
	}
	return $v;
}

=head2 parse_row_dump

This function parses a row from a dump file

=cut

sub parse_row_dump {
	my $row = shift;
	return undef unless $row =~ s/^\t//;
	chomp $row;
	my @row = split /\t/, $row, -1;
	for (@row) { $_ = unescape_dump($_); }
	return \@row;
}

=head2 format_row_dump

This function formats a row for dumping to a file

=cut

sub format_row_dump {
	my $ra_row = shift;
	return defined $ra_row
		? (join '', (map {"\t".escape_dump($_)} @$ra_row)) . "\n"
		: undef;
}

=head2 write_file

This function returns a function which can be used to output text to a file

=cut

# returns a function which can be used to output text to a file
# parameter may be a filehandle ref, or nothing (for STDOUT), '>filename' or '>>filename'
sub write_file {
	my $filespec = shift;
	my $fh;
	
	$filespec = \*STDOUT unless defined $filespec;
	
	if (ref $filespec) {
		$fh = $filespec;
	} else {
		$fh = new IO::File($filespec)
			or die "cannot open $filespec: $!";
	}
	
	return sub {
		my $line = shift;
		defined $line
			? print $fh $line
			: undef $fh; # or close $fh
	}
}

=head2 read_file

This function returns a function which can be used to read text from a file

=cut

sub read_file {
	my $filespec = shift || \*STDIN;
	
	my $fh;
	if (ref $filespec) {
		$fh = $filespec;
	} else {
		$fh = new IO::File($filespec)
		or die "cannot open $filespec: $!";
	}
	
	return sub { scalar(<$fh>) }
}

=head2 write_string

This function returns a function which can be used to output text to a string

=cut

sub write_string {
	my $text = '';
	return (
		sub {
			my $line = shift;
			defined $line and $text .= $line;
		},
		\$text
        );
}

=head2 read_string

This function returns a function which can be used to read text from a string

=cut

sub read_string {
	my $text = shift; # local copy
	return (
		sub {
			return undef unless defined $text;
			my $line;
			($line, $text) = split /\n/, $text, 2;
			return $line;
		},
		\$text
        );
}

=head2 write_dump

This function returns a function which can be used to output a row to a dump file

=cut

sub write_dump {
	my $text_writer = shift;
	
	return sub {
		my $row = shift;
		&$text_writer(format_row_dump($row));
	}
}

=head2 read_dump

This function returns a function which can be used to read a row from a dump file

=cut

# read_dump ignores comments (lines that don't start with a tab)
sub read_dump {
	my $text_reader = shift;
	
	return sub {
		my ($line, $row);
		do {
			$line = &$text_reader;
			return undef unless defined $line;
			$row = parse_row_dump($line);
		} until (defined $row);
		
		return $row;
	}
}

=head2 write_dump_file

This function returns a function which can be used to output a row to a dump file

=cut

sub write_dump_file {
	my ($table, $fields) = @_;
	my $dump_writer = write_dump(write_file(">$table"));
	&$dump_writer($fields);
	return $dump_writer;
}

=head2 read_dump_file

This function returns a function which can be used to read a row from a dump file

=cut

sub read_dump_file {
	my ($table) = @_;
	my $text_reader = read_file("<$table");
	my $dump_reader = read_dump($text_reader);
	return $dump_reader, &$dump_reader;
}

#
##### end, copy of DBP.pm functions

$| = 1;

# CONSTANTS:
my $dot_every = 100; # hard coded 'option'!

#-----------------------------------------------------------------------
# parse options
#-----------------------------------------------------------------------

# TODO move many options to be command options, and integrate with dbischema?

my $commit_every = 0; # commit every 256 records by default - 0 for autocommit
my $quiet = 1;
my $wipe = 0;
my $append = 0;
my $log = 0;
my $format = 'dump';
my $sort;
my $mode;
my $schema;
my $schema_database;
my $coerce_nulls;
my $dbms;
my $user;
my $pass;
my $host;
my $port;
my $dsn;
my $database;
my @numeric; # which fields of a table are numeric
my @coerce_nulls; # which fields of a table should be converted to blank from null
my $fix_dates;
my @fix_dates; # which fields of a table are dates to be fixed

my @problem_tables;
my $failed;
my $directory;

=head2 help

This function prints the help text

=cut

sub help {
	print <<End;
$USAGE

general options:
  --help, --version   print help or version
  -d, --dbms dbms     specify the DBMS (or a DBI data source spec)
  -u, --user user     user name for accessing the DBMS
  -p, --pass pass     password for accessing the DBMS
  -h, --host host     database server host
  -P, --port port     database server TCP port
  -c, --commit count  commit every 'count' rows (default 256)
  -C, --auto-commit   in restore mode, autocommit (default)
  -v, --verbose       put dots in the commentary
  -q, --quiet         no commentary
  -W, --wipe          wipe tables (or dump files) before inserting
  -A, --append        append rows to tables (or .dump files)
  -l, --log           log insert errors for 'foo' to 'foo.X.dump'
  -s, --schema file   specify a dbischema file for this database
  -H, --html          produce HTML as output of dump
  -t, --tsv           produce 'normal' TSV as output of dump
  -n, --text          produce neat text as output of dump
  -S, --sort          pipe the output (or diff input) through sort -n
  -D, --dir dir       change to the specified directory first
  -N, --coerce-nulls  allow nulls to become blanks (with --schema)
  -f, --fix-dates     fix mysql dates for PostgreSQL (with --schema)

commands:
  dump database [opts]       dump from database to files
  restore database [opts]    restore from files to database
  convert [database] [opts]  convert a .dump file in some way
  diff old new [opts]        compare (directories of) .dump files

dump/restore/convert command options:
  -t tables           process only these tables
  -T tables           process all tables except these
  -t table options    process a single table, with these options
single table options:
  -f fields           include only these fields
  -F fields           exclude these fields
  -w, --where where   select rows matching this 'WHERE' expression
  -r from,to ...      rename fields

diff command options:
  -S, --mysql-spaces  ignore trailing spaces (mysql strips them)
  -Z, --msql-zeros    ignore trailing \\0s (mSQL strips them)
End
        exit 0;
}

# parse options

while (1) {
	$_ = shift;
	last unless defined $_ and s/^-(.+)$/$1/;
	
	if (/^-help$/) {
		help();
	} elsif (/^-version$/) {
		version();
	} elsif (/^d$/ || /^-dbms$/) {
		$dbms = shift || fatal "you did not specify a dbms after -$_";
	} elsif (/^u$/ || /^-user$/) {
		$user = shift || fatal "you did not specify a user name after -$_";
	} elsif (/^p$/ || /^-pass$/) {
		$pass = shift || fatal "you did not specify a password after -$_";
	} elsif (/^h$/ || /^-host$/) {
		$host = shift || fatal "you did not specify a host name after -$_";
	} elsif (/^P$/ || /^-port$/) {
		$port = shift || fatal "you did not specify a port after -$_";
	} elsif (/^c$/ || /^-commit$/) {
		$commit_every = $ARGV[0] =~ /^\d/ ? shift : 256; # slightly dodgy
	} elsif (/^C$/ || /^-auto-commit$/) {
		$commit_every = 0;
	} elsif (/^v$/ || /^-verbose$/) {
		$quiet = 0;
	} elsif (/^q$/ || /^-quiet$/) {
		$quiet = 2;
	} elsif (/^W$/ || /^-wipe$/) {
		$wipe = 1;
	} elsif (/^A$/ || /^-append$/) {
		$append = 1;
	} elsif (/^l$/ || /^-log$/) {
		$log = 1;
	} elsif (/^s$/ || /^-schema$/) {
		$schema = shift || fatal "you did not specify a schema file after -$_";
		local $^W = 0 unless $debug;
		my $lib_dir;
		($lib_dir = $0) =~ s|[^/]+$|../lib/dbischema|;
		if (! -d $lib_dir) {
			for (@INC) { if (/dbischema/) { $lib_dir = $_; last; } }
		}
		if (! -d $lib_dir) {
			for ('/usr/lib/dbischema', '/usr/local/lib/dbischema') {
				if (-d $_) { $lib_dir = $_; last }
			}
		}
		eval qq{
		use lib '$lib_dir'; use XMLParser; use Schema; use Field;
		};
		die "cannot find dbischema libs: $@" if $@;
		$schema = XMLParser->new->parsefile($schema);
	} elsif (/^H$/ || /^-html$/) {
		$format = 'html';
	} elsif (/^t$/ || /^-tsv$/) {
		$format = 'tsv';
	} elsif (/^n$/ || /^-text$/) {
		$format = 'txt';
	} elsif (/^S$/ || /^-sort$/) {
		$sort = 1;
	} elsif (/^D$/ || /^-dir$/) {
		$directory = shift || fatal "you did not specify a working directory after -$_";
	} elsif (/^N$/ || /^-coerce-nulls$/) {
		$coerce_nulls = 1;
	} elsif (/^f$/ || /^-fix-dates$/) {
		$fix_dates = 1;
	} else {
		fatal "unexpected option -$_";
	}
}

if (defined $directory) {
	mkdir $directory, 0777 unless -d $directory;
	chdir $directory || fatal "cannot change to directory `$directory'";
}

$mode = $_;
if (! defined $mode or ($mode !~ /^(dump|restore|convert|diff)$/)) {
	print STDERR <<End;
$USAGE

  for help, try the --help option
End
	exit 1;
}

if ($mode =~ /dump|restore|convert/ &&
    ($fix_dates || $coerce_nulls) && !$schema) {
	fatal "the --schema option is required for --coerce-nulls or --fix-dates";
}

if ($wipe and $append) {
	fatal "cannot use --wipe and --append together!";
}

my $dbh;
if ($mode =~ /^(restore|dump)$/) {
	# need to access the database

#-----------------------------------------------------------------------
# read the database name, work out dsn ; and connect to database
#-----------------------------------------------------------------------

	$dbms || fatal "you did not specify the dbms";
	$database = shift || fatal "you did not specify a database";

	($dbms, $dsn) = build_dsn($dbms, $database, $host, $port);
	print "connecting to $dsn\n" unless $quiet == 2;

	# connect to the database
	TRY: {
		local $^W = 0;
		eval {
			$dbh = DBI->connect($dsn, $user, $pass, {
				PrintError => 0,
				AutoCommit => $commit_every ? 0 : 1
			});

            # set date/time formats for firebird / interbase
            if ($dsn =~ m{^dbi:InterBase}) {
                $dbh->{ib_timestampformat}  = '%Y-%m-%d %H:%M:%S.0000';
                $dbh->{ib_dateformat}       = '%Y-%m-%d';
                $dbh->{ib_timeformat}       = '%H:%M:%S';
            }
		};
		if ($@ ne '') {
			if ($commit_every) {
				warn $@;
				# an error occurred, it might be due to autocommit = 0, try again without...
				$commit_every = 0;
				redo TRY;
			}
			die $@;
		}
	}
	unless ($dbh) { die "cannot connect: $DBI::errstr"; }
} elsif ($mode eq "convert") {
	# they may have specified the database (for use with the schema file)
	if (defined $ARGV[0] && $ARGV[0] !~ /^-/) {
		$database = shift;
	}
}

my %rename_table = ();

if ($schema) {
	if ($database) {
		$schema_database = $schema->database($database) ||
			fatal "database `$database' is not in the schema";
	} else {
		my @databases = $schema->databases;
		fatal "there are no databases in the schema" if @databases == 0;
		fatal "you must specify the database name (the schema contains more than one)" if @databases != 1;
		$schema_database = $databases[0];
	}

	# look for old table names, for auto-rename function
	for my $table ($schema_database->tables) {
		my $name = $table->name;
		if (my $olds = $table->old) {
			for my $old (split /,\s*/, $olds) {
				$rename_table{$old} = $name
					unless $schema_database->table($old);
			}
		}
	}
}

if ($sort and $mode eq "restore") {
	fatal "it's silly to sort when restoring!";
}

if ($sort and $format ne "dump") {
	fatal "can only sort .dump format";
}

my $table_command = '';
my $field_command = '';
my $where_clause = '';
my @table_params = ();
my @field_params = ();
my %field_params = ();
my %rename_field = ();

my $ignore_trailing_spaces = 0;
my $ignore_trailing_zeros = 0;

if ($mode =~ /^(dump|restore|convert)$/) {
	#-----------------------------------------------------------------------
	# parse command options for dump / restore / convert
	#-----------------------------------------------------------------------
	
	# parse command options
	while(1) {
		local $_ = shift;
		last unless defined $_;
		unless (s/^-(.)$/$1/) {
			fatal "bad command option: $_";
		}
		if (/^t$/i) {
			# parse table command
			&execute_command if $table_command;
			($table_command, $field_command, @table_params, @field_params, %rename_field) = ($_, '', (), (), ());
			while (defined $ARGV[0] and $ARGV[0] !~ /^-/) {
				push @table_params, shift;
			}
		} elsif (/^f$/i) {
			# parse field attribute
			fatal "you can only apply a -$_ modifier after a -t command" unless $table_command eq 't';
			fatal "you cannot apply a -$_ modifier to multiple tables" unless @table_params == 1;

			if ($field_command) {
				fatal <<End;
cannot apply two field commands to one table;
try one table command with multiple fields: -t fred -f foo bar
or two table commands: -t fred -f foo -t wilma -f bar
End
			}
			$field_command = $_;
			while (defined $ARGV[0] and $ARGV[0] !~ /^-/) {
				my $field = shift;
				push @field_params, $field;
				$field_params{$field} = 1;
			}
		} elsif (/^r$/) {
			# parse rename attribute
			if (%rename_field) {
				fatal <<End;
you cannot apply two separate rename commands to one table;
just do it in one command, e.g: -r foo,bar bar,foo
End
			}
			if ($table_command ne 't') {
				fatal <<End;
you can only use the rename commands with a single table;
e.g: -t fred -r foo,bar
End
			}
			while (defined $ARGV[0] and $ARGV[0] !~ /^-/) {
				my ($old, $new) = split /,/, shift;
				fatal "rename syntax: -r old1,new1 old2,new2 ... oldN,newN" if !defined $new;
				$rename_field{$old} = $new;
			}
		} elsif (/^w$/) {
			unless ($mode eq 'dump') {
				fatal "can only use --where in dump mode"; # TODO fix this!
			}
			# parse where expression
			$where_clause = '';
			while (defined $ARGV[0] and $ARGV[0] !~ /^-/) {
				$where_clause .= shift;
			}
			unless ($where_clause) {
				fatal "-w command without where expression";
			}
			$where_clause = "WHERE $where_clause";
		} else {
			fatal "unknown command -$_\n";
		}
	}

	# if we've been given a schema to help, look for renamed tables...
	
	&execute_command;
} else {
	# parse command options for diff

	while ($ARGV[0] =~ /^-/) {
		my $arg = shift;
		if ($arg eq "-S" || $arg eq "--mysql-spaces") {
			$ignore_trailing_spaces = 1
		} elsif ($arg eq "-Z" || $arg eq "--msql-zeros") {
			$ignore_trailing_zeros = 1
		} else {
			fatal "unknown option `$arg'";
		}
	}

	my ($old, $new);
	($old = shift) && ($new = shift) || fatal "the diff command takes two parameters";

	&execute_diff($old, $new);
}

$dbh->disconnect if defined $dbh;

if (@problem_tables) {
	print STDERR "insertion errors occurred while processing tables:\n(@problem_tables)\n" unless $quiet == 2;
}
if ($failed) {
	print STDERR "failed." unless $quiet == 2;
	exit 1;
}
if (@problem_tables) {
	exit 2;
}
exit 0;

sub execute_command {
	if ($mode eq 'dump') { &execute_dump }
	elsif ($mode eq 'restore') { &execute_restore }
	elsif ($mode eq 'convert') { &execute_convert }
}

#-----------------------------------------------------------------------
# execute dump of all tables
#-----------------------------------------------------------------------

sub execute_dump {
	my @tables = all_db_tables($dbh);
	
	# filter tables
	process_table_filter(\@tables); # modifies the list in place
	
	for my $table (@tables) {
		dump_table($table);
		($table_command, $field_command, @table_params, @field_params, %rename_field) = ($_, '', (), (), ());
	}
}

#-----------------------------------------------------------------------
# dump one table
#-----------------------------------------------------------------------

sub dump_table {
	my $table = shift;
	
	print STDERR "dumping $table " unless $quiet == 2;
	my ($reader, $fields) = sql_query($dbh, "SELECT * FROM $quote$table$quote $where_clause");
	
	# rename the table?
	$table = try_rename_table($table);
	
	# do we auto-rename fields?  which fields are numeric?
	check_schema_for_table($table, $fields);

	# prepare field filter - this alters the $fields array
	my @field_slice = process_field_slice($fields);
	
	# rename the fields - modifies in place
	rename_fields($fields);
	
	my $file = "$table.$format";
	
	if (not ($append or $wipe) and -e $file) {
		print STDERR <<End;
\ncannot overwrite existing file `$file'
use --wipe or --append
End
		$failed = 1;
		return;
	}

	my $writer = writer($format, $file, $fields);

	# the main loop to dump the table
	my $count = 0;
	my $row;
	do {
		$row = &$reader;
		# filter fields
		@$row = @$row[@field_slice] if $field_command and defined $row;
		&$writer($row);
		# print an 'alive' indicator (dot) every 100 rows, if wanted
		print STDERR '.' if ++$count % $dot_every == 0 and not $quiet;
	} while defined $row;
	
	print STDERR "\n" unless $quiet == 2;

	sort_dumpfile($file) if $sort;

	%rename_field = ();
}

#-----------------------------------------------------------------------
# execute restore of all tables
#-----------------------------------------------------------------------

sub execute_restore {
	my @tables = all_dumped_tables();
	
	# filter tables
	process_table_filter(\@tables); # modifies in place
	
	for my $table (@tables) {
		restore_table($table);
		($table_command, $field_command, @table_params, @field_params, %rename_field) = ($_, '', (), (), ());
	}
}

#-----------------------------------------------------------------------
# restore one table
#-----------------------------------------------------------------------

sub restore_table {
	my $table_with_suffix = shift; # this may have a .X or .C suffix on the end
	(my $table = $table_with_suffix) =~ s/\.[^\.]*$//; # get rid of any file suffix (i.e. table.X -> table)
	
	print STDERR "restoring $table_with_suffix " unless $quiet == 2;

	my ($reader, $fields) = read_dump_file("$table_with_suffix.dump");

	# rename the table?
	$table = try_rename_table($table);
	
	# do we auto-rename fields?  which fields are numeric?
	check_schema_for_table($table, $fields);
	
	# prepare field filter - this alters the $fields array
	my @field_slice = process_field_slice($fields);
	
	# rename the fields - modifies in place
	rename_fields($fields);
	
	# wipe the table if necessary
	if (not ($append or $wipe)) {
		# check that the table is empty
		if (@{$dbh->selectall_arrayref("SELECT * FROM $quote$table$quote LIMIT 1") || do { print STDERR "\ncannot access table `$table'\n"; return; } }) {
			# I hope the DBMSs all support LIMIT, I was using COUNT(*), my mSQL can't!
			print STDERR <<End;
\ncannot restore to non-empty table $table
use --wipe or --append
End
			$failed = 1;
			return;
		}
	}
	
	if ($wipe and not defined $dbh->do("DELETE FROM $quote$table$quote")) {
		print STDERR "cannot wipe table $table\n";
		return;
	}
	
	# the sql writer
	my $writer = write_sql($dbh, $table, $fields, \@numeric, \@coerce_nulls, \@fix_dates, $commit_every);
	
	# the exceptions writer
	# - this is delayed ('lazy'), so it only creates a file if necessary
	my ($except_comments, $except_rows) = write_dump_exceptions_file($table, $fields);
	
	# the main loop to restore the table
	my $count = 0;
	my $row;
	do {
		$row = &$reader;
		# filter fields
		@$row = @$row[@field_slice] if $field_command and defined $row;	
		# print an 'alive' indicator (dot) every 100 rows, if wanted
		print STDERR '.' if ++$count % $dot_every == 0 and not $quiet;
		# try to insert the row - any problems, we report them to the exceptions log
		unless (&$writer($row)) {
			my $errstr = $dbh->errstr || '';
			$errstr .= "\n" unless $errstr =~ /\n$/;
			&$except_comments("cannot insert row $count: $errstr");
			&$except_rows($row);
		}
	} while defined $row;
	
	print STDERR "\n" unless $quiet == 2;

	%rename_field = ();
}

#-----------------------------------------------------------------------
# execute convert of all tables
#-----------------------------------------------------------------------

sub execute_convert {
	my @tables = all_dumped_tables();
	
	# filter tables
	process_table_filter(\@tables); # modifies in place
	
	for my $table (@tables) {
		convert_table($table);
		($table_command, $field_command, @table_params, @field_params, %rename_field) = ($_, '', (), (), ());
	}
}

#-----------------------------------------------------------------------
# convert one table
#-----------------------------------------------------------------------

sub convert_table {
	my $table_with_suffix = shift; # this may have a .X or .C suffix on the end
	(my $table = $table_with_suffix) =~ s/\.[^\.]*$//; # get rid of any file suffix (i.e. table.X -> table)
	
	print STDERR "converting $table_with_suffix " unless $quiet == 2;

	my ($reader, $fields) = read_dump_file("$table_with_suffix.dump");

	# rename the table?
	$table = try_rename_table($table);
	
	# do we auto-rename fields?  which fields are numeric?
	check_schema_for_table($table, $fields);

	# prepare field filter - this alters the $fields array
	my @field_slice = process_field_slice($fields);
	
	# rename the fields - modifies in place
	rename_fields($fields);
	
	my $file = $format eq 'dump' ? "$table_with_suffix.C.dump" : "$table_with_suffix.$format";

	# wipe the destination file if necessary
	if (not ($append or $wipe) and -e $file) {
		print STDERR <<End;
\ncannot overwrite existing file `$file'
use --wipe or --append
End
		$failed = 1;
		return;
	}
	
	my $writer = writer($format, $file, $fields);

	# the main loop to convert the table
	my $count = 0;
	my $row;
	do {
		$row = &$reader;
		# filter fields
		@$row = @$row[@field_slice] if $field_command and defined $row;	
		# print an 'alive' indicator (dot) every 100 rows, if wanted
		print STDERR '.' if ++$count % $dot_every == 0 and not $quiet;
		# try to insert the row - any problems, we report them to the exceptions log
		&$writer($row);
	} while defined $row;
	
	print STDERR "\n" unless $quiet == 2;

	sort_dumpfile($file) if $sort;

	%rename_field = ();
}

# try to rename a table

sub try_rename_table {
	my ($table) = @_;
	# is this table being renamed?
	if (exists $rename_table{$table}) {
		print STDERR "renaming table $table -> $rename_table{$table}" unless $quiet == 2;
		$table = $rename_table{$table};
	}
	return $table;
}

#-----------------------------------------------------------------------
# if we have been given a schema to help, work out which fields are numeric,
# which are dates, and look for fields that have been renamed since the dump
#-----------------------------------------------------------------------

sub check_schema_for_table {
	my ($table, $fields) = @_;
	@numeric = ();
	@coerce_nulls = ();
	@fix_dates = ();
		
	if ($schema_database) {
		my $schema_table = $schema_database->table($table);

		if (!$schema_table) {
			print STDERR "\ntable `$table' is not in the schema\n";
			return;
		}

		# look for old field names, for auto-rename function
		for my $field ($schema_table->fields) {
			my $name = $field->name;
			if (my $olds = $field->old) {
				for my $old (split /,\s*/, $olds) {
					$rename_field{$old} = $name
						unless $schema_table->field($old);
				}
			}
		}

		# look for numeric fields in schema - but we go by the order in
		# the dump file

		# we also check which fields are marked NOT NULL, so we can
		# coerce the values to '' or 0 if --coerce-nulls was specified
		
		# we also check whether the field actually exists in the
		# schema, if it doesn't, then we put in in the @field_params
		# and set field command to -F if no field command was specified
		# already given

		$field_command = '!' if ! $field_command;
		
		for my $field_name (@$fields) {
			my $field = $schema_table->field($field_name);
			if ($field_command eq "f" && !$field_params{$field_name}
			    || $field_command eq "F" && $field_params{$field_name}) {
				next;
			}
			if (!defined $field) {
				if (my $new = $rename_field{$field_name}) {
					$field = $schema_table->field($new) if $new;
				} elsif ($field_command eq '!') {
					push @field_params, $field_name;
					print STDERR "\ndropping field `$field_name'\n";
					next;
				} else {
					print STDERR "\nfield `$field_name' is not in the schema\n";
					exit 1;
					return;
				}
			}
			push @numeric, $field->numeric;
			push @coerce_nulls, $coerce_nulls ? !$field->null : 0;
			push @fix_dates, $fix_dates ? $field->date_or_time : 0;
		}

		$field_command = "F" if $field_command eq "!";
	} else {
		# check for alternate method of specifying numeric fields -
		# a `+' before the field name
		for (@$fields) {
			my $numeric = scalar(s/^\+//);
			if ($field_command eq "f" && !$field_params{$_}
			    || $field_command eq "F" && $field_params{$_}) {
				next;
			}
			push @numeric, $numeric;
			push @coerce_nulls, 0;
			push @fix_dates, 0;
		}
	}
}

# writer: returns a function that writes a row to the output file

sub writer {
	my ($format, $file, $fields) = @_;
	my $writer;
	if ($format eq 'dump') {
		# the dump file writer
		$writer = ($append and -e $file) ?
			append_dump_file($file, $fields) :
				write_dump_file($file, $fields);
	} elsif ($format eq 'html') {
		require HTML::Entities;
		import HTML::Entities;
		$writer = ($append and -e $file) ?
			append_html_file($file, $fields) :
				write_html_file($file, $fields);
		
	} elsif ($format eq 'txt') {
		$writer = ($append and -e $file) ?
			append_file_neatly($file, $fields) :
				write_file_neatly($file, $fields);
	} elsif ($format eq 'tsv') {
		$writer = ($append and -e $file) ?
			append_tsv_file($file, $fields) :
				write_tsv_file($file, $fields);
	}
	return $writer;
}

# process_table_filter: modifies the list of tables in place, according
# to the table command and the table parameters

sub process_table_filter {
	my $tables = shift; # modifes in place
	
	if ($table_command eq 't') { # INCLUDE these tables
		@$tables = @table_params;
	} elsif ($table_command eq 'T') { # EXCLUDE these tables
		my %table_params = map {$_, 1} @table_params;
		@$tables = grep {not $table_params{$_}} @$tables;
	} # can also be '' for all tables
}

# process_field_filter: modifies the list of fields in place, according
# to the field command and the field parameters
sub process_field_slice {
	my $fields = shift;
	return 0..$#$fields unless $field_command;
	
	my @field_slice = ($field_command eq 'f') ?
		slice_include($fields, [@field_params]) :
		slice_exclude($fields, [@field_params]);
	
	@$fields = @$fields[@field_slice];
	
	return @field_slice;
}

# rename fields according to the schema
sub rename_fields {
	my $fields = shift;
	for my $field (@$fields) {
		$field = $rename_field{$field}
			if exists $rename_field{$field};
	}
}

# a slice that selects some fields from the whole set
sub slice_include {
	my ($fields, $inc) = @_;
	my %field_i;
	@field_i{@$fields} = 0..$#$fields;
	defined $field_i{$_} || fatal "\nunknown field `$_'" for @$inc;
	my @slice = map {$field_i{$_}} @$inc;
	return @slice;
}

# a slice that excludes some fields from the whole set
sub slice_exclude {
	my ($fields, $exc) = @_;
	my %field_e = map {$_, 1} @$exc;
	defined $field_e{$_} || fatal "\nunknown field `$_'" for @$exc;
	my @slice = grep {not $field_e{$fields->[$_]}} 0..$#$fields;
	return @slice;
}

# append to a DUMP file

sub append_dump_file {
	my ($table, $fields) = @_;
	# verify that the fields provided match those at the head of this file
	my ($dummy, $file_fields) = read_dump_file($table, $fields);
	unless (format_row_dump($file_fields) eq format_row_dump($fields)) {
		fatal "\ncannot --append to $table - fields do not match";
	}
	my $dump_writer = write_dump(write_file(">>$table"));
	return $dump_writer;
}

# this returns a 'lazy' writer for commented 'insert exceptions' files
# it is lazy in that no file is created unless the writer is used
# two functions are returned: the first for writing comments, the second for rows
sub write_dump_exceptions_file {
	my ($table, $fields) = @_;
	my $log_fh = $log ? ">$table.X.dump" : \*STDOUT;
	my $lazy_text_writer = lazy(
		sub {
		        my $text_writer = write_file($log_fh);
		        &$text_writer("\n** $table exceptions:\n") unless $log;
		        return $text_writer;
		}
	);
	my $lazy_dump_writer = lazy(
        	sub {
	    		my $write_dump = write_dump($lazy_text_writer);
	    		&$write_dump($fields);
	    		push @problem_tables, $table; # note the problem
	    		return $write_dump;
		}
        );

	return ($lazy_text_writer, $lazy_dump_writer);
}

# lazy: returns a function that builds a function the first time it is called
sub lazy {
	my $builder = shift;
	my @params = @_;
	my $func;
	return sub {
		$func = &$builder(@params) unless $func;
		&$func(@_);
	}
}

# all_db_tables: returns a list of all tables in the database
sub all_db_tables {
	my $dbh = shift;
	my @tables =  $dbh->tables;
	for (@tables) { s/`//g; } # kill bogus mysql backticks!!
	# kill bogus PostgreSQL system tables:
	@tables = grep { !/\./ || s/^public\.// } @tables;
	return @tables;
}

# all_dumped_tables: returns a list of all tables in the current directory
sub all_dumped_tables {
	my @tables = <*.dump>;
	for (@tables) { s/\.dump$// }
	# TODO - should this ignore .C.dump and .X.dump files?
	return @tables;
}

# write_html: returns a function that writes an HTML table
sub write_html {
	my $text_writer = shift;
	
	&$text_writer("<html><body>\n<table>\n");
	
	return sub {
		my $row = shift;
		if (defined $row) {
			&$text_writer("<tr>".(join '', map {"<td>".(defined $_ ? encode_entities($_) : "<i>NULL</i>")."</td>"} @$row)."</tr>\n");
		} else {
			&$text_writer("</table>\n</body></html>\n");
			&$text_writer(undef);
		}
	}
}

# write_html_file: returns a function that writes an HTML table to a file
sub write_html_file {
	my ($table, $fields) = @_;
	my $html_writer = write_html(write_file(">$table"));
	&$html_writer($fields);
	return $html_writer;
}

# append_html_file: returns a function that appends an HTML table to a file
sub append_html_file {
	my ($table, $fields) = @_;
	my $html_writer = write_html(write_file(">>$table"));
	&$html_writer($fields);
	return $html_writer;
}

# write_neatly: returns a function that writes a neatly formatted table
sub write_neatly {
	my ($text_writer) = @_;
	my @rows = ();
	
	my @maxlen = ();
	
	return sub {
		my $row = shift;
		
		if (defined $row) {
			push @rows, $row;
			for my $i (0..$#$row) {
				my $l = defined $row->[$i] ? length($row->[$i]) : 4;
				$maxlen[$i] = $l if $l > ($maxlen[$i] || 0);
			}
		} else {
			for my $row (@rows) {
				my @line = ();
				for (0..$#$row) {
					my $t = $row->[$_]; $t = 'NULL' unless defined $t;
					push @line, $t . ' ' x ($maxlen[$_] - length($t));
				}
				&$text_writer((join ' ', @line) . "\n");
			}
			&$text_writer(undef);
		}
	}
		
}

# write_file_neatly: returns a function that writes a neatly formatted table to a file
sub write_file_neatly {
	my ($table, $fields) = @_;
	my $neat_writer = write_neatly(write_file(">$table"));
	&$neat_writer($fields);
	return $neat_writer;
}

# append_file_neatly: returns a function that appends a neatly formatted table to a file
sub append_file_neatly {
	my ($table, $fields) = @_;
	my $neat_writer = write_neatly(write_file(">>$table"));
	&$neat_writer($fields);
	return $neat_writer;
}

# write_tsv: returns a function that writes a tab-separated table
sub write_tsv {
	my $text_writer = shift;
	
	return sub {
		my $row = shift;
		local $_ = format_row_dump($row);
		if (defined $_) {
			s/\r/\\r/;
			tr/\x01-\x08\x0a\x0b-\x1f\x7f//d;
			s/^\t//;
			chomp;
			$_ = "$_\r\n";
		}
		&$text_writer($_);
	}
}

# write_tsv_file: returns a function that writes a tab-separated table to a file
sub write_tsv_file {
	my ($table, $fields) = @_;
	my $tsv_writer = write_tsv(write_file(">$table"));
	&$tsv_writer($fields);
	return $tsv_writer;
}

# append_tsv_file: returns a function that appends a tab-separated table to a file
sub append_tsv_file {
	my ($table, $fields) = @_;
	my $tsv_writer = write_tsv(write_file(">>$table"));
	&$tsv_writer($fields);
	return $tsv_writer;
}

# sort_dumpfile: sorts a dumpfile numerically
sub sort_dumpfile {
	my ($file_in, $file_out) = @_;
	$file_out = $file_in unless defined $file_out;
	
	my $in = IO::File->new($file_in);
	
	unlink $file_out; # so can write to same filename if necessary
	
	my $out = IO::File->new(">$file_out");
	print $out scalar(<$in>);
	close $out;

	open $out, "| sort -n >> $file_out";
	while (<$in>) { print $out $_ }
	close $out;
	close $in;
}

# execute_diff: executes a diff on two dumpfiles
sub execute_diff {
	my ($old, $new) = @_;
	if (-d $old && -d $new) {
		my @old_files = grep { !/\.X\./ } map { substr $_, 1+length $old } <$old/*.dump>;
		my @new_files = grep { !/\.X\./ } map { substr $_, 1+length $new } <$new/*.dump>;

		my $last = '';
		for (sort @old_files, @new_files) {
			next if $_ eq $last; $last = $_;
			diff_dumpfiles("$old/$_", "$new/$_");
		}
	} elsif (-f $old && -f $new) {
		diff_dumpfiles($old, $new);
	} else {
		$old .= ".dump";
		$new .= ".dump";
		if (-f $old && -f $new) {
			diff_dumpfiles($old, $new);
		} else {
			fatal "cannot make any sense out of params: `$old' `$new'";
		}
	}
}

#TODO - make this faster by comparing text of a row first, then splitting up
#only if different

# diff_dumpfiles: compares two dumpfiles
sub diff_dumpfiles {
        my ($old_file, $new_file) = @_;

	unless (-f $old_file) { print "old file `$old_file' does not exist\n\n"; return }
	unless (-f $new_file) { print "new file `$new_file' does not exist\n\n"; return }

	print "comparing: `$old_file' and `$new_file'\n" unless $quiet == 2;

	# sort the files into temp files
	my $old_sorted = POSIX::tmpnam;
	my $new_sorted = POSIX::tmpnam;

	if ($ignore_trailing_spaces || $coerce_nulls) {
		strip_trailing_spaces_and_or_coerce_nulls($old_file, $old_sorted);
		strip_trailing_spaces_and_or_coerce_nulls($new_file, $new_sorted);
	} else {
		link $old_file, $old_sorted;
		link $new_file, $new_sorted;
	}
	
	if ($sort) {
		sort_dumpfile($old_sorted);
		sort_dumpfile($new_sorted);
	}

	my ($lc_old, $lc_new) = map {(split ' ', (`wc -l $_`))[0] - 1} ($old_file, $new_file);
	if ($lc_old ne $lc_new) {
		print "different number of rows ($lc_old : $lc_new)\n\n";
	}

    	my ($old_reader, $old_fields) = read_dump_file($old_sorted);
    	my ($new_reader, $new_fields) = read_dump_file($new_sorted);

    	if (@$old_fields != @$new_fields) {
		print "different number of fields (@$old_fields : @$new_fields\n\n";
		return;
	}

	return if $lc_old ne $lc_new;

    	# go through 1 at a time, compare each field of each record

    	for (my $i=0; ; ++$i) {
	        my $old_record = &$old_reader();
	        my $new_record = &$new_reader();

	        last if ! defined $old_record && ! defined $new_record;

	        my $old_line = format_row_dump($old_record);
	        my $new_line = format_row_dump($new_record);

	        my $diffs = 0;
	        for my $j (0..$#$old_fields) {
		        my $oldf = $old_record->[$j];
		        my $newf = $new_record->[$j];
		        
# convert_field: converts a field to a string
sub convert_field {
        if (defined $_[0]) {
		$_[0] = "`$_[0]'";
        } else {
	        $_[0] = "NULL";
        }
}

		        convert_field($oldf);
		        convert_field($newf);
    
		        if ($oldf ne $newf) {
			        next if $oldf eq "`0'" && $newf =~ /^`0.0+'$/;
			        next if $newf eq "`0'" && $oldf =~ /^`0.0+'$/;
			        next if $oldf eq "NULL" && ($newf eq "`'" || $newf eq "`0'" || $newf =~ /^`0.0+'$/) && $coerce_nulls;
		        
			        print "row #$i:\n" if ! $diffs++;
			        my $f = $old_fields->[$j] . "(" . $j . ")";
			        print "    $f: " . (" " x (20 - length($f))) . $oldf . " -> " . $newf . "\n";
		        }
	        }
        }
	print "\n";

	unlink $old_sorted, $new_sorted;
}

# strip_trailing_spaces_and_or_coerce_nulls: strips trailing spaces and/or
# coerces nulls (represented by \0) to the empty string
sub strip_trailing_spaces_and_or_coerce_nulls {
	my ($file_in, $file_out) = @_;
	$file_out = $file_in unless defined $file_out;
	
	my $in = IO::File->new($file_in);
	
	unlink $file_out; # so can write to same filename if necessary
	
	my $out = IO::File->new(">$file_out");
	
	while (<$in>) {
		s/ +(\t|$)/$1/g if $ignore_trailing_spaces;
		s/(?:\\0)+(\t|$)/$1/g if $ignore_trailing_zeros;
		s/\0//g if $coerce_nulls;
		print $out $_;
	}

	close $out;
	close $in;
}
