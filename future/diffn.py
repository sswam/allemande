"""
A multi-way diff tool that compares two or more text files.

Usage: python diffn.py file1 file2 [file3 ...]

This script performs a multi-way diff on the input files, highlighting
differences and commonalities between them.
"""

import sys
from typing import List, Tuple
from functools import lru_cache


def lcs(sequences: List[List[str]]) -> List[str]:
    """Compute the Longest Common Subsequence (LCS) of given sequences."""
    # sequences is a list of sequences (lists of items)

    @lru_cache(maxsize=None)
    def lcs_recursive(*positions):
        if any(pos < 0 for pos in positions):
            return []
        elif all(sequences[i][positions[i]] == sequences[0][positions[0]] for i in range(len(sequences))):
            prev_positions = tuple(pos - 1 for pos in positions)
            return lcs_recursive(*prev_positions) + [sequences[0][positions[0]]]
        else:
            options = []
            for i in range(len(sequences)):
                if positions[i] >= 0:
                    new_positions = list(positions)
                    new_positions[i] -= 1
                    options.append(lcs_recursive(*new_positions))
            if options:
                return max(options, key=len)
            else:
                return []

    positions = [len(seq) - 1 for seq in sequences]
    return lcs_recursive(*positions)


def multi_way_diff(*sequences: List[str]) -> List[Tuple[str, List[bool]]]:
    """Perform a multi-way diff on the given sequences."""
    # Find the common subsequence
    common = lcs(list(sequences))
    result = []
    indices = [0] * len(sequences)

    # Process each item in the common subsequence
    for item in common:
        chunk = []
        for i, seq in enumerate(sequences):
            # Add non-matching items to the chunk
            while indices[i] < len(seq) and seq[indices[i]] != item:
                line_present = [j == i for j in range(len(sequences))]
                chunk.append((seq[indices[i]], line_present))
                indices[i] += 1
            if indices[i] < len(seq):
                indices[i] += 1
        if chunk:
            result.extend(chunk)
        # Add the common item
        result.append((item, [True] * len(sequences)))

    # Add remaining items from each sequence
    for i, seq in enumerate(sequences):
        while indices[i] < len(seq):
            line_present = [j == i for j in range(len(sequences))]
            result.append((seq[indices[i]], line_present))
            indices[i] += 1

    return result


def multi_file_diff(*files):
    """Perform a multi-way diff on the contents of the given files."""
    # Read contents of all files
    file_contents = []
    for file in files:
        with open(file, "r") as f:
            file_contents.append([line.rstrip('\n') for line in f])

    # Perform the diff
    diffs = multi_way_diff(*file_contents)

    # Print the diff results
    for i, (line, present) in enumerate(diffs, start=1):
        if all(present):
            print(f"    {line}")
        else:
            for j, p in enumerate(present):
                if p:
                    print(f"{j + 1:3d} {line}")


if __name__ == "__main__":
    # Check for correct usage
    if len(sys.argv) < 3:
        print("Usage: python diffn.py file1 file2 [file3 ...]")
        sys.exit(1)

    # Perform multi-file diff on command-line arguments
    multi_file_diff(*sys.argv[1:])

# **Comments on other issues:**
#
# - The recursive computation of the LCS for multiple sequences can be inefficient for large files or a large number of files due to the exponential time complexity. This implementation is suitable for small files or a limited number of sequences.
# - For better performance on larger datasets, consider implementing an iterative dynamic programming approach or using specialized libraries that handle multi-sequence alignment more efficiently.

