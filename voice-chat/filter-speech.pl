#!/usr/bin/perl -p
use strict;
use warnings;
BEGIN { $| = 1; }
s/–/.../g;
s/\x{7e9}/'/g;
s/[^\0-~]//g;    # filter out emojis; but \x7e9 is closing single-quote / "smart" apostrophe
#s{\bThalia\b}{<phoneme ph="təˈliːə">Thalia</phoneme>}g;
s{\bThalia\b}{Thalia}g;
