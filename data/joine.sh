#!/bin/bash -e

# Function to display help message
show_help() {
    cat << EOF
joine: Joins two files based on specified columns using the 'join' command.

Usage: $0 [OPTION] FILE1 FILE2 [COLUMN1] [COLUMN2]

Options:
  -h, --help    Display this help message and exit

Arguments:
  FILE1         First input file
  FILE2         Second input file
  COLUMN1       Join column for first file (default: 1)
  COLUMN2       Join column for second file (default: same as COLUMN1)

The script uses tab as a field separator and sets LC_ALL=C for consistent sorting behavior.

Examples:

1. Join two files based on the first column (default):

  $0 names.txt ages.txt

2. Join two files using the second column of the first file and the first column of the second file:

  $0 employees.txt departments.txt 2 1
EOF
    exit 0
}

# Check for help option
if [[ "$1" == "-h" || "$1" == "--help" ]]; then
    show_help
fi

# Check if at least two arguments are provided
if [ $# -lt 2 ]; then
    echo "Error: Two input files are required." >&2
    echo "Use '$0 --help' for more information." >&2
    exit 1
fi

F1=$1
F2=$2

shift 2

A=1
[ -n "${1:-}" ] && A=$1

B=$A
[ -n "${2:-}" ] && B=$2

LC_ALL=C join -t $'\t' -j1 $A -j2 $B "$F1" "$F2"
