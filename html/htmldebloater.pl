#!/usr/bin/perl
# htmldebloater -- debloat HTML so it can be comfortably read
#                  even on a turn of the centry black and white PDA
# License         : http://www.fsf.org/licensing/licenses/gpl.txt
# Created         : December 2004
# Last Modified On: Fri, 20 Sep 2024 00:17:25 +1000
# Update Count    : 26
# Inspiration     : Dan Jacobson -- http://jidanni.org/comp
# Dodgy Perl Code : Sam Watkins <sam@ucm.dev>

our $VERSION = 26;

use strict;
use warnings;

use HTML::Parser;
use HTML::Entities;
use Getopt::Std;

our %opts;

# configuration...

# Only tags in this list will get through.
my $ok_tags = set(
    qw(
      html head body
      title base meta
      p br hr
      a img
      table th tr td
      b i u em strong
      blockquote
      center
      ul ol li dl dt dd
      h1 h2 h3 h4 h5 h6
      pre
      form input textarea
      )
);

my $block_tags_to_remove = set(
    qw(
      div
      )
);

# Attributes in this list will get through no matter what tag they are in.
# - I can't think of any yet.
my $ok_attr = set(
    qw(
      )
);

# a list of allowed attributes for each tag
my $ok_tag_attr = {
    td   => set(qw(colspan rowspan valign)),
    a    => set(qw(href name)),
    img  => set(qw(src width height alt)),
    base => set(qw(href)),
    meta => set(qw(http-equiv content)),
    form => set(qw(action)),
    input => set(qw(name type value size)),
    textarea => set(qw(name rows cols)),
};

# a list of tags where we want to strip the content between <foo> and </foo>
my $kill_containers = set(
    qw(
      script style
      select
      )
);

# a list of tags where we want to preserve the text content exactly
my $pre_containers = set(
    qw(
      pre textarea
      )
);

# Tags in this list will be filtered based on a predicate over their attributes.
# The "predicate" could also change the attribute names or values, delete attributes, etc.
my $tag_filter = {
    meta => sub { my $attr = $_[0]; $attr->{'http-equiv'} && $attr->{content} }
};

# optional stuff:

my $keep_unnecessary_whitespace = $opts{s};
my $keep_align = $opts{a};
my $keep_title = $opts{t};
my $keep_imgs = $opts{i};

if ($keep_align) {
	$ok_tag_attr->{td}{align} = 1;
	$ok_tag_attr->{td}{valign} = 1;
}

if ($keep_title) {
	$ok_tag_attr->{img}{alt} = 1;
	$ok_tag_attr->{img}{title} = 1;
}

# global state...

my $in_dead_container = 0;
my $in_pre_container = 0;
my $last_out = "";

# main code starts here...

sub main {
    $Getopt::Std::STANDARD_HELP_VERSION = 1;
    getopts('hvsati', \%opts);
    if ($opts{h}) { HELP_MESSAGE(); }
    if ($opts{v}) { VERSION_MESSAGE(); }

    my $parser = HTML::Parser->new(
        text_h => [ \&pass_through, "text" ],
        declaration_h => [ \&pass_through, "text" ],
        start_h => [ \&start_tag, "self, tagname, attrseq, attr" ],
        end_h   => [ \&end_tag,   "self, tagname, text" ]
        #	no comments will get through
        #	default_h => [ sub    { print shift },        'text' ],
    );
    $parser->parse_file(*STDIN);

    if ($last_out !~ /\n$/) {
        out("\n");
    }
}

sub pass_through {
    my ($text) = @_;
    if (!$keep_unnecessary_whitespace && !$in_pre_container) {
        $text =~ s/(\s)\s+/$1/gs;
        if ($last_out =~ /\s+$/) {
            $text =~ s/^\s+//;
        }
    }
    unless ($in_dead_container) {
        out($text);
    }
}

sub add_spacing_for_removed_tag {
    my ($tag) = @_;
    if ($block_tags_to_remove->{$tag} && $last_out !~ /\n$/) {
        # Add a newline for removed block tags
        out("\n");
    } elsif (!$block_tags_to_remove->{$tag} && $last_out !~ /\s$/) {
        # Add a space for removed inline tags
        out(" ");
    }
}

sub start_tag {
    my ( $self, $tag, $attrseq, $attr ) = @_;
    if ( $ok_tags->{$tag} && !$in_dead_container ) {
        $attrseq =
          [ grep { $ok_attr->{$_} || $ok_tag_attr->{$tag}{$_} } @$attrseq ];
        my $keep_tag = 1;
        if (my $pred = $tag_filter->{$tag}) {
            $keep_tag = $pred->($attr);
        }
        if ($tag eq "img" and !$keep_imgs) {
            my $alt = $attr->{alt} || "";
            out(" [$alt] ");
        } elsif ($keep_tag) {
            out(format_start_tag( $tag, $attrseq, $attr ));
        }
    } elsif (!$in_dead_container) {
        add_spacing_for_removed_tag($tag);
    }
    if ( $kill_containers->{$tag} ) {
        ++$in_dead_container;
    }
    if ( $pre_containers->{$tag} ) {
        ++$in_pre_container;
    }
}

sub end_tag {
    my ( $self, $tag, $text ) = @_;
    if ($ok_tags->{$tag} && !$in_dead_container) {
        out($text);
    } elsif (!$in_dead_container) {
        add_spacing_for_removed_tag($tag);
    }
    if ( $kill_containers->{$tag} ) {
        --$in_dead_container;
    }
    if ( $pre_containers->{$tag} ) {
        --$in_pre_container;
    }
}

sub set {
    return { map { $_, 1 } @_ };
}

sub format_start_tag {
    my ( $tag, $attrseq, $attr ) = @_;
    my $out = "<$tag";
    for (@$attrseq) {
        $out .= " $_";
	if ( defined($attr->{$_}) ) {
	    $out .= '="' . encode_entities( $attr->{$_}, '<>&"' ) . '"';
	}
    }
    $out .= '>';
    return $out;
}

sub HELP_MESSAGE {
	print <<End;

htmldebloater [options] < from.html > to.html

-v	display version
-h	display help
-s	keep unnecessary whitespace
-a	keep valign and align attributes
-t	keep alt and title attributes
-i	keep img tags

End
	exit;
}

sub VERSION_MESSAGE {
	open SCRIPT, $0;
	my $hash_bang = <SCRIPT>;
	print "\n";
	while (1) {
		my $line = <SCRIPT>;
		last unless $line =~ s/^# //;
		print $line;
	}
    HELP_MESSAGE();
	exit;
}

sub out {
    my ($text) = @_;
    $last_out = $text if $text ne "";
    print $text;
}

main();
