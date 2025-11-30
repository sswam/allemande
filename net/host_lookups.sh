#!/bin/bash -eu
each host : "$@" |
sed -n 's/.* has address //p'
