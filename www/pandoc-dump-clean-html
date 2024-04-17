#!/usr/bin/perl
# pandoc-dump-clean-html - clean up HTML to get main content only, e.g. Wikipedia, <main> and <article>

# TODO another approach might be to create a DOM map of sorts and let an AI guess where the main content would be

use strict;
use warnings;

undef $/;

$_ = <STDIN>;

if (/<meta name="generator" content="MediaWiki/) {
#	s{<li class="interlanguage-link.*?</li>}{}g;
#	s{<a class="vector-toc-link"[^>]*>\s*<div class="vector-toc-text">\s*(.*?)</div>\s*</a>}{$1}gs;
	s{\A.*?(<div id="bodyContent)}{$1}s;
	s{<h2><span class="mw-headline" id="See_also">.*}{}s;
	s{<h2><span class="mw-headline" id="References">.*}{}s;
} else {
	if (m{<main\b[^>]*>\s*(.*?)\s*</main>}si) {
		$_ = "$1\n";
	}
	if (m{<article\b[^>]*>\s*(.*?)\s*</article>}si) {
		$_ = "$1\n";
	}
}

print "$_";
