"""Apply multiple regex mappings to a string in a single pass."""

import re

__VERSION__ = "0.1.2"


def apply_mappings(text: str, mapping: dict[str, str], mapping_first: dict[str, str]) -> str:
    """Apply multiple regex mappings to a string in a single pass."""
    if not text or (not mapping and not mapping_first):
        return text

    result = []
    remaining = text
    used_first_patterns = set()

    def try_match_pattern(pattern: str, repl: str, match_obj) -> str | None:
        """Try to apply a single pattern and return the replacement if successful."""
        if not match_obj:
            return None
        return re.sub(r"\\(.)", lambda m: match_obj.group(int(m.group(1))) if m.group(1)[0].isdigit() else m.group(1), repl)

    while remaining:
        match_found = False

        # Try mapping_first patterns first
        for pattern, repl in mapping_first.items():
            if pattern in used_first_patterns:
                continue
            match = re.match(pattern, remaining)
            if match:
                replacement = try_match_pattern(pattern, repl, match)
                if replacement is not None:
                    result.append(replacement)
                    remaining = remaining[match.end():]
                    match_found = True
                    used_first_patterns.add(pattern)
                    break

        if match_found:
            continue

        # Try regular mapping patterns
        for pattern, repl in mapping.items():
            match = re.match(pattern, remaining)
            if match:
                replacement = try_match_pattern(pattern, repl, match)
                if replacement is not None:
                    result.append(replacement)
                    remaining = remaining[match.end():]
                    match_found = True
                    break

        if not match_found:
            # No match found, move forward one character
            result.append(remaining[0])
            remaining = remaining[1:]

    return "".join(result)
