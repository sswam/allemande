#!/usr/bin/perl -0p
s/\n//g;
s{/\*.*?\*/}{}g;
s/\s*{\s*/{ /g;
s/\s*}\s*/}\n/g;
s/;\s*/; /g;
