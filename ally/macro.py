import re


def process_macros(text: str, env: dict) -> str:
    """Process conditional <if varname> ... </if> blocks in text.

    Blocks are included only if env.get(varname) is truthy. Supports nesting.
    """
    lines = text.split('\n')
    output = []
    stack = []  # stack of condition booleans for nested <if> blocks

    for line in lines:
        stripped = line.strip()
        if m := re.fullmatch(r'<if (\w+)>', stripped):
            stack.append(bool(env.get(m.group(1))))
        elif stripped == '</if>':
            if stack:
                stack.pop()
        elif all(stack):
            output.append(line)

    return '\n'.join(output)
