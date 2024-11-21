#!/bin/bash

# Function to display help message
show_help() {
    cat << EOF
Usage: order [OPTIONS] [FIELD_NUMBERS]

Sort lines of text from standard input using specified field numbers.

Options:
  -h, --help    Display this help message and exit

Arguments:
  FIELD_NUMBERS  One or more field numbers to sort by, separated by spaces.
                 Fields are assumed to be tab-separated.

Description:
  This script sorts input lines based on specified field numbers. It uses
  the Unix 'sort' command with tab as the field separator. The sorting is
  stable (-s) and uses the C locale (LC_ALL=C) for consistent sorting.

Examples:
  ./script.sh 2       Sort based on the second field
  ./script.sh 3 1     Sort first by the third field, then by the first field

Note:
  - Fields are numbered starting from 1
  - Input is expected to be tab-separated
  - Output preserves the original order of lines with equal sort keys
EOF
    exit 0
}

# Check for help option
if [[ "$1" == "-h" || "$1" == "--help" ]]; then
    show_help
fi

# Main sorting logic
LC_ALL=C sort -s -t$'\t' `echo $@ | sed 's/\([0-9.][0-9.]*\)/-k\1,\1/g'`
