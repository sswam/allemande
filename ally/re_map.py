"""Apply multiple regex mappings to a string in a single pass."""

import re


def apply_mappings(text: str, mapping: dict[str, str], mapping_first: dict[str, str]) -> str:
    """Apply multiple regex mappings to a string in a single pass."""
    if not text or (not mapping and not mapping_first):
        return text

    # Remove duplicates by prioritizing mapping_first patterns
    unique_patterns: list[str] = []
    pattern_to_index: dict[str, int] = {}

    # Add mapping_first patterns first (higher priority)
    for pattern in mapping_first:
        if pattern not in pattern_to_index:
            pattern_to_index[pattern] = len(unique_patterns)
            unique_patterns.append(pattern)

    # Add mapping patterns if not already present
    for pattern in mapping:
        if pattern not in pattern_to_index:
            pattern_to_index[pattern] = len(unique_patterns)
            unique_patterns.append(pattern)

    # Combine unique patterns into a single pattern
    combined_pattern = "|".join(f"({pattern})" for pattern in unique_patterns)

    # Track which patterns from mapping_first have been used
    first_match_used = {pattern: False for pattern in mapping_first}

    def replace_func(match):
        # Find which pattern matched
        for i, group in enumerate(match.groups(), 1):
            if group is not None:
                pattern = unique_patterns[i - 1]

                # Store all groups for potential references in replacement
                groups = match.groups()

                def repl(m, pattern_index=i, matched_groups=groups):
                    # if not a digit, return as-is
                    if not "0" <= m.group(1)[0] <= "9":
                        return m.group(0)
                    # Convert \1 style references to the actual captured group
                    group_num = int(m.group(1))
                    # Adjust group number based on which pattern matched
                    adjusted_num = group_num + (pattern_index - 1)
                    if 0 <= adjusted_num < len(matched_groups):
                        return matched_groups[adjusted_num] or ""
                    return m.group(0)

                # Handle mapping_first patterns
                if pattern in mapping_first:
                    result = re.sub(r"\\(\d+|.)", repl, mapping_first[pattern])
                    mapping_first.pop(pattern)  # Remove after first use
                    return result

                # Handle regular mapping patterns
                if pattern in mapping:
                    result = re.sub(r"\\(\d+|.)", repl, mapping[pattern])
                    return result

        return match.group(0)

    return re.sub(combined_pattern, replace_func, text)
