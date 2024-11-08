#!/usr/bin/env python3-allemande

"""
This module indents HTML nicely, focusing on major elements while keeping
inline elements on a single line with their content.
"""

import sys
import logging
import re
from typing import TextIO
from html.parser import HTMLParser

from argh import arg
import jsbeautifier
import cssbeautifier

from ally import main
from ally.text import stripper
from ally.quote import qw

__version__ = "0.1.5"

logger = main.get_logger()


# List of HTML elements that should not be indented
INLINE_ELEMENTS = {
    *qw(
        """
    a abbr acronym b bdo big br button cite dfn em i img input kbd label map
    object q samp select small span strong sub sup time tt var td th
"""
    )
}

# HTML singleton elements
SINGLETON_ELEMENTS = {
    *qw(
        """
    area base br col embed hr img input link meta param source track wbr
"""
    )
}

# Elements that should appear on their own line but not start an indented container
SINGLE_LINE_ELEMENTS = {*qw("p title tr li")}

# Elements that should preserve their content formatting
PRESERVE_CONTENT_ELEMENTS = {*qw("pre code textarea")}


class HTMLIndenter(HTMLParser):
    def __init__(self, indent="\t", mark_singletons=True):
        super().__init__()
        self.indent = indent
        self.mark_singletons = mark_singletons
        self.indent_level = 0
        self.output = []
        self.current_line = ""
        self.in_inline = 0
        self.in_preserve_content = False
        self.preserve_content = ""

    def handle_decl(self, decl):
        self.output.append(self.indent * self.indent_level + '<!' + decl + '>')

    def handle_comment(self, comment):
        self.output.append(self.indent * self.indent_level + '<!--' + comment + '-->')

    def handle_starttag(self, tag, attrs):
        if self.in_preserve_content:
            self.preserve_content += self.get_starttag_text()
            return

        closer = " /" if self.mark_singletons and tag in SINGLETON_ELEMENTS else ""

        if tag in INLINE_ELEMENTS:
            self.current_line += f"<{tag}{self._format_attrs(attrs)}{closer}>"
            self.in_inline += 1
        elif tag in SINGLE_LINE_ELEMENTS:
            if not self.in_inline:
                self._flush_line()
            self.current_line += f"<{tag}{self._format_attrs(attrs)}{closer}>"
            self.in_inline += 1
        elif tag in PRESERVE_CONTENT_ELEMENTS:
            self._flush_line()
            self.output.append(
                self.indent * self.indent_level
                + f"<{tag}{self._format_attrs(attrs)}{closer}>"
            )
            self.in_preserve_content = True
        else:
            self._flush_line()
            self.output.append(
                self.indent * self.indent_level
                + f"<{tag}{self._format_attrs(attrs)}{closer}>"
            )
            if tag not in SINGLETON_ELEMENTS and tag != "html":
                self.indent_level += 1

    def handle_endtag(self, tag):
        if self.in_preserve_content:
            if tag in PRESERVE_CONTENT_ELEMENTS:
                self.in_preserve_content = False
                self.output.append(self.preserve_content.rstrip())
                self.output.append(self.indent * self.indent_level + f"</{tag}>")
                self.preserve_content = ""
            else:
                self.preserve_content += f"</{tag}>"
            return

        if tag in SINGLETON_ELEMENTS:
            return

        if tag in INLINE_ELEMENTS:
            self.current_line += f"</{tag}>"
        elif tag in SINGLE_LINE_ELEMENTS:
            self.current_line += f"</{tag}>"
            self._flush_line()
        else:
            if tag != "html":
                self.indent_level -= 1
            self._flush_line()
            self.output.append(self.indent * self.indent_level + f"</{tag}>")

        # Flush the line if it's not empty and we're not in an inline context
        if self.current_line.strip() and not self.in_inline:
            self._flush_line()
        if tag in INLINE_ELEMENTS:
            self.in_inline -= 1

    def handle_data(self, data):
        if self.in_preserve_content:
            self.preserve_content += data
            return

        leading_spaces, data, final_spaces = stripper(data)

        if not data:
            return

        data = re.sub(r"\s+", " ", data)

        if self.in_inline:
            self.current_line = (
                self.current_line.rstrip()
                + (" " if leading_spaces else "")
                + data
                + (" " if final_spaces else "")
            )
        else:
            self._flush_line()
            self.output.append(self.indent * self.indent_level + data)

    def close(self):
        self._flush_line()
        return "\n".join(self.output)

    def _flush_line(self):
        if self.current_line.strip():
            self.output.append(
                self.indent * self.indent_level + self.current_line.strip()
            )
        self.current_line = ""

    def _format_attrs(self, attrs):
        return "".join(f' {attr}="{value}"' for attr, value in attrs)


def format_embedded_language(output, indenter, i, indent, tag, beautifier):
    content = []
    opening_tag = indenter.output[i]

    opening_indent_str, _, _ = stripper(opening_tag)
    indent_level = len(opening_indent_str) // len(indent)
    common_indent = (indent_level + 1) * indent

    i += 1
    while i < len(indenter.output) and not indenter.output[i].strip().startswith(
        f"</{tag}>"
    ):
        content.append(indenter.output[i].strip())  # TODO multi-line strings?
        i += 1

    closing_tag = indenter.output[i] if i < len(indenter.output) else f"</{tag}>"
    code = "\n".join(content)  # Exclude closing tag from formatting

    # Check if the container is empty or contains only whitespace
    if not code.strip():
        # Output opening and closing tags on the same line
        output.append(f"{opening_tag}{closing_tag.strip()}")
    else:
        # Configure beautifier options for custom indentation
        opts = beautifier.default_options()
        if indent == "\t":
            opts.indent_with_tabs = True
        else:
            opts.indent_size = len(indent)
            opts.indent_char = " "

        formatted_code = beautifier.beautify(code, opts)

        # logger.debug("%r", formatted_code)

        output.append(opening_tag)
        for line in formatted_code.split("\n"):
            output.append(common_indent + line)
        output.append(closing_tag)

    i += 1
    return i


def indent_html(html: str, indent="\t") -> str:
    """Indent the given HTML string."""
    indenter = HTMLIndenter(indent=indent)
    indenter.feed(html)
    indenter.close()
    output: list[str] = []
    i = 0

    while i < len(indenter.output):
        line = indenter.output[i]
        if m := re.match(r"\s*<(script|style)\b", line):
            tag = m[1]
            beautifier = jsbeautifier if tag == "script" else cssbeautifier
            i = format_embedded_language(output, indenter, i, indent, tag, beautifier)
        else:
            output.append(line)
            i += 1

    return "\n".join(output) + "\n"


def html_indent(
    input_file: TextIO = sys.stdin,
    output_file: TextIO = sys.stdout,
    indent: str = "\t",
) -> None:
    """
    Indent HTML nicely, focusing on major elements while keeping
    inline elements on a single line with their content.
    """
    try:
        indent = " " * int(indent)
    except:
        pass
    html_content = input_file.read()
    indented_html = indent_html(html_content, indent=indent)
    output_file.write(indented_html)


if __name__ == "__main__":
    main.run(html_indent)


# Notes to AI:
#
# - do not add error handling; let the exceptions fly.  ally.run handles them nicely
