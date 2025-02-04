#!/usr/bin/env python3-allemande

""" Allemande chat file format library """

import os
import sys
import html
from pathlib import Path
import re
import logging
from typing import Iterator, Any, TypeAlias, Protocol, TextIO
import shutil
import subprocess

import argh
import markdown
from starlette.exceptions import HTTPException
import aiofiles

import video_compatible


EXTENSION = ".bb"
ROOMS_DIR = os.environ["ALLEMANDE_ROOMS"]

global_admins = ["sam"]  # TODO from enviorment variable


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Symbol:  # pylint: disable=too-few-public-methods
    """A symbol singleton object"""

    def __init__(self, name):
        """Create a new symbol with the given name"""
        self.name = name

    def __repr__(self):
        """Return a string representation of the symbol"""
        return f"<{self.name}>"


USER_NARRATIVE = Symbol("Narrative")
USER_CONTINUED = Symbol("Continued")
ROOM_MAX_LENGTH = 100
ROOM_MAX_DEPTH = 10

# see: https://python-markdown.github.io/extensions/
MARKDOWN_EXTENSIONS = [
    "abbr",
    # 'attr_list',
    "def_list",
    "fenced_code",
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
    "markdown_katex",
]

MARKDOWN_EXTENSION_CONFIGS = {
    "markdown_katex": {
        # 		'no_inline_svg': True, # fix for WeasyPrint
        "insert_fonts_css": True,
    },
}


class Room:
    """A chat room object."""

    def __init__(self, name=None, path=None):
        """Create a room object."""
        if path:
            assert name is None
            assert isinstance(path, Path)
            self.path = path
            self.name = path.relative_to(ROOMS_DIR).with_suffix("").as_posix()
        else:
            name = sanitize_pathname(name)
            assert isinstance(name, str)
            assert not name.startswith("/")
            assert not name.endswith("/")
            self.name = name
            self.path = Path(ROOMS_DIR, name + EXTENSION)
        self.parent = self.path.parent
        self.parent.mkdir(parents=True, exist_ok=True)
        self.parent_url = Path("/", self.name).parent

    def touch(self):
        """Touch / poke a room."""
        self.path.touch()

    def append(self, text):
        """Append text to a room."""
        with self.path.open("a", encoding="utf-8") as f:
            f.write(text)

    def check_admin(self, user):
        """Check if a user is an admin."""
        if user in global_admins:
            return True
        components = self.name.split("/")
        top_dir = components[0]
        return user in top_dir.split(",")

    def clear(self, op="clear"):
        """Clear a room."""
        if op == "archive":
            # run room-rotate script with room name
            # TODO in Python
            subprocess.run(["room-rotate", self.name], check=True)
        elif op == "rotate":
            # run room-rotate script with room name
            # TODO in Python, archive half, keep half. Media?
            subprocess.run(["room-rotate", self.name], check=True)
        else:
            # unlink the file
            self.path.unlink()
            # with self.path.open("w", encoding="utf-8"):
            # 	pass

    def undo(self, n=1):
        """Remove the last n messages from a room."""
        # Messages are delimited by blank lines, and the file should end with a blank line.
        if n <= 0:
            return

        count_bytes = 0
        for line in tac(self.path, binary=True, keepends=True):
            if line == b"\n":
                n -= 1
            if n < 0:
                break
            count_bytes += len(line)

        with open(self.path, "a+b") as f:
            logger.debug("undo truncating file %s", self.path)
            logger.debug("undo truncate %d bytes", count_bytes)
            logger.debug("current file size: %d", f.tell())
            f.truncate(f.tell() - count_bytes)

    def last(self, n=1):
        """Get the last n messages from a room."""
        if n <= 0:
            return []

        messages = []
        message = ""
        for line in tac(self.path, binary=False, keepends=True):
            if line == "\n" and message:
                messages.append(message)
                message = ""
            if line == "\n":
                n -= 1
            else:
                message = line + message
            if n < 0:
                break
        else:
            if message:
                messages.append(message)

        return list(reversed(messages))


# TODO move to a separate module
def tac(file, chunk_size=4096, binary=False, keepends=False):
    """Read a file in reverse, a line at a time."""
    with open(file, "rb") as f:
        # Seek to end of file
        f.seek(0, 2)
        # Get total file size
        total_size = remaining_size = f.tell()
        pos = total_size
        block = b""
        while remaining_size > 0:
            # Calculate size to read, limited by chunk_size
            read_size = min(chunk_size, remaining_size)
            # Move position back by read_size
            pos -= read_size
            f.seek(pos)
            # Read chunk and combine with previous block
            chunk = f.read(read_size)
            current = chunk + block
            # Split off any partial line at the start
            parts = current.split(b"\n", 1)
            if len(parts) > 1:
                parts[0] += b"\n"
                lines_text = parts[1]
                if not binary:
                    lines_text = lines_text.decode()
                lines = lines_text.splitlines(keepends=keepends)
                # Yield complete lines in reverse
                for line in reversed(lines):
                    yield line
            block = parts[0]
            remaining_size -= read_size
        # Yield final remaining text
        if block:
            if not binary:
                block = block.decode()
            yield block


def safe_join(base_dir: Path, path: Path) -> Path:
    """Return a safe path under base_dir, or raise ValueError if the path is unsafe."""
    safe_path = base_dir.joinpath(path).resolve()
    if base_dir in safe_path.parents:
        return safe_path
    raise ValueError(f"Invalid or unsafe path provided: {base_dir}, {path}")


def sanitize_filename(filename):
    """Sanitize a filename, allowing most characters."""

    assert isinstance(filename, str)
    assert "/" not in filename

    # remove leading dots and whitespace:
    # don't want hidden files
    filename = re.sub(r"^[.\s]+", "", filename)

    # remove trailing dots and whitespace:
    # don't want confusion around file extensions
    filename = re.sub(r"[.\s]+$", "", filename)

    # squeeze whitespace
    filename = re.sub(r"\s+", " ", filename)

    return filename


def sanitize_pathname(room):
    """Sanitize a pathname, allowing most characters."""

    # split into parts
    parts = room.split("/")

    # sanitize each part
    parts = map(sanitize_filename, parts)

    # remove empty parts
    parts = list(filter(lambda x: x, parts))

    if not parts:
        raise HTTPException(status_code=400, detail="Please enter the name of a room.")

    if len(parts) > ROOM_MAX_DEPTH:
        raise HTTPException(status_code=400, detail=f"The room is too deeply nested, max {ROOM_MAX_DEPTH} parts.")

    # join back together
    room = "/".join(parts)

    if len(room) > ROOM_MAX_LENGTH:
        raise HTTPException(status_code=400, detail=f"The room name is too long, max {ROOM_MAX_LENGTH} characters.")

    # check for control characters
    if re.search(r"[\x00-\x1F\x7F]", room):
        raise HTTPException(status_code=400, detail="The room name cannot contain control characters.")

    return room


def split_message_line(line):
    """Split a message line into user and content."""

    if not line.endswith("\n"):
        line += "\n"

    if "\t" in line:
        label, content = line.split("\t", 1)
    else:
        label = None
        content = line

    logger.debug("split_message_line line, label, content: %r, %r, %r", line, label, content)

    if label is None:
        user = USER_NARRATIVE
    elif label == "":
        user = USER_CONTINUED
    elif label.endswith(":"):
        user = label[:-1]
    else:
        logger.warning("Invalid label missing colon, in line: %s", line)
        user = USER_NARRATIVE
        content = label + "\t" + content

    return user, content


def lines_to_messages(lines):
    """A generator to convert an iterable of lines to chat messages."""

    message: Optional[Dict] = None

    lines = iter(lines)
    skipped_blank = 0

    while True:
        line = next(lines, None)
        if line is None:
            break

        if isinstance(line, bytes):
            line = line.decode("utf-8")

        # skip blank lines
        if line.rstrip("\r\n") == "":
            skipped_blank += 1
            continue

        user, content = split_message_line(line)

        # accumulate continued lines
        if message and user == USER_CONTINUED:  # pylint: disable=unsupported-assignment-operation
            message["content"] += "\n" * skipped_blank + content  # pylint: disable=unsupported-assignment-operation
            skipped_blank = 0
            continue

        if not message and user == USER_CONTINUED:
            logger.warning("Continued line with no previous incomplete message: %s", line)
            user = USER_NARRATIVE

        if message and user == USER_NARRATIVE and "user" not in message:  # pylint: disable=unsupported-membership-test
            message["content"] += "\n" * skipped_blank + content  # pylint: disable=unsupported-assignment-operation
            skipped_blank = 0
            continue

        # yield the previous message
        if message:
            logger.debug(message)
            yield message
            message = None

        # start a new message
        skipped_blank = 0
        if user == USER_NARRATIVE:
            message = {"content": content}
        else:
            message = {"user": user, "content": content}

    if message is not None:
        logger.debug(message)
        yield message


def test_split_message_line():
    """Test split_message_line."""
    line = "Ally:	Hello\n"
    user, content = split_message_line(line)
    assert user == "Ally"
    assert content == "Hello\n"


def test_lines_to_messages():
    """Test lines_to_messages."""
    lines = """Ally:	Hello
	World
Sam:	How are you?
"""
    messages = list(lines_to_messages(lines.splitlines()))
    assert len(messages) == 2
    assert messages[0]["user"] == "Ally"
    assert messages[0]["content"] == "Hello\nWorld\n"
    assert messages[1]["user"] == "Sam"
    assert messages[1]["content"] == "How are you?\n"


def message_to_text(message):
    """Convert a chat message to text."""
    user = message.get("user")
    content = message["content"]
    if user:
        lines = content.splitlines() or [""]
        lines2 = []
        lines2.append(f"{user}:\t{lines[0]}\n")
        for line in lines[1:]:
            lines2.append(f"\t{line}\n")
        text = "".join(lines2)
    else:
        text = content
    return text.rstrip("\n") + "\n"


def preprocess(content):
    """Preprocess chat message content, for markdown-katex"""

    # replace $foo$ with $`foo`$
    # replace $$\n...\n$$ with ```math\n...\n```

    has_math = False

    def quote_math_inline(pre, d1, math, d2, post):
        """Process potential inline math delimited by matching delimiters, wrapping math content in $`...`$"""
        # check if it looks like math...
        nonlocal has_math
        is_math = True
        if math.startswith("`") and math.endswith("`"):
            # already processed
            has_math = True
            is_math = False
        # 		elif not (re.match(r'^\s.*\s$', math) or re.match(r'^\S.*\S$', math) or len(math) == 1):
        # 			is_math = False
        elif d1 != d2:
            is_math = False
        elif re.match(r"^\w", post):
            is_math = False
        elif re.match(r"\w$", pre):
            is_math = False
        if is_math:
            has_math = True
            return f"$`{math}`$"
        return f"{d1}{math}{d2}"

    out = []

    in_math = False
    in_code = False
    for line in content.splitlines():
        is_html = False
        # if first and re.search(r"\t<", line[0]):
        # 	is_html = True
        if re.search(
            r"</?(html|base|head|link|meta|style|title|body|address|article|aside|footer|header|h1|h2|h3|h4|h5|h6|hgroup|main|nav|section|blockquote|dd|div|dl|dt|figcaption|figure|hr|li|main|ol|p|pre|ul|a|abbr|b|bdi|bdo|br|cite|code|data|dfn|em|i|kbd|mark|q|rb|rp|rt|rtc|ruby|s|samp|small|span|strong|sub|sup|time|u|var|wbr|area|audio|img|map|track|video|embed|iframe|object|param|picture|source|canvas|noscript|script|del|ins|caption|col|colgroup|table|tbody|td|tfoot|th|thead|tr|button|datalist|fieldset|form|input|label|legend|meter|optgroup|option|output|progress|select|textarea|details|dialog|menu|summary|slot|template|acronym|applet|basefont|bgsound|big|blink|center|command|content|dir|element|font|frame|frameset|image|isindex|keygen|listing|marquee|menuitem|multicol|nextid|nobr|noembed|noframes|plaintext|shadow|spacer|strike|tt|xmp)\b",
            line,
        ):
            is_html = True
        logger.debug("check line: %r", line)
        is_math_delim = re.match(r"\s*\$\$$", line)
        if is_math_delim and not in_math:
            out.append("```math")
            in_math = True
            has_math = True
            in_code = True
        elif is_math_delim and in_math:
            out.append("```")
            in_math = False
            in_code = False
        elif re.match(r"^```", line) and not in_code:
            out.append(line)
            in_code = True
        elif re.match(r"^```", line) and in_code:
            out.append(line)
            in_code = False
        else:
            # run the regexp sub repeatedly
            start = 0
            while True:
                logger.debug("preprocess line part from: %r %r", start, line[start:])
                match = re.match(r"^(.*?)(\$\$?)(.*?)(\$\$?)(.*)$", line[start:])
                logger.debug("preprocess match: %r", match)
                if match is None:
                    if not in_code and not is_html:
                        line = line[:start] + html.escape(line[start:])
                    break
                pre, d1, math, d2, post = match.groups()
                replace = quote_math_inline(pre, d1, math, d2, post)
                if not in_code and not is_html:
                    pre = html.escape(pre)
                line = line[:start] + pre + replace + post
                start += len(pre) + len(replace)
            out.append(line)

    content = "\n".join(out) + "\n"
    logger.debug("preprocess content: %r", content)
    return content, has_math


math_cache: dict[str, str] = {}


def message_to_html(message):
    """Convert a chat message to HTML."""
    global math_cache
    logger.debug("converting message to html: %r", message["content"])
    content, has_math = preprocess(message["content"])
    if content in math_cache:
        html_content = math_cache[content]
    else:
        try:
            html_content = markdown.markdown(content, extensions=MARKDOWN_EXTENSIONS, extension_configs=MARKDOWN_EXTENSION_CONFIGS)
        except Exception as e:
            logger.error("markdown error: %r", e)
            html_content = f"<pre>{html.escape(content)}</pre>"
        if has_math:
            math_cache[content] = html_content
    logger.debug("html_content: %r", html_content)
    if html_content == "":
        html_content = "&nbsp;"
    user = message.get("user")
    if user:
        user_ee = html.escape(user)
        return f"""<div class="message" user="{user_ee}"><div class="label">{user_ee}:</div><div class="content">{html_content}</div></div>\n"""
    return f"""<div class="narrative"><div class="content">{html_content}</div></div>\n"""


# @argh.arg('--doctype', nargs='?')
# @argh.arg('--stylesheets', nargs='*', type=str, default=["/room.css"])
# @argh.arg('--scripts', nargs='*', type=str, default=["https://ucm.dev/js/util.js", "/room.js"])
# def chat_to_html(doctype="html", stylesheets=None, scripts=None):
def chat_to_html():
    """Convert an Allemande chat file to HTML."""
    # 	if doctype:
    # 		print(f"""<!DOCTYPE {doctype}>""")
    # 	for src in stylesheets:
    # 		print(f"""<link rel="stylesheet" href="{html.escape(src)}">""")
    # 	for src in scripts:
    # 		print(f"""<script src="{html.escape(src)}"></script>""")
    for message in lines_to_messages(sys.stdin.buffer):
        print(message_to_html(message))


image_extensions = ["jpg", "jpeg", "png", "gif", "svg", "webp"]
audio_extensions = ["mp3", "ogg", "wav", "flac", "aac", "m4a"]
video_extensions = ["mp4", "webm", "ogv", "avi", "mov", "flv", "mkv"]


async def save_uploaded_file(from_path, to_path, file=None):
    """Save an uploaded file."""
    if not file:
        shutil.move(from_path, to_path)
        return
    chunk_size = 64 * 1024
    async with aiofiles.open(to_path, "wb") as ostream:
        while chunk := await file.read(chunk_size):
            await ostream.write(chunk)


def av_element_html(tag, label, url):
    """Return an audio or video element."""

    def ee(s):
        """Encode entities."""
        return html.escape(s, quote=True)

    return f'<{tag} aria-label="{ee(label)}" src="{ee(url)}" controls></{tag}>'


async def upload_file(room_name, user, filename, file=None, alt=None):
    """Upload a file to a room."""
    room = Room(name=room_name)

    name = sanitize_filename(os.path.basename(filename))
    stem, ext = os.path.splitext(name)

    i = 1
    suffix = ""
    while True:
        name = stem + suffix + ext
        file_path = room.parent / name
        if not file_path.exists():
            break
        i += 1
        suffix = "_" + str(i)

    # TODO track which user uploaded which files?

    url = (room.parent_url / name).as_posix()

    logger.info(f"Uploading {name} to {room} by {user}: {file_path=} {url=}")

    await save_uploaded_file(filename, str(file_path), file=file)

    task = None

    ext = ext.lower().lstrip(".")

    if ext in image_extensions:
        medium = "image"
    elif ext in audio_extensions:
        medium = "audio"
    elif ext in video_extensions:
        # webm can be audio or video
        result = await video_compatible.check(file_path)
        if result["video_codecs"]:
            medium = "video"
        else:
            medium = "audio"
        task = lambda: video_compatible.recode_if_needed(file_path, result=result, replace=True)
    else:
        medium = "file"

    relurl = name

    # view options for PDFs
    append = ""
    if ext == "pdf":
        append = "#toolbar=0&navpanes=0&scrollbar=0"
    url += append
    relurl += append

    alt = alt or stem

    alt = re.sub(r"\s+", " ", alt)

    # markdown to embed or link to the file
    if medium == "image":
        markdown = f"![{alt}]({relurl})"
    elif medium == "audio":
        markdown = av_element_html("audio", alt, relurl)
    elif medium == "video":
        markdown = av_element_html("video", alt, relurl)
    else:
        markdown = f"[{alt}]({relurl})"

    return name, url, medium, markdown, task


def chat_read(file, args):
    """Read the chat history from a file."""
    text = ""
    if file and os.path.exists(file):
        with open(file, encoding="utf-8") as f:
            text = f.read()
    # lookahead for non-space after newline
    history = re.split(r"\n+(?=\S|$)", text) if text else []

    if history and not history[-1]:
        history.pop()
    return history


def chat_write(file, history, delim="\n", mode="a", invitation=""):
    """Write or append the chat history to a file."""
    if not file:
        return
    text = delim.join(history) + invitation
    with open(file, mode, encoding="utf-8") as f:
        f.write(text)


if __name__ == "__main__":
    argh.dispatch_command(chat_to_html)
