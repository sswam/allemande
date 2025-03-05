#!/usr/bin/env python3-allemande

""" Allemande chat file format library """

import os
import sys
import html
from pathlib import Path
import re
import regex
import logging
from typing import Any, TextIO
from dataclasses import dataclass
import shutil
import subprocess
import random
import enum
from stat import S_IFREG, S_IROTH, S_IWOTH
import asyncio
import copy
import io
import yaml

import argh
import markdown
from starlette.exceptions import HTTPException
import aiofiles
from deepmerge import always_merger

import video_compatible
from ally.cache import cache


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


Agent = dict[str, Any]


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


def name_to_path(name):
    """Convert a filename to a path."""
    name = sanitize_pathname(name)
    assert isinstance(name, str)
    assert not name.startswith("/")
    assert not name.endswith("/")
    return Path(ROOMS_DIR) / name


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
            self.name = name
            self.path = name_to_path(name + EXTENSION)
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

    def exists(self):
        """Check if a room exists."""
        return self.path.exists()

    def write(self, user, content):
        """
        Write a message to a room.
        We don't convert to HTML here, a follower process does that.
        """
        access = check_access(user, self.name, self.path).value
        if not access & Access.WRITE.value:
            raise PermissionError("You are not allowed to post to this room.")

        # support narration by moderators
        if content.startswith("--") and access & Access.MODERATE.value:
            user = None
            content = content[2:]

        content = "\n".join(line.rstrip() for line in content.rstrip().splitlines())

        if content == "":
            # touch the markdown_file, to poke some attention
            self.touch()
            return

        if user and (user == user.lower() or user == user.upper()):
            user_tc = user.title()
        else:
            user_tc = user
        if user:
            user_tc = user_tc.replace(".", "_")
        message = {"user": user_tc, "content": content}

        text = message_to_text(message) + "\n"

        self.append(text)

    async def clear(self, user, op="clear", backup=True):
        """Clear a room."""
        access = check_access(user, self.name, self.path)
        if not self.path.exists():
            return
        if not self.path.is_file():
            raise FileNotFoundError("Room not found.")
        empty = self.path.stat().st_size == 0

        # A double clear will erase the file
        if empty:
            self.path.unlink()
            return

        if op == "archive":
            if not access.value & Access.MODERATE.value:
                raise PermissionError("You are not allowed to archive this room.")
            # run room-archive script with room name
            # TODO in Python
            subprocess.run(["room-archive", self.name], check=True)
        elif op == "rotate":
            raise NotImplementedError("Room rotation is not implemented yet.")
            # run room-rotate script with room name
            # TODO in Python, archive half, keep half. Media?
            # subprocess.run(["room-rotate", self.name], check=True)
        elif op == "clear":
            if not access.value & Access.ADMIN.value:
                raise PermissionError("You are not allowed to clear this room.")
            if backup:
                backup_file(str(self.path))
            # If there is a template file, copy it to the room
            # e.g. foo.bb => foo.bb.template
            # else, truncate the file
            template_file = self.path.with_suffix(".bb.template")
            if template_file.exists():
                shutil.copy(template_file, self.path)
            else:
                self.path.write_text("")
        elif op == "clean":
            await self.clean(user)

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

    async def clean(self, user, backup=True):
        """Clean up the room, removing specialist messages"""
        access = check_access(user, self.name, self.path)
        if not access.value & Access.MODERATE.value:
            raise PermissionError("You are not allowed to clean this room.")
        messages = load_chat_messages(self.path)
        # TODO don't hard-code the agent names!!!
        # TODO it would be better to do this as a view
        exclude = ["Illu", "Pixi", "Atla", "Chaz", "Brie", "Morf", "Pliny", "Sia", "Sio", "Summar", "Summi"]
        narrators = ["Nova", "Illy", "Yoni", "Poni", "Coni", "Boni", "Bigi", "Pigi"]

        messages = [msg for msg in messages if msg.user not in exclude]

        # remove player messages that start with invoking a specialist
        specialists = set(exclude + narrators)
        name_pattern = re.compile(f'^({"|".join(map(re.escape, specialists))})(,|$)')
        messages = [msg for msg in messages if not name_pattern.match(msg.content)]

        # convert narrator messages to narrative
        for msg in messages:
            if msg.user in narrators:
                msg.user = None

        output = io.StringIO()
        save_chat_messages(messages, output, mode="w")
        await overwrite_file(user, self.name + EXTENSION, output.getvalue(), backup=backup)

    def check_access(self, user: str) -> Access:
        """Check access for a user."""
        return check_access(user, self.name, self.path)

    def find_resource_file(self, ext, name=None, create=False):
        """Find a resource file for the chat room."""
        parent = self.path.parent
        stem = self.path.stem
        resource = parent / (stem + "." + ext)
        if not resource.exists():
            stem_no_num = re.sub(r"-\d+$", "", stem)
            if stem_no_num != stem:
                resource = parent / (stem_no_num + "." + ext)
        if not resource.exists():
            resource = parent / (name + "." + ext)
        if not resource.exists() and not create:
            resource = None
        return str(resource) if resource else None

    def find_agent_resource_file(self, ext, agent_name=None):
        """Find a resource file for the agent and chat room."""
        parent = self.path.parent
        stem = self.path.stem
        resource = parent / (stem + "." + agent_name + "." + ext)
        if not resource.exists():
            stem_no_num = re.sub(r"-\d+$", "", stem)
            if stem_no_num != stem:
                resource = parent / (stem_no_num + "." + agent_name + "." + ext)
        if not resource.exists():
            resource = parent / (agent_name + "." + ext)
        if not resource.exists():
            resource = None
        return str(resource) if resource else None

    def get_options(self, user) -> dict:
        """Get the options for a room."""
        access = check_access(user, self.name, self.path)
        if not access.value & Access.READ.value:
            raise PermissionError("You are not allowed to get options for this room.")
        options_file = self.find_resource_file("yml", "options")
        if options_file:
            options = cache.load(options_file)
        else:
            options = {}
        return options

    def set_options(self, user, options):
        """Set the options for a room."""
        access = check_access(user, self.name, self.path)
        if not access.value & Access.MODERATE.value:
            raise PermissionError("You are not allowed to set options for this room.")
        options_file = self.find_resource_file("yml", "options", create=True)
        if options_file:
            old_options = cache.load(options_file)
            logger.debug("old options: %r", old_options)
            new_options = always_merger.merge(old_options, options)
            new_options = tree_prune(new_options)
            logger.debug("new options: %r", new_options)
            cache.save(options_file, new_options)
        else:
            raise FileNotFoundError("Options file not found.")

def tree_prune(tree: dict) -> dict:
    """Prune a tree in-place, removing None values."""
    for key, value in list(tree.items()):
        if value is None:
            del tree[key]
        elif isinstance(value, dict):
            tree_prune(value)
    return tree


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


def quote_inline_math(pre, d1, math, d2, post):
    """Process potential inline math delimited by matching delimiters, wrapping math content in $`...`$"""
    logger.debug("quote_inline_math")
    logger.debug("  pre:  %r", pre)
    logger.debug("  d1:   %r", d1)
    logger.debug("  math: %r", math)
    logger.debug("  d2:   %r", d2)
    logger.debug("  post: %r", post)
    # check if it looks like math...
    has_math = False
    is_math = True
    if math.startswith("`") and math.endswith("`"):
        # already processed
        logger.warning("already processed: %r", math)
        has_math = True
        is_math = False
    elif d1 == r"\(" and d2 == r"\)":
        pass
    elif d1 == r"\[" and d2 == r"\]":
        pass
    elif re.match(r"^\w", post):
        is_math = False
    elif re.match(r"\w$", pre):
        is_math = False
    if is_math:
        has_math = True
        math = fix_math_escape_percentages(math)
        return f"$`{math}`$", has_math
    return f"{d1}{math}{d2}", has_math


def fix_math_escape_percentages(math_content):
    """Escape unescaped % symbols in math content"""
    # FIXME: This approach assumes that a % symbol immediately preceded by a
    # backslash is already escaped. This is not always the case.
    return re.sub(r"(?<!\\)%", r"\%", math_content)


def find_and_fix_inline_math_part(part: str) -> str:
    """Find and fix inline math in a part of a line, without quoted code."""
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
                    (.+?)  # Group 3: Math content
                    \$\$
                ) |
                (          # Group 4: Inline math with $...$
                    \$     
                    (.+?)  # Group 5: Math content
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
                )
            )
            (.*)           # Group 10: Any remaining characters
            $
            """,
            part[start:],
            re.VERBOSE
        )
        if match is None:
            part = part[:start] + html.escape(part[start:], quote=False)
            break
        groups = match.groups()
        pre, post = groups[0], groups[10]
        if groups[2]:
            d1, math, d2 = "$$", groups[3], "$$"
        elif groups[4]:
            d1, math, d2 = "$", groups[5], "$"
        elif groups[6]:
            d1, math, d2 = r"\[", groups[7], r"\]"
        elif groups[8]:
            d1, math, d2 = r"\(", groups[9], r"\)"
        else:
            raise ValueError("No math group matched")
        replaced, has_math1 = quote_inline_math(pre, d1, math, d2, post)
        has_math = has_math or has_math1
        pre = html.escape(pre, quote=False)
        part = part[:start] + pre + replaced + post
        start += len(pre) + len(replaced)

    return part, has_math


def find_and_fix_inline_math(line: str) -> str:
    """Find and fix inline math in a line."""
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
            re.VERBOSE
        )
        if not match:
            break
        found = match.group(1)
        if found.startswith("`"):
            start += len(found)
            continue

        # 2. find inline math, and replace with $`...`$

        fixed, has_math1 = find_and_fix_inline_math_part(found)
        has_math = has_math or has_math1

        # 3. replace the fixed part in the line
        line = line[:start] + fixed + line[start + len(found):]
        start += len(fixed)

    return line, has_math


def preprocess(content):
    """Preprocess chat message content, for markdown-katex"""

    # replace $foo$ with $`foo`$
    # replace $$\n...\n$$ with ```math\n...\n```

    has_math = False

    out = []

    # make sure <think> tags are on their own lines...
    content = re.sub(r"\s*(</?think(ing)?>)\s*", r"\n\1\n", content, flags=re.DOTALL)

    in_math = False
    in_code = 0
    in_script = False
    was_blank = False
    for line in content.splitlines():
        is_html = False
        was_code = bool(in_code)
        # if first and re.search(r"\t<", line[0]):
        #     is_html = True
        if not in_code and re.search(
            r"</?(html|base|head|link|meta|style|title|body|address|article|aside|footer|header|h1|h2|h3|h4|h5|h6|hgroup|main|nav|section|blockquote|dd|div|dl|dt|figcaption|figure|hr|li|main|ol|p|pre|ul|a|abbr|b|bdi|bdo|br|cite|code|data|dfn|em|i|kbd|mark|q|rb|rp|rt|rtc|ruby|s|samp|small|span|strong|sub|sup|time|u|var|wbr|area|audio|img|map|track|video|embed|iframe|object|param|picture|source|canvas|noscript|script|del|ins|caption|col|colgroup|table|tbody|td|tfoot|th|thead|tr|button|datalist|fieldset|form|input|label|legend|meter|optgroup|option|output|progress|select|textarea|details|dialog|menu|summary|slot|template|acronym|applet|basefont|bgsound|big|blink|center|command|content|dir|element|font|frame|frameset|image|isindex|keygen|listing|marquee|menuitem|multicol|nextid|nobr|noembed|noframes|plaintext|shadow|spacer|strike|tt|xmp)\b",
            line,
        ):
            is_html = True
        is_markdown_image = re.search(r"!\[.*\]\(.*\)", line)
        logger.debug("check line: %r", line)
        is_math_start = re.match(r"\s*(\$\$|```tex|```math)$", line)
        is_math_end = re.match(r"\s*(\$\$|```)$", line)
        if re.match(r"""^\s*<script( type=["']?text/javascript["']?)?>$""", line) and not in_code:
            out.append(line)
            in_code = 1
            in_script = True
        elif re.match(r"^\s*</script>$", line) and in_script:
            out.append(line)
            in_code = 0
            in_script = False
        elif is_html or is_markdown_image:
            out.append(line)
        elif is_math_start and not in_code:
            out.append("```math")
            in_math = True
            has_math = True
            in_code += 1
        elif is_math_end and in_math:
            out.append("```")
            in_math = False
            in_code = 0
        elif in_math:
            line = fix_math_escape_percentages(line)
            out.append(line)
        elif re.match(r"\s*```", line) and not in_code:
            if not was_blank:
                out.append("")
            out.append(line)
            in_code = 1
        elif re.match(r"\s*```\w", line) and not in_script:
            if not was_blank:
                out.append("")
            out.append(line)
            in_code += 1
        elif re.match(r"\s*```", line) and in_code:
            out.append(line)
            in_code -= 1
        elif in_code:
            out.append(line)
        elif re.match(r"^\s*<think(ing)?>$", line):
            out.append(r"""<details markdown="1" class="think"><summary>thinking</summary>""")
        elif re.match(r"^\s*</think(ing)?>$", line):
            out.append(r"""</details>""")
        else:
            line, has_math1 = find_and_fix_inline_math(line)
            has_math = has_math or has_math1
            out.append(line)

    out = add_blanks_after_code_blocks(out)

    content = "\n".join(out) + "\n"
    logger.info("preprocess content: %s", content)
    return content, has_math


def add_blanks_after_code_blocks(lines: list[str]) -> list[str]:
    out = []
    in_code_block = False
    code_block_indent = 0

    for i, line in enumerate(lines):
        out.append(line)

        stripped = line.strip()
        if not stripped:
            continue

        indent = len(line) - len(line.lstrip())

        if stripped == '```' and in_code_block:
            if indent <= code_block_indent:  # Close block if at same or less indent
                in_code_block = False
                # Add blank line if:
                # 1. Next line exists and isn't blank
                # 2. Next line isn't another code block
                # 3. Next line isn't less indented
                if (i + 1 < len(lines) and
                    lines[i + 1].strip() and
                    not lines[i + 1].strip().startswith('```') and
                    len(lines[i + 1]) - len(lines[i + 1].lstrip()) <= indent):
                    out.append('')

        elif stripped.startswith('```') and not in_code_block:
            in_code_block = True
            code_block_indent = indent

    return out


math_cache: dict[str, str] = {}


SPACE_MARKER = "§S§"
TAB_MARKER = "§T§"


def escape_indents(text):
    """Escape leading whitespace in each line."""
    global SPACE_MARKER, TAB_MARKER
    while SPACE_MARKER in text or TAB_MARKER in text:
        r = random.randint(0, 999999)
        SPACE_MARKER = f"§S{r}§"
        TAB_MARKER = f"§T{r}§"

    lines = text.splitlines()
    processed_lines = []

    for line in lines:
        # Match leading whitespace
        indent_match = re.match(r'^(\s+)', line)
        if indent_match:
            indent = indent_match.group(1)
            # Replace spaces and tabs with markers
            escaped_indent = indent.replace(' ', SPACE_MARKER).replace('\t', TAB_MARKER)
            # Replace the original indent with the escaped version
            processed_line = escaped_indent + line[len(indent):]
        else:
            processed_line = line
        processed_lines.append(processed_line)

    return '\n'.join(processed_lines)


def restore_indents(text):
    """Restore leading whitespace in each line."""
    text = text.replace(SPACE_MARKER, ' ')
    text = text.replace(TAB_MARKER, '\t')
    return text


def message_to_html(message):
    """Convert a chat message to HTML."""
    global math_cache
    logger.debug("converting message to html: %r", message["content"])
    content, has_math = preprocess(message["content"])
    if content in math_cache:
        html_content = math_cache[content]
    else:
        try:
            logger.debug("markdown content: %r", content)
            # content = escape_indents(content)
            html_content = markdown.markdown(content, extensions=MARKDOWN_EXTENSIONS, extension_configs=MARKDOWN_EXTENSION_CONFIGS)
            # html_content = restore_indents(html_content)
            logger.debug("html content: %r", html_content)
            html_content = disenfuckulate_nested_code_blocks(html_content)
#            html_content = "\n".join(wrap_indent(line) for line in html_content.splitlines())
#             html_content = html_content.replace("<br />", "")
#             html_content = html_content.replace("<p>", "")
#             html_content = html_content.replace("</p>", "\n")
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
        return f"""<div class="message" user="{user_ee}"><div class="label">{user_ee}:</div><div class="content">{html_content}</div></div>\n\n"""
    return f"""<div class="narrative"><div class="content">{html_content}</div></div>\n\n"""


LANGUAGES = r'python|bash|sh|shell|console|html|xml|css|javascript|js|json|yaml|yml|toml|ini|sql|c|cpp|csharp|cs|java|kotlin|swift|php|perl|ruby|lua|rust|go|dart|scala|groovy|powershell|plaintext'


def disenfuckulate_nested_code_blocks(html: str) -> str:
    """Fix nested code blocks in HTML."""
    def replace_nested_code_block(match):
        class_attr = f' class="language-{match.group(1)}"' if match.group(1) else ""
        return f"<pre><code{class_attr}>{match.group(2)}</code></pre>"
    return re.sub(rf'<p><code>((?:{LANGUAGES})\n)?(.*?)</code></p>', replace_nested_code_block, html, flags=re.DOTALL)


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


async def upload_file(room_name, user, filename, file=None, alt=None, to_text=False):
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

    # convert to text if wanted
    try:
        if to_text and medium in ("audio", "video"):
            alt = await speech_to_text.convert_audio_video_to_text(file_path, medium)
        elif to_text and medium == "image":
            alt = await image_to_text.convert_image_to_text(file_path)
    except Exception as e:
        logger.error("Error converting to text: %r, %r, %r", medium, file_path, e)

    # alt text
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


def chat_read(file, args) -> list[str]:
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

    # Handle path outputs
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


def load_config(path: Path, filename: str) -> dict[str, Any]:
    """Load YAML configuration from files."""
    # list of folders from path up to ROOMS_DIR
    folders = list(path.relative_to(ROOMS_DIR).parents)
    # Go top-down from ROOMS_DIR to the folder containing the file
    config_all = {}
    for folder in reversed(folders):
        config_path = ROOMS_DIR / folder / filename
        if not config_path.exists():
            continue
        with config_path.open("r", encoding="utf-8") as f:
            config = cache.load(config_path)
            if config.get("reset"):
                config_all = config
            else:
                # We only merge at the top level
                config_all.update(config)
    return config_all


def write_agents_list(agents):
    """Write the list of agents to a file."""
    agent_names = list(agents.keys())
    path = Path(os.environ["ALLEMANDE_ROOMS"]) / "agents.yml"
    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(agent_names, f)


def read_agents_list() -> list[str]:
    """Read the list of agents from a file."""
    path = Path(os.environ["ALLEMANDE_ROOMS"]) / "agents.yml"
    if not path.exists():
        return []
    agent_names = cache.load(path)
    if not isinstance(agent_names, list):
        raise ValueError("Invalid agents list")
    agent_names = [name.lower() for name in agent_names]
    return agent_names


def check_access(user: str, pathname: str, path: Path) -> Access:
    """Check if the user has access to the path, and log the access."""
    access, reason = _check_access_2(user, pathname, path)
    logger.debug("check_access: User: %s, pathname: %s, Path: %s, Access: %s, Reason: %s", user, pathname, path, access, reason)
    return access


def _check_access_2(user: str, pathname: str, path: Path) -> Access:
    """Check if the user has access to the path"""
    # TODO make a wrapper method in the room class
    # user has access to the top-level dir, all files at the top-level
    # their own directory (/username/), and all files in their own directory (/username/*)
    # TODO detailed access control via files for exceptions

    # TODO What's the difference between a moderator and an admin?
    #      Do we need both?

    access = load_config(path, "access.yml")
    agent_names = read_agents_list()

    user = user.lower()

    logger.debug("check_access: User: %s, pathname: %s, Path: %s", user, pathname, path)

    # Admins have access to everything
    if user in ADMINS:
        return Access.ADMIN, "admin"

    # Moderators have moderation on the root
    if user in MODERATORS and pathname == "":
        return Access.MODERATE_READ_WRITE, "moderator"

    # Users have admin on their own directory, and files in their own directory
    if re.match(rf"{user}\.[a-z]+$", pathname, flags=re.IGNORECASE) or pathname == user or pathname.startswith(user + "/"):
        return Access.ADMIN, "user_dir"

    # Users have admin on their top-level room, or a file with their name and any extension
    if re.match(rf"{user}\.[a-z]+$", pathname, flags=re.IGNORECASE):
        return Access.ADMIN, "user_top"


    exists = True
    try:
        stats = path.stat()
    except FileNotFoundError:
        exists = False

    is_file = not exists or stats.st_mode & S_IFREG


    # Moderators have moderation on all files in the root
    if user in MODERATORS and not "/" in pathname and is_file:
        return Access.MODERATE_READ_WRITE, "moderator_top"


    # Denied users have no access
    if user in access.get("deny", []):
        return Access.NONE, "deny"

    # Allowed users have access
    logger.debug("access: %s", access)
    if user in access.get("allow", []):
        return Access.READ_WRITE, "allow"

    # Agents have access if allowed
    if access.get("allow_agents") and user in agent_names:
        return Access.READ_WRITE, "allow_agents"

    # Users have access to the root
    if pathname == "":
        return Access.READ, "root"

    # Users have access to files in the root, check is a file
    if not "/" in pathname and is_file:
        return Access.READ_WRITE, "user_root_file"

    # TODO guests can create new files in a shared folder?

    # Check if the path exists
    if not path.exists():
        return Access.NONE, "not_found"

    mode = stats.st_mode

    access = Access.NONE.value

    # Users have access to shared other-readable entries anywhere
    if mode & S_IROTH:
        access |= Access.READ.value
    if mode & S_IWOTH:
        access |= Access.WRITE.value

    # TODO Users have access to group-readable entries if they are marked as a friend

    return Access(access), "shared_public"


def backup_file(path: str):
    """Backup a file using git.

    Args:
        path: Path to the file to backup (can be relative or absolute)

    Raises:
        subprocess.CalledProcessError: If git commands fail
        ValueError: If the file is not in a git repository
    """
    # Convert to absolute path
    abs_path = os.path.abspath(path)

    if not os.path.exists(abs_path):
        return

    logger.warning("backup_file: %s", path)
    logger.warning("  abs_path: %s", abs_path)

    # Find the git repo root directory
    try:
        repo_root = subprocess.check_output(
            ["git", "rev-parse", "--show-toplevel"],
            cwd=os.path.dirname(abs_path),
            text=True
        ).strip()
    except subprocess.CalledProcessError:
        raise ValueError(f"File {path} is not in a git repository")

    logger.warning("  repo_root: %s", repo_root)

    # Get path relative to repo root
    rel_path = os.path.relpath(abs_path, repo_root)

    logger.warning("  rel_path: %s", rel_path)

    # Run git commands from repo root
    try:
        subprocess.run(["git", "add", rel_path], check=True, cwd=repo_root)
        subprocess.run(["git", "commit", "-m", f"Backup {rel_path}"], check=True, cwd=repo_root)
    except subprocess.CalledProcessError as e:
        # This can happen if there are no changes to commit
        logger.error("git error: %s", e)


async def overwrite_file(user, file, content, backup=True, delay=0.2, noclobber=False):
    """Overwrite a file with new content."""
    logger.warning("overwrite_file: %s", file)
    path = str(name_to_path(file))
    logger.warning("  path: %s", path)
    if not check_access(user, file, Path(path)).value & Access.WRITE.value:
        logger.warning("  user: %s", user)
        logger.warning("  access: %s", check_access(user, file, Path(path)))
        raise PermissionError("You are not allowed to overwrite this file.")
    exists = Path(path).exists()
    if exists and Path(path).is_dir():
        raise ValueError("Cannot overwrite a directory.")
    if exists and noclobber:
        raise ValueError("File already exists, will not overwrite.")
    if backup:
        backup_file(path)
    if path.endswith(".bb"):
        html_path = path[:-3] + ".html"
        logger.warning("  html_file: %s", html_path)
        if Path(html_path).exists():
            # We unlink the HTML file to trigger a full rebuild of the HTML
            os.unlink(html_path)
        # We unlink the .bb file before writing, to avoid triggering an AI response to an edit
        try:
            os.unlink(path)
        except FileNotFoundError:
            pass
        if delay:
            await asyncio.sleep(delay)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def remove_thinking_sections(content: str, agent: Agent|None, n_own_messages: int) -> tuple[str, int]:
    remember_thoughts = agent.get("remember_thoughts", 0) if agent else 0
    if agent:
        logger.debug("Agent name %s, remember_thoughts %s, n_own_messages %s", agent["name"], remember_thoughts, n_own_messages)
    agent_name = agent["name"] if agent else None
    replace = ""
    if agent_name and content.startswith(agent_name + ":\t"):
        n_own_messages += 1
        if n_own_messages <= remember_thoughts:
            logger.debug("Remembering agent's thoughts: %s", content)
            return content, n_own_messages
#        replace = "<think>\nI was thinking something ...\n</think>"
        replace = ""
    modified = re.sub(
        r"""
        <think(ing)?>
        (.*?)
        (</think(ing)?>|\Z)
        """,
        replace,
        content,
        flags=re.MULTILINE|re.IGNORECASE|re.VERBOSE|re.DOTALL
    )
    if modified != content:
        logger.debug("Removed 'thinking' section/s from message: original: %s", content)
        logger.debug("  modified: %s", modified)
        return modified, n_own_messages
    logger.debug("No 'thinking' section/s found in message: %s", content)
    return content, n_own_messages


def context_remove_thinking_sections(context: list[str], agent: Agent|None) -> list[str]:
    """Remove "thinking" sections from the context."""
    # Remove any "thinking" sections from the context
    # A "thinking" section is a <think> block

    n = len(context)
    n_own_messages = 0
    for i in range(n - 1, -1, -1):
        context[i], n_own_messages = remove_thinking_sections(context[i], agent, n_own_messages)

    return context

def history_remove_thinking_sections(history: list[dict[str,Any]], agent: Agent|None):
    """Remove "thinking" sections from the history."""
    # Remove any "thinking" sections from the context
    # A "thinking" section is a <think> block

    history = copy.deepcopy(history)

    n = len(history)
    n_own_messages = 0
    for i in range(n - 1, -1, -1):
        message = history[i]
        message["content"], n_own_messages = remove_thinking_sections(message["content"], agent, n_own_messages)

    return history


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


def clean_prompt(context, name, delim):
    """Clean the prompt for image gen agents and tools."""

    logger.debug("clean_prompt: before: %s", context)

    agent_name_esc = regex.escape(name)

    # Remove one initial tab from each line in the context
    context = [regex.sub(r"(?m)^\t", "", line) for line in context]

    # Join all lines in context with the specified delimiter
    text = delim.join(context)

    logger.debug("clean_prompt: 1: %s", text)

    # Remove up to the first occurrence of the agent's name (case insensitive) and any following punctuation, with triple backticks
    text1 = regex.sub(r".*?```\w*\s*" + agent_name_esc + r"\b[,;.!:]*(.*?)```.*", r"\1", text, flags=regex.DOTALL | regex.IGNORECASE, count=1)

    logger.debug("clean_prompt: 2: %s", text1)

    # Remove up to the first occurrence of the agent's name (case insensitive) and any following punctuation, with single backticks
    if text1 == text:
        text1 = regex.sub(r".*?`\s*" + agent_name_esc + r"\b[,;.!:]*(.*?)`.*", r"\1", text, flags=regex.DOTALL | regex.IGNORECASE, count=1)

    logger.debug("clean_prompt: 3: %s", text1)

    # Remove up to the last occurrence of the agent's name (case insensitive) and any following punctuation
    if text1 == text:
        text1 = regex.sub(r".*\b" + agent_name_esc + r"\b[,;.!:]*", r"", text, flags=regex.DOTALL | regex.IGNORECASE, count=1)

        # Remove anything after a blank line in this case
        text1 = re.sub(r"\n\n.*", r"", text1, flags=re.DOTALL)

    logger.debug("clean_prompt: 4: %s", text1)

#     # Remove the last pair of triple backticks and keep only the content between them
#     text = re.sub(r".*```(.*?)```.*", r"\1", text, flags=re.DOTALL, count=1)

#     # Try single backticks too
#     text = re.sub(r".*`(.*?)`.*", r"\1", text, flags=re.DOTALL, count=1)

    text = text1

    # Remove leading and trailing whitespace
    text = text.strip()

    logger.debug("clean_prompt: after: %s", text)
    return text


def set_user_theme(user, theme):
    """Set the user's theme."""
    if sanitize_filename(theme) != theme:
        raise ValueError("Invalid theme name.")
    path = Path(os.environ["ALLEMANDE_USERS"]) / user / "theme.css"
    source = "../../static/themes/" + theme + ".css"
    if not (Path(os.environ["ALLEMANDE_USERS"]) / user / source).exists:
        raise ValueError("Theme not found.")
    path.parent.mkdir(parents=True, exist_ok=True)
    cache.chmod(path.parent, 0o755)
    cache.symlink(source, path)


if __name__ == "__main__":
    argh.dispatch_command(process_chat_cli)
