#!/usr/bin/perl -p
$| = 1;

BEGIN { @rsf = reverse sort map {$_>0 ? $_-1 : $_} @ARGV; @ARGV = () }

chomp;
@F=split/\t/,$_,-1;
for (@rsf) { splice @F, $_, 1 };
$_=(join"\t",@F)."\n";
