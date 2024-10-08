#!/bin/bash -eu
# file command [args ...]
# Process an input file in paginated chunks with optional overlap.
#
# This script processes an input file in chunks, applying a specified command
# to each chunk. It allows for overlap between chunks to ensure continuity in
# processing.
#
# Example:
#
#     chunkpro shakespeare.txt summary | program-to-magically-fix-the-duplicate-summary-bits

n=200   # number of lines per page
o=20    # overlap

. opts

input="$1"
shift

cmd=("$@")

# Count total lines in the input file
lines=`wc -l < "$input"`

i=1

while true; do
    # Extract a chunk of 'n' lines starting from line 'i'
    # and pass it to the specified command
    < "$input" tail -n +$i | head -n $n | "${cmd[@]}"

    # Check if we've processed all lines
    if [ $(($i+$n - 1)) -ge $lines ]; then
        break
    fi

    # Move to next chunk, accounting for overlap
    i=$((i+n-o))
done

# Usage: ./script.sh input_file command [args...]
# Example: ./script.sh large_file.txt grep "pattern"

# Here's the script with added comments describing how it works:

# This script processes a large input file in chunks, applying a specified command to each chunk. It allows for overlap between chunks to ensure continuity in processing. The script can be customized by modifying the `n` (chunk size) and `o` (overlap) variables or by sourcing additional options from an `opts` file.

