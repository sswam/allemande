#!/bin/bash -eu
export field=$1
export value=$2
ted 'my $field = $ENV{field}; my $value = $ENV{value}; chomp $field; s/^(\Q$field\E:.*?)(?=^[a-z])/$value\n/sm;'
