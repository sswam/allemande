#!/usr/bin/env python3-allemande

""" extract possible tools calls from message text, e.g. image gen propmts """

import re
import logging


logger = logging.getLogger(__name__)


def extract_tool_calls(content: str) -> list[str]:
    """
    extract possible tools calls from message text, e.g. image gen propmts
    """
    # logger.info("extract_tool_calls 1: %s", content)

    content = re.sub(r"(\A\w.*?:|^)\t", "", content, flags = re.MULTILINE)

    matches = re.findall(r"""
    ^`+\s*@\w.*?`+
    |
    ^\s*@\w.*?(?=\n\n|\Z|^\s*@\w)
    """, content, flags = re.VERBOSE | re.MULTILINE | re.DOTALL)

    matches = [m.strip(" \n\t`") for m in matches]

    # logger.info("extract_tool_calls 2: %r", matches)
    return matches


if __name__ == "__main__":
    import sys
    text = sys.stdin.read()
    print(extract_tool_calls(text))
