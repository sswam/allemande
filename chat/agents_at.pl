#!/usr/bin/perl -p
chomp;
s/^\.?\/?(.*)\.yml$/\@$1, / or $_ = ""
