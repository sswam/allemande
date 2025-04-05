def preprocess_normal_line(line: str) -> tuple[str, bool]:
    """Find and fix inline math in a line, also preprocess links."""
    # run the regexpes repeatedly to work through the string

    start = 0
    has_math = False
    while True:
        logger.debug("preprocess line part from: %r %r", start, line[start:])
        # 1. find quoted code, and skip those bits
        match = re.match(
            r"""
            ^
            (
                [^`]+       # Any characters except `
                |`.*?`       # OR `...`
                |```.*?```   # OR ```...```
                |.+          # OR Any characters, if syntax is broken
            )
            """,
            line[start:],
            re.VERBOSE,
        )
        if not match:
            break
        found = match.group(1)
        if found.startswith("`"):
            start += len(found)
            continue

        # 2. Fix links
        # TODO

        # 3. find inline math, and replace with $`...`$
        fixed, has_math1 = find_and_fix_inline_math_part(found)
        has_math = has_math or has_math1

        # 4. replace the fixed part in the line
        line = line[:start] + fixed + line[start + len(found) :]
        start += len(fixed)

    return line, has_math
