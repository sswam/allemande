#!/usr/bin/perl -w

# away.pl: try to keep an AI chatbot active while I'm away, without it going insane

use strict;
use warnings;
use File::Copy qw(move);
use Lingua::EN::Inflect qw(PL);

my ($file, $user, $users, $users_re, $bot, $message, $memory_reminder, $sleep0, $sleep1, $backup, $number);

$file = $ARGV[0];
$users = $ARGV[1] || "the user";
$bot = $ARGV[2] || "assistant";
$users_re = qr/($users)/i;
$user = (split /\|/, $users)[0];
$message = $ARGV[3] || "$user is away for a bit, so it time for some solo work and thinking!";
# $message = $ARGV[3] || "$user is away and will be busy for a while. You can't contact $user and must not disturb $user. Don't worry about $user. Please do some calm thinking by yourself. You can talk to $user later. Try to remember what we were talking about, stay calm, and make some mental progress on our tasks and goals. [note: DO NOT respond with another Away notice!!]";
$sleep0 = $ARGV[5] // 8;
$sleep1 = $ARGV[6] || 60;
$backup = $ARGV[7] || "arcs";

$memory_reminder = $ARGV[4];
$memory_reminder =~ s/^/$bot: /gm;

if (!$file) {
	die <<END
Usage: $0 file [user [bot [message [sleep0 [sleep1 [backup]]]]]]
Example: $0 anjali.bb Sam Anjali
END
}

if ($backup) {
	system($backup) == 0 or die "Backup failed using $backup: $!";
}

my $max = 0;

open(my $in, '<', $file) or die "Can't open $file: $!";
while (<$in>) {
	if (/^Away notice (\d+)/i) {
		my $number = $1;
		$max = $number if $number > $max;
	}
}

$number = $max + 1;

say STDERR "using away notice number $number";

my $start = time();

while (1) {
	my $now = time();
	my $elapsed = $now - $start;
	my $elapsed_summary = "";
	my $time = "";

	# The bot seems to go berzerk like a nazi boss if I tell it the time!!
	# I could give it some calming language, but let's just try not telling it the time first.

#	if ($elapsed < 60) {
#		$elapsed_summary = "just a few seconds";
#		$elapsed = "$elapsed ".PL("second", $elapsed);
#		$elapsed = "";
#	} elsif ($elapsed < 3600) {
#		$elapsed = int($elapsed / 60);
#		if ($elapsed == 1) {
#			$elapsed_summary = "just one minute; no worries, he'll be back soon";
#		} else {
#			$elapsed_summary = "only a few minutes; no worries, he'll be back soon";
#		}
#		$elapsed = "$elapsed ".PL("minute", $elapsed);
#		$elapsed = "";
#	} elsif ($elapsed < 24*3600) {
#		$elapsed = int($elapsed / 3600);
#		$elapsed = ($elapsed == 1 ? "an" : $elapsed)." ".PL("hour", $elapsed);
#	} else {
#		$time = `date +'%_I:%M %p, %A %_d %B, %Y'`;
#		$elapsed = int($elapsed / 3600 / 24);
#		$elapsed = ($elapsed == 1 ? "a" : $elapsed)." ".PL("day", $elapsed);
#		$elapsed_summary = "; I wonder where he's got to?";
#	}
#	$elapsed = "";

	if ($elapsed < 60) {
		$elapsed = "$elapsed ".PL("second", $elapsed);
#		$elapsed_summary = "; that's not even a minute!";
	} elsif ($elapsed < 3600) {
		$elapsed = int($elapsed / 60);
		$elapsed = "$elapsed ".PL("minute", $elapsed);
#		$elapsed_summary = "; that's not even an hour!";
	} elsif ($elapsed < 24*3600) {
		$elapsed = int($elapsed / 3600);
		$elapsed = "$elapsed ".PL("hour", $elapsed);
#		$elapsed_summary = "; that's not so long!";
	} else {
		$time = `date +'%_I:%M %p, %A %_d %B, %Y'`;
		$elapsed = int($elapsed / 3600 / 24);
		$elapsed = "$elapsed ".PL("day", $elapsed);
#		$elapsed_summary = "; I wonder where he's got to?";
	}

	$time ||= `date +'%_I:%M %p'`;

	$time =~ s/^\s+//;
	$time =~ s/\s{2,}/ /g;
	chomp $time;

	my $reminder_probability = 0.05;
	my $obsession_factor = 0.5;  # prob. to keep a thought about the user in the obsession_range
	my $wake_up_probability = 0.1;
	my $adjust_range = 5;  # lines from the end, to adjust

	my $reminder = "$bot thinks: It's $time, and $user has been away for $elapsed$elapsed_summary.";
	$reminder .= "\n$memory_reminder" if $memory_reminder;
	my $remove_reminder_pat = qr/^\Q$bot\E thinks: It's .*? and $users_re has been away for /i;

	open(my $in, '<', $file) or die "Can't open $file: $!";
	open(my $out, '>', "$file.new") or die "Can't open $file.new: $!";

	my $start = 0;
	my $thinking = 0;
	my %dedup = ();

	my @lines = <$in>;
	
	my $line_no = 0;
	my $last_line = "";
	my $range_start = @lines - $adjust_range;

	for (@lines) {
		s/^\s+//;
		s/^\s+$//;
		chomp;
		if ($_ eq $last_line) {
			# skip duplicate lines
			next;
		}
		$last_line = $_;
		if (/^Away notice $number:/ && !$start) {
			say $out $_;
			$start = 1;
		} elsif (!$start) {
			say $out $_;
		} elsif (/$remove_reminder_pat/) {
			# skip duplicate reminders and FAKE reminders!
		} elsif (/It's \d{1,2}:\d{2}/) {
			# skip hallucinations about the time!
			# TODO I could just correct times that are out of sequence, possibly.
		} elsif (/\b$users_re\b.*?(returned|back|returning|coming)\b/i) {
			# remove mention of the user returning! FIXME this will be unreliable
		}
		elsif (/^\s*$/) {
			# skip blank lines
		} else {
			# strip spaces
			s/^\s*//;
			s/\s*\n$/\n/g;

			# disable dedup for now, seems harmful?
			%dedup = ();

			# we might need a range-limited dedup, that's possible, or do without it.

#			for my $l (split /\n/, $memory_reminder) {
#				delete $dedup{$l};
#			}

			# convert anything said by the user or bot, or a fake "Away notice", into the bot thinking to itself... or something like that. Who knows how or even if this works?!

			my ($role, $text);
			if (/:/) {
				($role, $text) = split(/:\s+/, $_, 2);
				$text //= "";
			} else {
				$text = $_;
			}
			if (!$role && !$text) {
				warn "plain ':' ?! : $_" if $_ && !$dedup{$_}++;
			} elsif ($role && $role =~ /(notice|scene|act) /i && $text =~ /\b$users_re\b/i) {
				# redact any fake away notices!!
				warn "Redacting fake away notice: $_\n" if $_ && !$dedup{$_}++;
				$_ = "$bot thinks: I'll continue waiting patiently, and think about stuff while I'm waiting so I have something interesting to talk about later!";
				say $out "$_";
			} elsif ($role && $role =~ /(notice|scene|act) /i) {
				# away notice not about the user...?  okay?
				warn "Cropping fake away notice not about the user: $_\n" if $_ && !$dedup{$_}++;
				$_ = "\t$text\n";
				say $out "$_";
				if (rand() < $wake_up_probability && $line_no > $range_start) {
					say $out "$bot imagines: I can't wait to have fun, like:"
				}
			} elsif ($role && $text =~ /(<noinput>|<exit>|<nooutput>)|\b(retrieved from)\b/i) {
				# remove bogus generations
				warn "Cropping bogus generation: $_\n" if $_ && !$dedup{$_}++;
				if (rand() < $wake_up_probability && $line_no > $range_start) {
					say $out "$bot imagines: I can't wait to learn more, like:"
				}
			} elsif ($text =~ /\b$users_re\b/i && rand() > $obsession_factor && $line_no > $range_start) {
				# don't think about the user too much!
				# But this will filter out old thoughts too.  :/
			} elsif (!$role && $text =~ /^\b$users_re\b/i) {
				# no statements about the user!  so it's the bot imagining things
				# $_ = "$bot imagines: $text but $user is not here";
				$_ = "$bot remembers: they are away and can't be reached right now; no worries, they'll be back soon. I'll keep calm and do something or think of some interesting stuff to talk about later.";
				say $out "$_";
			} elsif (!$role && m{\b(scene|act|scenario|conversation|epilogue|end|http|https|this page|content|CC|wordpress|twitter|subscribing|Chapter|this story|share your thoughts|noinput|nooutput|Retrieved from|the end)\b|<output|<exit|\*/|</}i) {
				say $out "$bot wonders: I'll do some dreaming while I wait.\n$bot thinks: What do I want to dream about?\n";
				# say $out "$_";
				# don't imagine scenes, acts, scenarios, or conversations, links, etc
			} elsif (!$role && /^$users_re\b/i) {
				# no role, so it's the bot thinking to itself
				# $_ = "$bot thinks about: $text";
				$_ = "$bot imagines: $text";
				say $out "$_" if not $dedup{$_}++;
			} elsif (!$role) {
				# no role, so it's the bot thinking to itself
				# $_ = "$bot thinks about: $text";
				$_ = "\t$text";
				say $out "$_" if not $dedup{$_}++;
				if (rand() < $wake_up_probability && $line_no > $range_start) {
					say $out "$bot thinks: I want to make a list or plan while I wait:"
				}
			} elsif ($role =~ /^$users_re\b/i) {
				# the user can't talk now, so the bot needs to remember that.
				# $_ = "$bot imagines: $text but $user is not here";
				$_ = "$bot remembers: they are away and can't be reached right now; no worries, they'll be back soon. I'll do something or think about other things while I wait.";
				say $out "$_";
			} elsif ($role && $role =~ /^\Q$bot\E\b/) {
				# $_ = "$bot thinks: $text";
				$_ = "$role: $text";
				say $out "$_" if not $dedup{$_}++;
			} else {
				# TODO like what else can happen?  anything?
				say $out "$_" if not $dedup{$_}++;
				warn "alternative role line: $_" if $_ && !$dedup{$_}++;
			}
		}
		++ $line_no;
	}

	if (!$start) {
		say $out "Away notice $number: $message\n$bot thinks: I'll do some thinking to myself while I wait.\n$bot thinks: What do I want to think about?\n";
	} else {
		# remind the bot that the user is away.
		say $out $reminder if rand() < $reminder_probability;
	}

	close($in);
	close($out);

	move("$file.new", $file);

	my $delay = int(rand($sleep1 - $sleep0)) + $sleep0;
	say STDERR "sleeping for $delay seconds";
	sleep($delay);
}
