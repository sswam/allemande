#!/usr/bin/perl -n
if (! $count{$_}++) {
    push @order, $_;
}
END {
    for (@order) {
        print $count{$_}, "\t", $_;
    }
}
