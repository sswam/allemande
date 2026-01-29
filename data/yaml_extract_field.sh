#!/bin/bash -eu
export field=$1
ted 'my $field = $ENV{field}; /^(\Q$field\E:.*?)(?=^[a-z])/sm; print $1; $_=""'
