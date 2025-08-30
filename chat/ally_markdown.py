#!/usr/bin/env python3-allemande

""" Allemande markdown library """

import asyncio
import html
import logging
import os
import re
import sys
from urllib.parse import urlparse
import random
from typing import Any

import markdown
from markdown_it import MarkdownIt
from mdformat.renderer import MDRenderer
import mdformat_light_touch  # type: ignore

import fetch
from ally_room import check_access, safe_path_for_local_file
from bb_lib import lines_to_messages
from ally.quote import quote_words  # type: ignore  # pylint: disable=wrong-import-order


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
# logger.setLevel(logging.DEBUG)


ROOMS_DIR = os.environ["ALLEMANDE_ROOMS"]
ALLYCHAT_CHAT_URL = os.environ["ALLYCHAT_CHAT_URL"]


# see: https://python-markdown.github.io/extensions/
MARKDOWN_EXTENSIONS = [
    "abbr",
    # 'attr_list',
    "def_list",
    #    "fenced_code",
    "pymdownx.superfences",
    "pymdownx.highlight",
    "footnotes",
    "md_in_html",
    "tables",
    "admonition",
    # 'codehilite',
    # 'legacy_attrs',
    # 'legacy_em',
    # 'meta',
    "nl2br",
    "sane_lists",
    # 'smarty',
    "toc",
    "wikilinks",
    #   "markdown_katex",  # do this in the browser
    #    "markdown_criticmarkup",
    "attr_list",
#    "urlize",
]

MARKDOWN_EXTENSION_CONFIGS = {
#     "markdown_katex": {
#         # 		'no_inline_svg': True, # fix for WeasyPrint
#         "insert_fonts_css": True,
#     },
    "pymdownx.highlight": {
        "use_pygments": False,
    },
}

md_parser = MarkdownIt()
md_parser.disable("escape")
md_formatter = MDRenderer()


def quote_inline_math(pre, d1, math, d2, post):
    """Process potential inline math delimited by matching delimiters, wrapping math content in $`...`$"""
    logger.debug("quote_inline_math")
    logger.debug("  pre:  %s", pre)
    logger.debug("  d1:   %s", d1)
    logger.debug("  math: %s", math)
    logger.debug("  d2:   %s", d2)
    logger.debug("  post: %s", post)
    # check if it looks like math...
    is_math = True
    if d1 == r"$``" and d2 == r"``$":
        pass
    elif d1 == r"$`" and d2 == r"`$":
        pass
    elif d1 == r"`$" and d2 == r"$`":
        pass
    elif d1 == r"\(" and d2 == r"\)" and " " not in math:  # hack for image prompt \(medium\) etc!
        is_math = False
    elif d1 == r"\(" and d2 == r"\)":
        pass
    elif d1 == r"\[" and d2 == r"\]":
        pass
    elif re.match(r"^\w", post):
        is_math = False
    elif re.match(r"\w$", pre):
        is_math = False
    if not is_math:
        return f"{d1}{math}{d2}", False
#    math = fix_math_escape_percentages(math)
    return f"""<code class="language-latex">{math}</code>""", True


# def fix_math_escape_percentages(math_content):
#     """Escape unescaped % symbols in math content"""
#     # FIXME: This approach assumes that a % symbol immediately preceded by a
#     # backslash is already escaped. This is not always the case.
#     return re.sub(r"(?<!\\)%", r"\%", math_content)


def find_and_fix_inline_math(part: str) -> tuple[str, bool]:
    """Find and fix inline math in text without quoted code."""
    # run the regexpes repeatedly to work through the string

    has_math = False
    start = 0
    while True:
        match = re.match(
            r"""
            (.*?)          # Group 1: Any characters (non-greedy)
            (
                (          # Group 2: Inline math with $$...$$
                    \$\$
                    ((?!\$\$).+?)  # Group 3: Math content
                    \$\$
                ) |
                (          # Group 4: Inline math with $...$
                    (?<!\$)\$
                    ((?:\\\$|[^$])+?)  # Group 5: Math content
                    \$
                ) |
                (          # Group 6: Inline math with \[...\]
                    \\\[
                    (.+?)  # Group 7: Math content
                    \\\]
                ) |
                (          # Group 8: Inline math with \(...\)
                    \\\(
                    (.+?)  # Group 9: Math content
                    \\\)
                ) |
                (          # Group 10: Inline math with $``...``$
                    \$``
                    ((?!``).+?)  # Group 11: Math content
                    ``\$
                ) |
                (          # Group 12: Inline math with $`...`$
                    \$`
                    ([^`]+?)  # Group 13: Math content
                    `\$
                ) |
                (          # Group 14: Inline math with `$...$`
                    `\$
                    ((?:\\\$|[^$])+?)  # Group 15: Math content
                    \$`
                )
            )
            (.*)           # Group 16: Any remaining characters
            $
            """,
            part[start:],
            re.VERBOSE | re.DOTALL,
        )
        if match is None:
#            part = part[:start] + html.escape(part[start:], quote=False)
            break
        groups = match.groups()
        pre, post = groups[0], groups[16]
        if groups[2]:
            d1, math, d2 = "$$", groups[3], "$$"
        elif groups[4]:
            d1, math, d2 = "$", groups[5], "$"
        elif groups[6]:
            d1, math, d2 = r"\[", groups[7], r"\]"
        elif groups[8]:
            d1, math, d2 = r"\(", groups[9], r"\)"
        elif groups[10]:
            d1, math, d2 = "$``", groups[11], "``$"
        elif groups[12]:
            d1, math, d2 = "$`", groups[13], "`$"
        elif groups[14]:
            d1, math, d2 = "`$", groups[15], "$`"
        else:
            raise ValueError("No math group matched")
        replaced, has_math1 = quote_inline_math(pre, d1, math, d2, post)
        has_math = has_math or has_math1
#        pre = html.escape(pre, quote=False)
        part = part[:start] + pre + replaced + post
        start += len(pre) + len(replaced)

    return part, has_math


def preprocess_normal_markdown(in_text: str, bb_file: str) -> tuple[str, bool]:
    """Find and fix inline math in markdown, also preprocess links."""
    match = re.match(r"(\n*)(.*?)(\n*)$", in_text, re.DOTALL)
    if match is None:
        logger.error("preprocess_normal_markdown: internal error, regexp failed which should always match")
        return in_text, False
    newlines_before, text, newlines_after = match.groups()

    has_math = False

    # MarkdownIt replaces \( with ( etc, so we need to fix math first, I think it will be okay in most cases,
    # but we need to be careful with code blocks
    # This should match the whole string
    code_pattern = r"""
        (\$``(?!``).*?``\$)     # Math case 1
        |
        (\$`[^`]*?`\$)          # Math case 2
        |
        (`\$(?:\\\$|[^$])*?\$`)  # Math case 3
        |
        (````.*?````)   # Quad-quoted inline code
        |
        (```.*?```)     # Triple-quoted inline code
        |
        (``.*?``)       # Double-quoted inline code
        |
        (`.*?`+)        # Single-quoted inline code, with a catch-all for multi backticks
        |
        ([\s\S]+?)(?=`|\$`|$)    # Any other text, non-greedy, until a backtick or end of string
    """

    # Find all matches
    matches = re.finditer(code_pattern, text, re.VERBOSE)  # | re.DOTALL

    new_parts = []
    prev_end = 0
    for match in matches:
        if prev_end != match.start():
            raise ValueError("preprocess_normal_markdown: internal error, finditer did not match entire string (1)")
        prev_end = match.end()
        part = next(x for x in match.groups() if x is not None)

        if part.startswith("`") and not part.startswith("`$"):
            new_parts.append(part)
            continue

        # Process the part to find inline math
        logger.debug("part: %s", part)
        part, has_math_part = find_and_fix_inline_math(part)
        logger.debug("part after: %s", part)
        has_math = has_math or has_math_part

        # escape <lora> so visible
        part = re.sub(r"<(lora:.*?)>", r"&lt;\1&gt;", part)

        new_parts.append(part)

    if text and prev_end != len(text):
        raise ValueError("preprocess_normal_markdown: internal error, finditer did not match entire string (2)")

    text = "".join(new_parts)

    # Now fix the links

    # First replace ' ' with '+' in URLs
    def space_to_plus(m: re.Match) -> str:
        """Replace spaces in markdown links with '+'"""
        return m.group(1) + "(" + m.group(2).replace(" ", "+") + ")"
    text = re.sub(r"(?<!!)(\[[^]]*])\((.*?)\)", space_to_plus, text)

    tokens = md_parser.parse(text)

    def process_tokens(tokens):
        nonlocal has_math
        for token in tokens:
            if token.children:
                process_tokens(token.children)
            if token.type == 'link_open':
                token.attrs['href'] = fix_link(token.attrs['href'], bb_file)

    process_tokens(tokens)

    # render back to markdown using mdformat
    options = {
        "number": True,
        "parser_extension": [mdformat_light_touch],
    }
    logger.debug("tokens: %r", tokens)

    env: dict = {}
    out_text = md_formatter.render(tokens, options, env)

    # This should not be needed now with mdformat_light_touch:
    # replace $\` and \`$ with $` and `$  :(
    # out_text = out_text.replace(r"$\`", "$`").replace(r"\`$", "`$")

    out_text = newlines_before + out_text.strip("\n") + newlines_after

    if out_text != in_text:
        logger.debug("preprocess_normal_markdown:\n1: %s\n2: %s\n3: %s", in_text, text, out_text)

    return out_text, has_math


def fix_link(href: str, bb_file: str) -> str:
    """Fix room links"""
    # parse the URL
    url = urlparse(href)
    # is it a remote URL?
    if url.scheme or url.netloc:
        return href
    # is the final part a room, folder, or editable file name (file without an extension, or .yml .m .txt .md etc?)
    logger.info("Trying to match link: %r", href)
    if href.endswith("/") or re.search(r"(^|/)[^\./]+(.yml|.m|.txt|.md|/|)$", href):
        try:
            _safe_path, href = safe_path_for_local_file(bb_file, href)
        except ValueError as e:
            logger.warning("Invalid path: %s", e)
            # TODO should we return maybe a javascript warning or something?
            return href
        href = f"""{ALLYCHAT_CHAT_URL}/#{href}"""
    return href


HTML_TAGS = quote_words(
    """
html base head link meta style title body address article aside footer header
h1 h2 h3 h4 h5 h6 hgroup main nav section blockquote dd div dl dt figcaption
figure hr li main ol p pre ul a abbr b bdi bdo br cite code data dfn em i kbd
mark q rb rp rt rtc ruby s samp small span strong sub sup time u var wbr area
audio img map track video embed iframe object param picture source canvas
noscript script del ins caption col colgroup table tbody td tfoot th thead tr
button datalist fieldset form input label legend meter optgroup option output
progress select textarea details dialog menu summary slot template acronym
applet basefont bgsound big blink center command content dir element font frame
frameset image isindex keygen listing marquee menuitem multicol nextid nobr
noembed noframes plaintext shadow spacer strike tt xmp
"""
)

SVG_TAGS = quote_words(
    """
a animate animateMotion animateTransform circle clipPath defs desc discard
ellipse feBlend feColorMatrix feComponentTransfer feComposite feConvolveMatrix
feDiffuseLighting feDisplacementMap feDistantLight feDropShadow feFlood feFuncA
feFuncB feFuncG feFuncR feGaussianBlur feImage feMerge feMergeNode feMorphology
feOffset fePointLight feSpecularLighting feSpotLight feTile feTurbulence filter
foreignObject g image line linearGradient marker mask metadata mpath path
pattern polygon polyline radialGradient rect script set stop style svg switch
symbol text textPath title tspan use view
"""
)

ALLYCHAT_TAGS = quote_words(
    """
ac
"""
)

RE_TAGS = re.compile(rf"""</?({"|".join(list(set(HTML_TAGS + SVG_TAGS + ALLYCHAT_TAGS)))})\b""", flags=re.IGNORECASE)


# pylint: disable=too-many-locals, too-many-branches, too-many-statements
async def preprocess(content: str, bb_file: str, user: str | None) -> tuple[str, bool]:
    """Preprocess chat message content, for markdown-katex, and other fixes"""

    # replace $foo$ with $`foo`$
    # replace $$\n...\n$$ with ```latex\n...\n```

    has_math = False

    out = []

    # make sure <think> tags are on their own lines...
    content = re.sub(r"\s*(</?think>)\s*", r"\n\1\n", content, flags=re.IGNORECASE)

    in_math = False
    in_code = 0
    in_script = False
    in_svg = False  # we need to avoid line breaks in SVG unfortunately
    was_blank = False

    # accumulate normal lines to process together with process_normal_markdown
    normal_lines: list[str] = []

    is_normal_line = False

    def do_normal_lines():
        nonlocal normal_lines, has_math
        text = "\n".join(normal_lines) + "\n"
        text, has_math1 = preprocess_normal_markdown(text, bb_file)
        has_math = has_math or has_math1
        normal_lines.clear()
        return text

    for line in content.splitlines():
        logger.debug("line: %r", line)
#         is_markup = False
#         # if first and re.search(r"\t<", line[0]):
#         #     is_markup = True
#         if not in_code and re.search(RE_TAGS, line):
#             is_markup = True
#         is_markdown_image = re.search(r"!\[.*\]\(.*\)", line)
        logger.debug("check line: %r", line)
        is_math_start = bool(re.match(r"\s*(\$\$|```tex|```latex|```math|\\\[)$", line))
        is_math_end = bool(re.match(r"\s*(\$\$|```|\\\])$", line))
        is_normal_line = False
        if re.match(r"\s*<(script|style|svg)\b", line, flags=re.IGNORECASE) and not in_code:
            in_code = 1
            in_script = True
            in_svg = bool(re.match(r"\s*<svg\b", line, flags=re.IGNORECASE))
            if in_svg:
                out.append(line)
            else:
                out.append(line + "\n")
            # This is getting shady...!
            if re.search(r"</(script|style|svg)>\s*$", line, flags=re.IGNORECASE):
                in_code = 0
                in_script = False
                in_svg = False
        elif re.match(r"\s*</(script|style|svg)>\s*$", line, flags=re.IGNORECASE) and in_script:
            out.append(line + "\n")
            in_code = 0
            in_script = False
            in_svg = False
#         elif is_markup or is_markdown_image:
#             out.append(line + "\n")
        elif is_math_start and not in_code:
            out.append("```latex\n")
            in_math = True
            has_math = True
            in_code += 1
        elif is_math_end and in_math:
            out.append("```\n")
            in_math = False
            in_code = 0
        elif in_math:
#            line = fix_math_escape_percentages(line)
            out.append(line + "\n")
        elif re.match(r"\s*```", line) and not in_code:
            logger.debug("start code 1")
            if not was_blank:
                out.append("\n")
            out.append(line + "\n")
            in_code = 1
        elif re.match(r"\s*```\w", line) and not in_script:
            logger.debug("start code 2")
            if not was_blank:
                out.append("\n")
            out.append(line + "\n")
            in_code += 1
        elif re.match(r"\s*```", line) and in_code:
            logger.debug("end code")
            out.append(line + "\n")
            in_code -= 1
        elif in_svg:
            logger.debug("SVG line: %r", line)
            out.append(line)
        elif in_code:
            logger.debug("code line: %r", line)
            out.append(line + "\n")
        elif re.match(r"^\s*<think(ing)?>$", line, flags=re.IGNORECASE):
            out.append("""<details markdown="1" class="think">\n<summary>thinking</summary>\n""")
        elif re.match(r"^\s*</think(ing)?>$", line, flags=re.IGNORECASE):
            out.append("""</details>\n""")
        elif m := re.match(r"^\s*\[(.*?)\]\((.*?)\){(.*?)}\s*$", line):
            text = await process_include_maybe(line, bb_file, user, m.group(1), m.group(2), m.group(3))
            if not text.endswith("\n"):
                text += "\n"
            out.append(text)
        else:
            logger.debug("not in code or anything")
            normal_lines.append(line)
            is_normal_line = True

        if not is_normal_line and normal_lines:
            text = do_normal_lines()
            out.insert(-1, text)

    if normal_lines:
        text = do_normal_lines()
        out.append(text)

    out = add_blanks_after_code_blocks(out)

    content = "".join(out)
    logger.debug("preprocess content: %s, has_math: %s", content)
    return content, has_math


# pylint: disable=too-many-arguments, too-many-positional-arguments
async def process_include_maybe(line: str, bb_file: str, user: str | None, text: str, url_str: str, attributes_str: str) -> str:
    """Process an include directive"""
    attributes = parse_markdown_attributes(attributes_str)
    include = attributes.get("include")
    code = attributes.get("code")
    hide = attributes.get("hide")
    if not include:
        return line
    # basic literal include for now
    try:
        path = await resolve_url_path(bb_file, url_str, user, do_fetch=True)
        if path is None:
            raise ValueError("process_include_maybe: internal error: path is None with throw=True")
    except Exception as e:  # pylint: disable=broad-exception-caught
        logger.warning("Include error: %s, %s", url_str, e)
        return line

    try:
        with open(path, encoding="utf-8") as f:
            text = f.read()
    except (FileNotFoundError, PermissionError) as e:
        logger.warning("Include file not readable: %s: %s", path, e)
        return line

    if not text.endswith("\n"):
        text += "\n"
    lang = "" if code is True else code
    if lang is not None:
        text = f"```{lang}\n{text}\n```"
    if hide and lang is not None:
        text = f"\n{text}\n"
    if hide:
        text = f"""{line} <details markdown="1">\n<summary>include</summary>\n{text}</details>\n"""
    else:
        text = f"{line}\n\n" + text
    return text


async def resolve_url_path(file: str, url: str, user: str | None, throw: bool = True, do_fetch: bool = False) -> str | None:
    """
    Resolve a URL path, handling both local and remote URLs.

    Args:
        url: The URL or local path
        throw: Whether to raise exceptions on errors

    Returns:
        Resolved local filesystem path or URL

    Raises:
        ValueError: If the path is invalid and throw=True
        PermissionError: If access is denied and throw=True
        IOError: If fetch fails and throw=True
    """
    try:
        # Parse URL to determine if local or remote
        parsed_url = urlparse(url)

        # Remote URL - cache
        if parsed_url.scheme in ('http', 'https'):
            if do_fetch:
                cached_path = await fetch.fetch_cached(url)
                return cached_path
            return str(url)

        if parsed_url.scheme:
            raise ValueError(f"Unsupported URL scheme: {parsed_url.scheme}")

        # Local path
        # TODO improve this code, I think it's safe but it's not very simple
        safe_path, _rel_path = safe_path_for_local_file(file, url)  # type: ignore

        # Check access permissions
        if not check_access(user, safe_path):
            raise PermissionError(f"Access denied to {safe_path} for user {user}")

        if not os.path.exists(safe_path):
            raise FileNotFoundError(f"Local file not found: {safe_path}")

        return str(safe_path)

    except Exception as e:  # pylint: disable=broad-exception-caught
        logging.error("Error resolving file path %s: %s", url, e)
        if throw:
            raise
        return None


def parse_markdown_attributes(attr_str: str) -> dict:
    """Parse attributes in markdown format, e.g. {#id .class key=value key2="value 2"}"""
    attrs: dict[str, Any] = {}
    pos = 0
    attr_str = attr_str.strip('{}')

    pattern = r'''
        \s*                         # Leading whitespace
        (?:
            ([#.])([^\s#.=]+)      # #id or .class
            |
            ([^\s=#.][^\s=]*)      # Key (for key=value or boolean)
            (?:
                \s*=\s*            # = with optional whitespace
                (?:
                    (["'])(.*?)\4   # Quoted value
                    |
                    ([^\s"']+)     # Unquoted value
                )
                |
                ()                 # No value (boolean attribute)
            )?
        )
        \s*                        # Trailing whitespace
    '''

    while pos < len(attr_str):
        match = re.match(pattern, attr_str[pos:], re.VERBOSE)
        if not match:
            raise ValueError(f"Invalid attribute syntax at position {pos}: {attr_str[pos:]}")

        prefix, id_class, key, quote, quoted_val, unquoted_val, _ = match.groups()

        if prefix:  # #id or .class
            attr_type = 'id' if prefix == '#' else 'class'
            attrs.setdefault(attr_type, []).append(id_class)
        else:  # key=value or boolean attribute
            value = quoted_val if quote else unquoted_val if unquoted_val else True
            attrs[key] = value

        pos += match.end()
    return attrs


def add_blanks_after_code_blocks(lines: list[str]) -> list[str]:
    """ Add blank lines after code blocks to avoid markdown issues."""
    out = []
    in_code_block = False
    code_block_indent = 0

    for i, line in enumerate(lines):
        out.append(line)

        stripped = line.strip()
        if not stripped:
            continue

        indent = len(line) - len(line.lstrip())

        if stripped == "```" and in_code_block:
            if indent <= code_block_indent:  # Close block if at same or less indent
                in_code_block = False
                # Add blank line if:
                # 1. Next line exists and isn't blank
                # 2. Next line isn't another code block
                # 3. Next line isn't less indented
                if (
                    i + 1 < len(lines)
                    and lines[i + 1].strip()
                    and not lines[i + 1].strip().startswith("```")
                    and len(lines[i + 1]) - len(lines[i + 1].lstrip()) <= indent
                ):
                    out.append("")

        elif stripped.startswith("```") and not in_code_block:
            in_code_block = True
            code_block_indent = indent

    return out


math_cache: dict[str, str] = {}


SPACE_MARKER = "§S§"
TAB_MARKER = "§T§"


def escape_indents(text):
    """Escape leading whitespace in each line."""
    global SPACE_MARKER, TAB_MARKER  # pylint: disable=global-statement
    while SPACE_MARKER in text or TAB_MARKER in text:
        r = random.randint(0, 999999)
        SPACE_MARKER = f"§S{r}§"
        TAB_MARKER = f"§T{r}§"

    lines = text.splitlines()
    processed_lines = []

    for line in lines:
        # Match leading whitespace
        indent_match = re.match(r"^(\s+)", line)
        if indent_match:
            indent = indent_match.group(1)
            # Replace spaces and tabs with markers
            escaped_indent = indent.replace(" ", SPACE_MARKER).replace("\t", TAB_MARKER)
            # Replace the original indent with the escaped version
            processed_line = escaped_indent + line[len(indent) :]
        else:
            processed_line = line
        processed_lines.append(processed_line)

    return "\n".join(processed_lines)


def restore_indents(text):
    """Restore leading whitespace in each line."""
    text = text.replace(SPACE_MARKER, " ")
    text = text.replace(TAB_MARKER, "\t")
    return text


def markdown_to_html(content: str) -> str:
    """Convert markdown to HTML."""
    # Note: mdformat gives 3-space indents, so we need to use tab_length=3
    html_content = markdown.markdown(content, tab_length=3, extensions=MARKDOWN_EXTENSIONS, extension_configs=MARKDOWN_EXTENSION_CONFIGS)
    return html_content


async def message_to_html(message: dict[str, str], bb_file: str) -> str:
    """Convert a chat message to HTML."""
    #     logger.info("converting message to html: %r", message["content"])
    content, has_math = await preprocess(message["content"], bb_file, message.get("user"))
    if content in math_cache:
        html_content = math_cache[content]
    else:
        try:
            #             logger.info("markdown content: %r", content)
            # content = escape_indents(content)
            html_content = markdown_to_html(content)
            # html_content = restore_indents(html_content)
            #             logger.info("html content: %r", html_content)
            html_content = html_postprocess(html_content)
        #            html_content = "\n".join(wrap_indent(line) for line in html_content.splitlines())
        #             html_content = html_content.replace("<br />", "")
        #             html_content = html_content.replace("<p>", "")
        #             html_content = html_content.replace("</p>", "\n")
        except Exception as e:  # pylint: disable=broad-exception-caught
            logger.error("markdown error: %r", e)
            html_content = f"<pre>{html.escape(content)}</pre>"
        if has_math:
            math_cache[content] = html_content
    #     logger.info("html_content 2: %r", html_content)
    if html_content == "":
        html_content = "&nbsp;"
    user = message.get("user")
    if user:
        user_ee = html.escape(user)
        return f"""<div class="message" user="{user_ee}"><div class="label">{user_ee}:</div><div class="content">{html_content}</div></div>\n\n"""
    return f"""<div class="message narrative"><div class="content">{html_content}</div></div>\n\n"""


LANGUAGES = r"python|bash|sh|shell|console|html|xml|css|javascript|js|json|yaml|yml|toml|ini|sql|c|cpp|csharp|cs|java|kotlin|swift|php|perl|ruby|lua|rust|go|dart|scala|groovy|powershell|plaintext"


def html_postprocess(html_text: str) -> str:
    """Fix various issues with HTML generated by markdown."""

    # Hopefully not needed with superfences:
#     def replace_nested_code_block(match):
#         class_attr = f' class="language-{match.group(1)}"' if match.group(1) else ""
#         return f"<pre><code{class_attr}>{match.group(2)}</code></pre>"
#
#     # fix nested code blocks
#     html = re.sub(
#         rf"<p><code>((?:{LANGUAGES})\n)?(.*?)</code></p>", replace_nested_code_block, html, flags=re.DOTALL | re.IGNORECASE
#     )

    # fix <summary> tags, which sometimes get broken
    html_text = re.sub(r"<p><summary>(.*?)</summary><br\s*/>", r"<summary>\1</summary><p>", html_text)
    html_text = re.sub(r"<img ", r"<img loading=lazy ", html_text)

    # Disabled for now, don't want to mess up code!
#     # remove empty paragraphs: could potentially mess up code but whatever
#     html = re.sub(rf"<p></p>", r"", html)
    return html_text


# @argh.arg('--doctype', nargs='?')
# @argh.arg('--stylesheets', nargs='*', type=str, default=["/room.css"])
# @argh.arg('--scripts', nargs='*', type=str, default=["https://ucm.dev/js/util.js", "/room.js"])
# def chat_to_html(doctype="html", stylesheets=None, scripts=None):
def chat_to_html():
    """Convert an Allemande chat file to HTML."""
    # if doctype:
    #     print(f"""<!DOCTYPE {doctype}>""")
    # for src in stylesheets:
    #     print(f"""<link rel="stylesheet" href="{html.escape(src)}">""")
    # for src in scripts:
    #     print(f"""<script src="{html.escape(src)}"></script>""")
    bb_file = ""  # TODO
    for message in lines_to_messages(sys.stdin.buffer):
        print(asyncio.run(message_to_html(message, bb_file)))
