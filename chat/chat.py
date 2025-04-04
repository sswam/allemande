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
from stat import S_IFMT, S_IFREG, S_IROTH, S_IWOTH, S_IFLNK
import asyncio
import copy
import io
import yaml
from urllib.parse import urlparse
import fetch

import argh
import markdown
from starlette.exceptions import HTTPException
import aiofiles
from deepmerge import always_merger
from bs4 import BeautifulSoup
from markdown_it import MarkdownIt
from mdformat.renderer import MDRenderer
import mdformat_light_touch

import video_compatible
from ally.cache import cache
from ally.quote import quote_words


os.umask(0o007)


EXTENSION = ".bb"
ROOMS_DIR = os.environ["ALLEMANDE_ROOMS"]
ALLYCHAT_SITE = os.environ["ALLYCHAT_SITE"]

ADMINS = os.environ.get("ALLYCHAT_ADMINS", "").split()
MODERATORS = os.environ.get("ALLYCHAT_MODERATORS", "").split()

md = MarkdownIt()
mdformat = MDRenderer()


class Access(enum.Enum):
    """Access levels for a room."""

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
ROOM_PATH_MAX_LENGTH = 1000
ROOM_MAX_DEPTH = 10

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
    "markdown_katex",
    #    "markdown_criticmarkup",
    "attr_list",
]

MARKDOWN_EXTENSION_CONFIGS = {
    "markdown_katex": {
        # 		'no_inline_svg': True, # fix for WeasyPrint
        "insert_fonts_css": True,
    },
    "pymdownx.highlight": {
        "use_pygments": False,
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

        # TODO can a disallowed user create directories in this way?
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
        access = self.check_access(user).value
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
        access = self.check_access(user).value
        #         if not self.path.exists():
        #             return
        if self.path.exists() and not self.path.is_file():
            raise FileNotFoundError("Room not found.")
        #        empty = self.path.stat().st_size == 0

        if op == "archive":
            if not access & Access.MODERATE.value:
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
            if not access & Access.ADMIN.value:
                raise PermissionError("You are not allowed to clear this room.")
            if backup:
                backup_file(str(self.path))
            # If there is a base file, copy it to the room
            # e.g. foo.bb => foo.bb.base
            # else, truncate the file
            template_file = self.path.with_suffix(".bb.base")
            if template_file.exists():
                shutil.copy(template_file, self.path)
            else:
                # self.path.write_text("")
                self.path.unlink()
        elif op == "clean":
            await self.clean(user)

    def undo(self, user, n=1, backup=True):
        """Remove the last n messages from a room."""
        # Messages are delimited by blank lines, and the file should end with a blank line.
        if n <= 0:
            return

        access = self.check_access(user).value
        if n > 1 and not access & Access.ADMIN.value:
            raise PermissionError("You are not allowed to undo multiple messages in this room.")

        if not access & Access.MODERATE.value:
            raise PermissionError("You are not allowed to undo messages in this room.")

        count_bytes = 0
        for line in tac(self.path, binary=True, keepends=True):
            if line == b"\n":
                n -= 1
            if n < 0:
                break
            count_bytes += len(line)

        if backup:
            self.backup()

        with open(self.path, "a+b") as f:
            logger.debug("undo truncating file %s", self.path)
            logger.debug("undo truncate %d bytes", count_bytes)
            logger.debug("current file size: %d", f.tell())
            f.truncate(f.tell() - count_bytes)

    def backup(self):
        """Backup a room."""
        backup_file(str(self.path))

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
        access = self.check_access(user).value
        if not access & Access.MODERATE.value:
            raise PermissionError("You are not allowed to clean this room.")
        messages = load_chat_messages(self.path)
        # TODO don't hard-code the agent names!!!
        # TODO it would be better to do this as a view
        exclude = ["Illu", "Pixi", "Atla", "Chaz", "Brie", "Morf", "Pliny", "Sia", "Sio", "Summar", "Summi"]
        narrators = ["Nova", "Illy", "Hily", "Yoni", "Poni", "Coni", "Boni", "Bigi", "Pigi", "Dily", "Wili"]

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
        return check_access(user, self.name + EXTENSION)

    def find_resource_file(self, ext, name=None, create=False, try_room_name=True):
        """Find a resource file for the chat room."""
        parent = self.path.parent
        stem = self.path.stem
        resource = None
        if try_room_name:
            resource = parent / (stem + "." + ext)
        if try_room_name and not resource.exists():
            stem_no_num = re.sub(r"-\d+$", "", stem)
            if stem_no_num != stem:
                resource = parent / (stem_no_num + "." + ext)
        if not resource or not resource.exists() and name:
            resource = parent / (name + "." + ext)
        if resource and not resource.exists() and not create:
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
        access = self.check_access(user).value
        if not access & Access.READ.value:
            raise PermissionError("You are not allowed to get options for this room.")
        if self.path.is_symlink():
            target = self.path.resolve().relative_to(ROOMS_DIR)
            if target.suffix == EXTENSION:
                target = target.with_suffix("")
            room2 = Room(str(target))
            access = room2.check_access(user).value
            if not access & Access.READ.value:
                raise PermissionError("You are not allowed to get options for this room.")
            return {"redirect": str(target)}
        options_file = self.find_resource_file("yml", "options")
        if options_file:
            options = cache.load(options_file)
        else:
            options = {}
        return options

    def set_options(self, user, new_options):
        """Set the options for a room."""
        access = self.check_access(user).value
        if not access & Access.MODERATE.value:
            raise PermissionError("You are not allowed to set options for this room.")
        options_file = self.find_resource_file("yml", "options", create=True)
        if options_file:
            logger.debug("options file: %s", options_file)
            options = cache.load(options_file) or {}
            logger.debug("old options: %r", options)
            logger.debug("new options: %r", new_options)
            always_merger.merge(options, new_options)  # modifies options
            logger.debug("merged options: %r", options)
            options = tree_prune(options)
            logger.debug("pruned options: %r", options)
            cache.save(options_file, options)
        else:
            raise FileNotFoundError("Options file not found.")

    def get_last_room_number(self, user: str) -> str:
        """Get the last room number."""
        access = check_access(user, str(self.parent)).value
        if not access & Access.READ.value:
            raise PermissionError("You are not allowed to get the last room number.")

        # chop off any number
        name = self.name
        name = re.sub(r"-\d+$", "", name)

        path = name_to_path(name)
        basename = path.name

        # list files in parent
        files = list(path.parent.glob(f"{basename}*{EXTENSION}"))

        # cut off room dir and extension
        files = [f.stem for f in files]

        # only this room and its numbered pages
        files = [f for f in files if f == basename or f.startswith(basename + "-")]

        # cut off room name
        files = [re.sub(rf"^{re.escape(basename)}-?", "", f) or "-1" for f in files]

        # convert to integers
        files = [int(f) for f in files]

        # find the maximum
        last = max(files, default=-1)

        last = "" if last == -1 else str(last)

        return last


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


def safe_join(base_dir: Path | str, *paths: str | Path) -> Path:
    """
    Return a safe path under base_dir, or raise ValueError if the path is unsafe.
    Preserves symlinks and only checks for path traversal attacks.

    Args:
        base_dir: Base directory path
        *paths: Additional path components to join

    Returns:
        Path: Safe joined path

    Raises:
        ValueError: If resulting path would be outside base_dir
    """
    # Convert base_dir to Path if it's a string
    base_dir = Path(base_dir).absolute()

    # Convert all path components to strings and join them
    path_parts = [str(p) for p in paths]

    # Create complete path without resolving
    full_path = base_dir.joinpath(*path_parts)

    # Normalize the path (remove . and .., but don't resolve symlinks)
    normalized_path = Path(os.path.normpath(str(full_path)))
    normalized_base = Path(os.path.normpath(str(base_dir)))

    # Check if the normalized path starts with the normalized base path
    normalized_path_s = str(normalized_path)
    normalized_base_s = str(normalized_base)
    if not (normalized_path_s == normalized_base_s or normalized_path_s.startswith(normalized_base_s + os.sep)):
        raise ValueError(f"Path {full_path} is outside base directory {base_dir}")

    # Make sure they share the same root
    if normalized_path.root != normalized_base.root:
        raise ValueError(f"Path {full_path} is outside base directory {base_dir}")

    return full_path


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

    is_dir = room.endswith("/")
    if is_dir:
        room = room[:-1]

    # split into parts
    parts = room.split("/")

    # sanitize each part
    parts = map(sanitize_filename, parts)

    # remove empty parts
    parts = list(filter(lambda x: x, parts))

    if not parts:
        raise HTTPException(status_code=400, detail="Please enter the name of a room.")

    # Check max depth BEFORE joining
    if len(parts) > ROOM_MAX_DEPTH:
        raise HTTPException(status_code=400, detail=f"The room is too deeply nested, max {ROOM_MAX_DEPTH} parts.")

    # join back together
    room = "/".join(parts)

    if len(room) > ROOM_PATH_MAX_LENGTH:
        raise HTTPException(status_code=400, detail=f"The room name is too long, max {ROOM_PATH_MAX_LENGTH} characters.")

    # check for control characters
    if re.search(r"[\x00-\x1F\x7F]", room):
        raise HTTPException(status_code=400, detail="The room name cannot contain control characters.")

    if is_dir:
        room += "/"

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

    message: dict | None = None

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


def messages_to_lines(messages):
    """Convert chat messages to lines."""
    for message in messages:
        yield message_to_text(message)


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
    elif d1 == r"\(" and d2 == r"\)" and " " not in math:  # hack: avoid triggering on image prompt \(medium\) etc!
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


def find_and_fix_inline_math_part(part: str) -> tuple[str, bool]:
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
            re.VERBOSE,
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


def preprocess_normal_markdown(in_text: str, bb_file: str) -> tuple[str, bool]:
    """Find and fix inline math in markdown, also preprocess links."""
    newlines_before, text, newlines_after = re.match(r"(\n*)(.*?)(\n*)$", in_text, re.DOTALL).groups()

    has_math = False
    tokens = md.parse(text)

    def process_tokens(tokens):
        nonlocal has_math
        for token in tokens:
            if token.children:
                process_tokens(token.children)
            if token.type == 'link_open':
                token.attrs['href'] = fix_link(token.attrs['href'], bb_file)
            elif token.type == 'text':
                fixed_text, has_math_part = find_and_fix_inline_math_part(token.content)
                has_math = has_math or has_math_part
                token.content = fixed_text

    process_tokens(tokens)

    # render back to markdown using mdformat
    options = {
        "number": True,
        "parser_extension": [mdformat_light_touch],
    }
    env = {}
    out_text = mdformat.render(tokens, options, env)

    # This should not be needed now with mdformat_light_touch:
    # replace $\` and \`$ with $` and `$  :(
    # out_text = out_text.replace(r"$\`", "$`").replace(r"\`$", "`$")

    out_text = newlines_before + out_text.strip("\n") + newlines_after

    if out_text != in_text:
        logger.info("preprocess_normal_markdown:\n%s\n%s", in_text, out_text)

    return out_text, has_math


def fix_link(href: str, bb_file: str) -> str:
    """Fix room links"""
    logger.info("fix_link: %r", href)
    # parse the URL
    url = urlparse(href)
    # is it a remote URL?
    if url.scheme or url.netloc:
        return href
    # is the final part a room name (file without an extension?)
    if re.match(r"(^|/)[^\./]+", href):
        try:
            _safe_path, href = safe_path_for_local_file(bb_file, href)
        except ValueError as e:
            logger.warning("Invalid path: %s", e)
            # TODO should we return maybe a javascript warning or something?
            return href
        href = f"""{ALLYCHAT_SITE}/#{href}"""
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
allychat-meta
"""
)

RE_TAGS = re.compile(rf"</?({'|'.join(set(HTML_TAGS + SVG_TAGS + ALLYCHAT_TAGS))})\b", flags=re.IGNORECASE)


async def preprocess(content: str, bb_file: str, user: str|None) -> tuple[str, bool]:
    """Preprocess chat message content, for markdown-katex, and other fixes"""

    # replace $foo$ with $`foo`$
    # replace $$\n...\n$$ with ```math\n...\n```

    has_math = False

    out = []

    # make sure <think> tags are on their own lines...
    content = re.sub(r"^\s*(<think>)\s*", r"\n\1\n", content, flags=re.IGNORECASE|re.MULTILINE)
    content = re.sub(r"\s*(</think>)\s*$", r"\n\1\n", content, flags=re.IGNORECASE|re.MULTILINE)

    in_math = False
    in_code = 0
    in_script = False
    in_svg = False  # we need to avoid line breaks in SVG unfortunately
    was_blank = False

    # accumulate normal lines to process together with process_normal_markdown
    normal_lines = []

    is_normal_line = False

    def do_normal_lines():
        nonlocal normal_lines, has_math
        text = "\n".join(normal_lines) + "\n"
        text, has_math1 = preprocess_normal_markdown(text, bb_file)
        has_math = has_math or has_math1
        normal_lines = []
        return text

    for line in content.splitlines():
        logger.debug("line: %r", line)
        is_markup = False
        was_code = bool(in_code)
        # if first and re.search(r"\t<", line[0]):
        #     is_markup = True
        if not in_code and re.search(RE_TAGS, line):
            is_markup = True
        is_markdown_image = re.search(r"!\[.*\]\(.*\)", line)
        logger.debug("check line: %r", line)
        is_math_start = re.match(r"\s*(\$\$|```tex|```math|\\\[)$", line)
        is_math_end = re.match(r"\s*(\$\$|```|\\\])$", line)
        is_normal_line = False
        if re.match(r"\s*<(script|style|svg)\b", line, flags=re.IGNORECASE) and not in_code:
            in_code = 1
            in_script = True
            in_svg = re.match(r"\s*<svg\b", line, flags=re.IGNORECASE)
            if in_svg:
                out.append(line)
            else:
                out.append(line + "\n")
        elif re.match(r"\s*</(script|style|svg)>\s*$", line, flags=re.IGNORECASE) and in_script:
            out.append(line + "\n")
            in_code = 0
            in_script = False
            in_svg = False
        elif is_markup or is_markdown_image:
            out.append(line + "\n")
        elif is_math_start and not in_code:
            out.append("```math\n")
            in_math = True
            has_math = True
            in_code += 1
        elif is_math_end and in_math:
            out.append("```\n")
            in_math = False
            in_code = 0
        elif in_math:
            line = fix_math_escape_percentages(line)
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
    logger.debug("preprocess content: %s", content)
    return content, has_math


def preprocess_cli():
    """Preprocess stdin and print to stdout"""
    content = sys.stdin.read()
    processed, has_math = asyncio.run(preprocess(content, "/", "root"))
    print(processed)


async def process_include_maybe(line: str, bb_file: str, user: str|None, text: str, url_str: str, attributes_str: str) -> str:
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
    except Exception as e:
        logger.warning("Include error: %s, %s", url_str, e)
        return line

    try:
        with open(path) as f:
            text = f.read()
    except (FileNotFoundError, PermissionError) as e:
        logger.warning("Include file not readable: %s", path)
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


async def resolve_url_path(file: str, url: str, user: str|None, throw: bool = True, do_fetch: bool = False) -> str|None:
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
            else:
                return str(url)

        if parsed_url.scheme:
            raise ValueError(f"Unsupported URL scheme: {parsed_url.scheme}")

        # Local path
        # TODO improve this code, I think it's safe but it's not very simple
        safe_path, _rel_path = safe_path_for_local_file(file, url)

        # Check access permissions
        if not (user and check_access(user, safe_path)):
            raise PermissionError(f"Access denied to {safe_path} for user {user}")

        if not os.path.exists(safe_path):
            raise FileNotFoundError(f"Local file not found: {safe_path}")

        return str(safe_path)

    except Exception as e:
        logging.error(f"Error resolving file path {url}: {str(e)}")
        if throw:
            raise
        return None


def safe_path_for_local_file(file: str, url: str) -> str:
    """Resolve a local file path, ensuring it's safe and within the rooms directory."""
    room = Room(path=Path(file))
    if url.startswith("/"):
        path2 = Path(url[1:])
    else:
        path2 = (Path(room.name).parent)/url
    safe_path = safe_join(Path(ROOMS_DIR), Path(path2))
    rel_path = safe_path.relative_to(Path(ROOMS_DIR))
    return safe_path, rel_path


def parse_markdown_attributes(attr_str: str) -> dict:
    """Parse attributes in markdown format, e.g. {#id .class key=value key2="value 2"}"""
    attrs = {}
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
    global SPACE_MARKER, TAB_MARKER
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


def markdown_to_html_cli():
    """Convert markdown from stdin to html on stdout"""
    content = sys.stdin.read()
    html_content = markdown_to_html(content)
    print(html_content)


async def message_to_html(message: str, bb_file: str):
    """Convert a chat message to HTML."""
    global math_cache
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
            html_content = disenfuckulate_html(html_content)
        #            html_content = "\n".join(wrap_indent(line) for line in html_content.splitlines())
        #             html_content = html_content.replace("<br />", "")
        #             html_content = html_content.replace("<p>", "")
        #             html_content = html_content.replace("</p>", "\n")
        except Exception as e:
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


def disenfuckulate_html(html: str) -> str:
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
    html = re.sub(rf"<p><summary>(.*?)</summary><br\s*/>", r"<summary>\1</summary><p>", html)

    # Disabled for now, don't want to mess up code!
#     # remove empty paragraphs: could potentially mess up code but whatever
#     html = re.sub(rf"<p></p>", r"", html)
    return html


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
        print(asyncio.run(message_to_html(message)))


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

    if not room.check_access(user).value & Access.WRITE.value:
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

    logger.info(f"Uploading {name} to {room.name} by {user}: {file_path=} {url=}")

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
    if hasattr(source, "read"):
        return [ChatMessage(content=msg["content"], user=msg.get("user")) for msg in lines_to_messages(source)]

    # Handle path inputs
    path = Path(source) if isinstance(source, str) else source
    if not path.exists():
        return []

    with path.open("r", encoding="utf-8") as f:
        return load_chat_messages(f)


def save_chat_messages(messages: list[ChatMessage], destination: str | Path | TextIO = sys.stdout, mode: str = "a") -> None:
    """Write chat messages to a file path or file-like object.

    Args:
        messages: List of ChatMessage objects to write
        destination: Output file path, Path object, or file-like object (defaults to stdout)
        mode: File open mode when writing to a path, defaults to 'a' for append
    """
    # Handle file-like objects directly
    if hasattr(destination, "write"):
        for msg in messages:
            destination.write(chat_message_to_text(msg) + "\n")
        return

    # Handle path outputs
    path = Path(destination) if isinstance(destination, str) else destination
    with path.open(mode, encoding="utf-8") as f:
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
    content = re.sub(r"\*.*?\*", "", content)

    # 2. Remove lines that begin or end with *
    lines = content.split("\n")
    lines = [line for line in lines if not (line.strip().startswith("*") or line.strip().endswith("*"))]
    content = "\n".join(lines)

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
    lines = content.split("\n")
    lines_out = []
    for line in lines:
        if line.strip().startswith("*") and not line.strip().endswith("*"):
            line += "*"
        if line.strip().endswith("*") and not line.strip().startswith("*"):
            line = "*" + line
        lines_out.append(line)
    content = "\n".join(lines_out)

    # 2. Remove random selection of text between * and * (non-greedy match)
    def random_replace(match):
        """Replace match with empty string with probability prob."""
        return "" if random.random() < prob else match.group(0)

    content = re.sub(r"\*.*?\*", random_replace, content)

    # 3. squeeze whitespace and strip, preserving the format
    content = re.sub(r"\s*\n\n+\s*", "\n\n", content)
    content = re.sub(r" +", " ", content)
    content = content.strip()

    # 4. Check if anything remains
    if not content:
        return None

    # Create new message with filtered content
    return ChatMessage(
        user=message.user,
        content=content,
    )


def load_config(dir_path: Path, filename: str) -> dict[str, Any]:
    """Load YAML configuration from files."""
    # list of folders from dir_path up to ROOMS_DIR
    rel_path = dir_path.relative_to(ROOMS_DIR)
    folders = [rel_path] + list(rel_path.parents)
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


def read_agents_list(path) -> list[str]:
    """Read the list of agents from a file."""
    if not path.exists():
        return []
    agent_names = cache.load(path)
    if not isinstance(agent_names, list):
        raise ValueError("Invalid agents list")
    agent_names = [name.lower() for name in agent_names]
    return agent_names


def read_agents_lists(path) -> list[str]:
    """Read the list of agents from a file."""
    top_dir = Path(os.environ["ALLEMANDE_ROOMS"])
    agent_names = []

    room_dir = path
    # if not a dir, go to parent
    if not room_dir.is_dir():
        room_dir = room_dir.parent
    if top_dir != room_dir and top_dir not in room_dir.parents:
        raise ValueError(f"Invalid room directory: {room_dir}")

    while True:
        agent_names.extend(read_agents_list(room_dir / ".agents.yml"))
        if room_dir == top_dir:
            break
        room_dir = room_dir.parent

    return list(set(agent_names))


def check_access(user: str|None, pathname: Path | str) -> Access:
    """Check if the user has access to the path, and log the access."""
    if isinstance(pathname, Path):
        pathname = str(pathname)
    try:
        access, reason = _check_access_2(user, pathname)
    except PermissionError as e:
        access, reason = Access.NONE, "PermissionError"
    #     logger.info("check_access: User: %s, pathname: %s, Access: %s, Reason: %s", user, pathname, access, reason)
    return access


def _check_access_2(user: str|None, pathname: str) -> tuple[Access, str]:
    """Check if the user has access to the path"""
    # TODO make a wrapper method in the room class
    # user has access to the top-level dir, all files at the top-level
    # their own directory (/username/), and all files in their own directory (/username/*)
    # TODO detailed access control via files for exceptions

    # TODO What's the difference between a moderator and an admin?
    #      Do we need both?

    if pathname == "/":
        pathname = ""

    # handle absolute paths
    if pathname == ROOMS_DIR:
        pathname = ""
    elif pathname.startswith(ROOMS_DIR + "/"):
        pathname = pathname[len(ROOMS_DIR) + 1 :]

    # If pathname ends with / it's a directory
    is_dir = pathname.endswith("/") or pathname == ""

    #     logger.info("pathname %r is_dir %r", pathname, is_dir)

    if sanitize_pathname(pathname) != pathname:
        raise ValueError(f"Invalid pathname, not sanitized: {pathname}, {sanitize_pathname(pathname)}")

    try:
        path = safe_join(Path(ROOMS_DIR), Path(pathname))
    except ValueError:
        return Access.NONE, "invalid_path"

    if is_dir:
        dir_path = path
    else:
        dir_path = path.parent

    access = load_config(dir_path, ".access.yml")
    agent_names = read_agents_lists(path)

    logger.debug("path %r access %r", path, access)

    if user is not None:
        user = user.lower()

    logger.debug("check_access: User: %s, pathname: %s, Path: %s", user, pathname, path)

    # Admins have access to everything
    if user in ADMINS:
        return Access.ADMIN, "admin"

    # Moderators have moderation on the root
    if user in MODERATORS and pathname == "":
        return Access.MODERATE_READ_WRITE, "moderator"

    # Users have admin on their own directory, and files in their own directory
    if user is not None and re.match(rf"{user}\.[a-z]+$", pathname, flags=re.IGNORECASE) or pathname == user or pathname.startswith(user + "/"):
        return Access.ADMIN, "user_dir"

    # Users have admin on their top-level room, or a file with their name and any extension
    if user is not None and re.match(rf"{user}\.[a-z]+$", pathname, flags=re.IGNORECASE):
        return Access.ADMIN, "user_top"

    exists = True
    try:
        stats = path.lstat()
    except FileNotFoundError:
        exists = False

    is_file = not exists or S_IFMT(stats.st_mode) == S_IFREG
    is_symlink = exists and S_IFMT(stats.st_mode) == S_IFLNK

    # Symlink, must have access to the target too
    if is_symlink:
        target = None
        try:
            target = path.resolve().relative_to(ROOMS_DIR)
        except ValueError:
            # target is not in ROOMS_DIR, that's fine, don't check access
            pass
        except FileNotFoundError:
            return Access.NONE, "broken_symlink"
        if target and not check_access(user, str(target)).value & Access.READ.value:
            return Access.NONE, "symlink_target unreadable"

    # Moderators have moderation on all files in the root
    if user in MODERATORS and not "/" in pathname and (is_file or is_symlink):
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
    if not "/" in pathname and (is_file or is_symlink):
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

# symlink done above?
#     if access & Access.READ.value and is_symlink:
#         return check_access(user, str(Path(pathname).resolve()))

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
            ["git", "rev-parse", "--show-toplevel"], cwd=os.path.dirname(abs_path), text=True
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
        # Check if there are staged changes for the file
        result = subprocess.run(["git", "diff", "--staged", "--quiet", rel_path], cwd=repo_root, capture_output=True)

        # If exit code is 1, there are changes to commit
        if result.returncode == 1:
            # Proceed with commit
            subprocess.run(["git", "commit", "-m", f"Backup {rel_path}", rel_path], check=True, cwd=repo_root)
    except subprocess.CalledProcessError as e:
        # Handle any git command failures
        print(f"Git operation failed: {e}")


async def overwrite_file(user, file, content, backup=True, delay=0.2, noclobber=False):
    """Overwrite a file with new content."""
    logger.warning("overwrite_file: %s", file)
    path = str(name_to_path(file))
    file = None  # be safe
    logger.warning("  path: %s", path)
    access = check_access(user, path).value
    if not access & Access.WRITE.value:
        raise PermissionError(f"You are not allowed to overwrite this file: user: {user}, path: {path}, access: {access}")
    exists = Path(path).exists()
    if exists and Path(path).is_dir():
        raise ValueError(f"Cannot overwrite a directory: {path}")
    if exists and noclobber:
        raise ValueError(f"File already exists, will not overwrite: {path}")
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


def move_file(user, source, dest, clobber=False):
    """Move a file to a new location."""
    source_path = name_to_path(source)
    dest_path = name_to_path(dest)
    access = check_access(user, source_path).value
    if not access & Access.WRITE.value:
        raise PermissionError(f"You are not allowed to move this file: user: {user}, path: {source_path}, access: {access}")
    access = check_access(user, dest_path).value
    if not access & Access.WRITE.value:
        raise PermissionError(f"You are not allowed to move to this location: user: {user}, path: {dest_path}, access: {access}")
    if not clobber and Path(dest_path).exists():
        raise ValueError(f"Destination already exists: {dest_path}")

    # hack: if moving a folder, the user would have to be able to write to a file within the proposed destination folder
    dest_example_file = Path(dest_path) / ("chat" + EXTENSION)
    access = check_access(user, dest_example_file).value
    if not access & Access.WRITE.value:
        raise PermissionError(f"You are not allowed to write to this location: user: {user}, path: {dest}/, access: {access}")

    try:
        # move html files for chat rooms too
        # should I move config files too? not right now
        if source_path.suffix == EXTENSION and dest_path.suffix == EXTENSION:
            source_html = source_path.with_suffix(".html")
            dest_html = dest_path.with_suffix(".html")
            if source_html.exists():
                # ok to overwrite the html file
                shutil.move(source_html, dest_html)

        shutil.move(str(source_path), str(dest_path))
    except (shutil.Error, OSError) as e:
        raise PermissionError(f"Error moving file: {e}")


def remove_thinking_sections(content: str, agent: Agent | None, n_own_messages: int) -> tuple[str, int]:
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
        flags=re.MULTILINE | re.IGNORECASE | re.VERBOSE | re.DOTALL,
    )
    if modified != content:
        logger.debug("Removed 'thinking' section/s from message: original: %s", content)
        logger.debug("  modified: %s", modified)
        return modified, n_own_messages
    logger.debug("No 'thinking' section/s found in message: %s", content)
    return content, n_own_messages


def context_remove_thinking_sections(context: list[str], agent: Agent | None) -> list[str]:
    """Remove "thinking" sections from the context."""
    # Remove any "thinking" sections from the context
    # A "thinking" section is a <think> block

    n = len(context)
    n_own_messages = 0
    for i in range(n - 1, -1, -1):
        context[i], n_own_messages = remove_thinking_sections(context[i], agent, n_own_messages)

    return context


def history_remove_thinking_sections(history: list[dict[str, Any]], agent: Agent | None):
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


def process_chat_cli(code: str | None = None, func: str | None = None):
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
    text1 = regex.sub(
        r".*?```\w*\s*" + agent_name_esc + r"\b[,;.!:]*(.*?)```.*", r"\1", text, flags=regex.DOTALL | regex.IGNORECASE, count=1
    )

    logger.debug("clean_prompt: 2: %s", text1)

    # Remove up to the first occurrence of the agent's name (case insensitive) and any following punctuation, with single backticks
    if text1 == text:
        text1 = regex.sub(
            r".*?`\s*" + agent_name_esc + r"\b[,;.!:]*(.*?)`.*", r"\1", text, flags=regex.DOTALL | regex.IGNORECASE, count=1
        )

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


def apply_editing_commands(messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Apply editing commands to the chat history."""
    #     logger.info("\n\n\n")
    #     logger.info("messages before editing commands: %r", messages)
    #     logger.info("\n\n\n")
    lookup = messages.copy()
    for i in range(len(messages)):
        message = messages[i]
        m = re.search(r"""(<allychat-meta\b[-a-z0-9 ="']*>)\s*$""", message["content"], flags=re.IGNORECASE)
        if not m:
            continue
        xmltext = m.group(1).strip()
        # chop it off the message content
        message["content"] = message["content"][: m.start()].rstrip()
        soup = BeautifulSoup(xmltext, "html.parser")
        meta = soup.find("allychat-meta")
        if not meta:
            raise ValueError("Invalid allychat-meta tag.")

        remove = meta.get("remove")
        edit = meta.get("edit")
        insert = meta.get("insert")

        # remove the remove, edit and insert attributes
        for attr in ["remove", "edit", "insert"]:
            if attr in meta.attrs:
                del meta[attr]
        # add the meta tag back to the message content if there are any remaining attributes
        if meta.attrs:
            message["content"] += str(meta)

        rm_ids = []
        if edit:
            rm_ids.append(int(edit))
        elif remove:
            rm_ids += list(map(int, remove.split(" ")))
        for rm_id in rm_ids:
            if rm_id <= len(lookup):
                #                 logger.warning("Removing message ID: %s", rm_id)
                lookup[rm_id]["remove"] = True
            else:
                logger.warning("Invalid message ID in editing command: %s", rm_id)

        if edit and insert:
            logger.warning("Both edit and insert attributes in the same message, will edit: %s", message)

        target = edit or insert
        if target is not None:
            if "before" not in lookup[int(target)]:
                lookup[int(target)]["before"] = [message]
            else:
                lookup[int(target)]["before"].append(message)
            messages[i] = None

        #         logger.info("message ID: %s, remove: %s, edit: %s, insert: %s, content: %s", i, remove, edit, insert, message["content"])

        # if a message that wasn't moved is now empty, mark it for removal
        if remove and not edit and not insert and not message["content"].strip():
            #             logger.warning("Removing editing message ID: %s", i)
            messages[i]["remove"] = True

    #     logger.info("messages after editing commands: %r", messages)
    #     logger.info("\n\n\n")

    output = []
    flatten_edited_messages(messages, output)

    #     logger.info("apply_editing_commands: output: %r", output)
    #     logger.info("\n\n\n")

    return output


def flatten_edited_messages(messages, output):
    """Flatten edited messages."""
    for message in messages:
        if message is None:
            continue
        if "before" in message:
            flatten_edited_messages(message["before"], output)
        if "remove" not in message:
            output.append(message)


def main():
    def proc(code: str | None = None, func: str | None = None):
        return process_chat_cli(code, func)

    def html():
        return chat_to_html()

    def pre():
        return preprocess_cli()

    def markdown():
        return markdown_to_html_cli()

    argh.dispatch_commands(
        [
            proc,
            html,
            pre,
            markdown,
        ]
    )


if __name__ == "__main__":
    main()
