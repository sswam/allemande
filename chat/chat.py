#!/usr/bin/env python3-allemande

""" Allemande chat file format library """

import os
import sys
import html
from pathlib import Path
import re
import logging
from typing import Any, TextIO
from dataclasses import dataclass
import shutil
import subprocess
import random
import enum
from stat import S_IFREG, S_IROTH, S_IWOTH

import argh
import markdown
from starlette.exceptions import HTTPException
import aiofiles

import video_compatible
from agents import ALLOWED_AGENTS


os.umask(0o007)


EXTENSION = ".bb"
ROOMS_DIR = os.environ["ALLEMANDE_ROOMS"]

ADMINS = os.environ.get("ALLYCHAT_ADMINS", "").split()
MODERATORS = os.environ.get("ALLYCHAT_MODERATORS", "").split()


class Access(enum.Enum):
    NONE = 0
    READ = 1
    WRITE = 2
    READ_WRITE = 3
    MODERATE = 4
    MODERATE_READ_WRITE = 7
    ADMIN = 15


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class ChatMessage:
    """A single chat message with user (optional) and content."""
    user: str | None
    content: str


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
    "md_in_html",
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

    def write(self, user, content):
    	"""
    	Write a message to a room.
    	We don't convert to HTML here, a follower process does that.
    	"""
    	if not check_access(user, self.name, self.path).value & Access.WRITE.value:
    		raise PermissionError("You are not allowed to post to this room.")

    	if content == "":
    		# touch the markdown_file, to poke some attention
    		self.touch()
    		return

    	if user == user.lower() or user == user.upper():
    		user_tc = user.title()
    	else:
    		user_tc = user
    	user_tc = user_tc.replace(".", "_")
    	message = {"user": user_tc, "content": content}

    	text = message_to_text(message) + "\n"

    	self.append(text)

#     def check_admin(self, user):
#         """Check if a user is an admin."""
#         if user in ADMINS:
#             return True
#         components = self.name.split("/")
#         top_dir = components[0]
#         return user in top_dir.split(",")

    def clear(self, op="clear"):
        """Clear a room."""
        access = check_access(user, self.name, self.path)
        if op == "archive":
            if not access.value & Access.MODERATE.value:
                raise PermissionError("You are not allowed to archive this room.")
            # run room-rotate script with room name
            # TODO in Python
            subprocess.run(["room-rotate", self.name], check=True)
        elif op == "rotate":
            raise NotImplementedError("Room rotation is not implemented yet.")
            # run room-rotate script with room name
            # TODO in Python, archive half, keep half. Media?
            # subprocess.run(["room-rotate", self.name], check=True)
        else:
            if not access.value & Access.ADMIN.value:
                raise PermissionError("You are not allowed to clear this room.")
            # unlink the file
            self.path.unlink()
            # with self.path.open("w", encoding="utf-8"):
            # 	pass

    def undo(self, user, n=1):
        """Remove the last n messages from a room."""
        # Messages are delimited by blank lines, and the file should end with a blank line.
        if n <= 0:
            return

        access = check_access(user, self.name, self.path)
        if n > 1 and not access.value & Access.ADMIN.value:
            raise PermissionError("You are not allowed to undo multiple messages in this room.")

        if not access.value & Access.MODERATE.value:
            raise PermissionError("You are not allowed to undo messages in this room.")

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
    if base_dir in safe_path.parents or base_dir == safe_path:
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

    if room in ("", "/"):
        return room

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


def message_to_text(message: dict[str, Any]) -> str:
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


def chat_message_to_text(message: ChatMessage) -> str:
    """Convert a chat message to text."""
    return message_to_text({"user": message.user, "content": message.content})


def fix_math_escape_percentages(math_content):
    """Escape unescaped % symbols in math content"""
    # FIXME: This approach assumes that a % symbol immediately preceded by a
    # backslash is already escaped. This is not always the case.
    return re.sub(r"(?<!\\)%", r"\%", math_content)


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
            logger.warning("already processed: %r", math)
            has_math = True
            is_math = False
        # 		elif not (re.match(r'^\s.*\s$', math) or re.match(r'^\S.*\S$', math) or len(math) == 1):
        # 			is_math = False
        elif d1 == r"\[" and d2 == r"\]":
            pass
        elif d1 != d2:
            is_math = False
        elif re.match(r"^\w", post):
            is_math = False
        elif re.match(r"\w$", pre):
            is_math = False
        if is_math:
            has_math = True
            math = fix_math_escape_percentages(math)
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
        elif in_math:
            line = fix_math_escape_percentages(line)
            out.append(line)
        else:
            # run the regexp sub repeatedly
            start = 0
            while True:
                logger.debug("preprocess line part from: %r %r", start, line[start:])
                match = re.match(r"^(.*?)(\$\$?|\\\[)(.*?)(\$\$?|\\\])(.*)$", line[start:])
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

    if not check_access(user, room_name, room.path).value & Access.WRITE.value:
        raise PermissionError("You are not allowed to upload files to this room.")

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


def load_chat_messages(source: str | Path | TextIO = sys.stdin) -> list[ChatMessage]:
    """Parse chat messages from a file path or file-like object.

    Args:
        source: Path to input file, Path object, or file-like object (defaults to stdin)

    Returns:
        List of ChatMessage records
    """
    # Handle file-like objects directly
    if hasattr(source, 'read'):
        return [
            ChatMessage(
                content=msg['content'],
                user=msg.get('user')
            )
            for msg in lines_to_messages(source)
        ]

    # Handle path inputs
    path = Path(source) if isinstance(source, str) else source
    if not path.exists():
        return []

    with path.open('r', encoding='utf-8') as f:
        return load_chat_messages(f)


def save_chat_messages(
    messages: list[ChatMessage],
    destination: str | Path | TextIO = sys.stdout,
    mode: str = 'a'
) -> None:
    """Write chat messages to a file path or file-like object.

    Args:
        messages: List of ChatMessage objects to write
        destination: Output file path, Path object, or file-like object (defaults to stdout)
        mode: File open mode when writing to a path, defaults to 'a' for append
    """
    # Handle file-like objects directly
    if hasattr(destination, 'write'):
        for msg in messages:
            destination.write(chat_message_to_text(msg) + '\n')
        return

    # Handle path inputs
    path = Path(destination) if isinstance(destination, str) else destination
    with path.open(mode, encoding='utf-8') as f:
        save_chat_messages(messages, f)


def process_chat(messages: list[ChatMessage], process_fn: callable) -> list[ChatMessage]:
    """Process chat messages using the provided function.

    Args:
        messages: List of ChatMessage objects to process
        process_fn: Function that takes a ChatMessage and returns a processed ChatMessage or None

    Returns:
        List of processed ChatMessage objects, excluding any that were filtered out
    """
    processed_messages = []

    for msg in messages:
        result = process_fn(msg)
        if result is not None:
            processed_messages.append(result)

    return processed_messages


def filter_stars(message: ChatMessage) -> ChatMessage | None:
    """
    Process a message by:
    1. Removing text between * and * (shortest matches) including delimiters
    2. Removing lines that begin or end with *
    3. Testing if remainder is just whitespace - if so, skip message

    Args:
        message: ChatMessage to process

    Returns:
        Original message if content remains after filtering, None if only whitespace remains
    """
    # Make a working copy of the content
    content = message.content

    # 1. Remove text between * and * (non-greedy match)
    content = re.sub(r'\*.*?\*', '', content)

    # 2. Remove lines that begin or end with *
    lines = content.split('\n')
    lines = [line for line in lines if not (line.strip().startswith('*') or line.strip().endswith('*'))]
    content = '\n'.join(lines)

    # 3. Check if only whitespace remains
    if not content.strip():
        return None

    # If we get here, there's non-whitespace content, so return original message
    return message


def filter_stars_prob(message: ChatMessage, prob: float = 0.5) -> ChatMessage | None:
    """
    Remove a certain proportion of stars / emotions / actions text from the message.
    If nothing is left, return None.

    Args:
        message: ChatMessage to process
        prob: Probability (0.0 to 1.0) of applying the filter to each starred section

    Returns:
        Processed message or None if only whitespace remains
    """
    if prob <= 0.0:
        return message

    # Make a working copy of the content
    content = message.content

    # 1. Fix malformed lines that begin or end with * but not both, by adding the missing *
    lines = content.split('\n')
    lines_out = []
    for line in lines:
        if line.strip().startswith('*') and not line.strip().endswith('*'):
            line += '*'
        if line.strip().endswith('*') and not line.strip().startswith('*'):
            line = '*' + line
        lines_out.append(line)
    content = '\n'.join(lines_out)

    # 2. Remove random selection of text between * and * (non-greedy match)
    def random_replace(match):
        return '' if random.random() < prob else match.group(0)

    content = re.sub(r'\*.*?\*', random_replace, content)

    # 3. squeeze whitespace and strip, preserving the format
    content = re.sub(r'\s*\n\n+\s*', '\n\n', content)
    content = re.sub(r' +', ' ', content)
    content = content.strip()

    # 4. Check if anything remains
    if not content:
        return None

    # Create new message with filtered content
    return ChatMessage(
        user=message.user,
        content=content,
    )


def process_chat_cli(code: str|None = None, func: str|None = None):
    """Read a chat file from stdin, process it with a Python expression from the CLI, and write the result to stdout."""
    messages = load_chat_messages()
    if func:
        globals()["process_fn"] = globals()[func]
    else:
        code = code.replace("\n", "\n    ")
        code = f"""
import re
def process_fn(msg):
    u = msg.user
    c = msg.content
    {code}
    if not c:
        return None
    return ChatMessage(u, c)
"""
        exec(code, globals())

    processed_messages = process_chat(messages, process_fn)
    save_chat_messages(processed_messages)


def check_access(user: str, pathname: str, path: Path) -> bool:
    """Check if the user has access to the path"""
    # TODO make this a method of the Room class
    # user has access to the top-level dir, all files at the top-level
    # their own directory (/username/), and all files in their own directory (/username/*)
    # TODO detailed access control via files for exceptions

    user = user.lower()

    logger.warning("check_access: User: %s, Path: %s", user, pathname)

    # Check if the path exists
    if not path.exists():
        return Access.NONE

    # Allowed agents have access to everything
    if user in ALLOWED_AGENTS:
        return Access.READ_WRITE

    # Admins have access to everything
    if user in ADMINS:
        return Access.ADMIN

    # Moderators have moderation on the root
    if user in MODERATORS and pathname == "":
        return Access.MODERATE_READ_WRITE

    # Users have access to the root
    if pathname == "":
        return Access.READ

    # Users have admin on their own directory, and files in their own directory
    if pathname == user or pathname.startswith(user + "/"):
        return Access.ADMIN

    stats = path.stat()

    is_file = stats.st_mode & S_IFREG

    # Moderators have moderation on all files in the root
    if user in MODERATORS and not "/" in pathname and is_file:
        return Access.MODERATE_READ_WRITE

    # Users have access to files in the root, check is a file
    if not "/" in pathname and is_file:
        return Access.READ_WRITE

    mode = stats.st_mode

    access = 0

    # Users have access to other-readable entries anywhere
    if mode & S_IROTH:
        access |= Access.READ.value
    if mode & S_IWOTH:
        access |= Access.WRITE.value

    # TODO Users have access to group-readable entries if they are marked as a friend

    return Access(access)


if __name__ == "__main__":
    argh.dispatch_command(process_chat_cli)
