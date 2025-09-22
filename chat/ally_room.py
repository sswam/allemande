#!/usr/bin/env python3-allemande

"""Allemande chat rooms library"""

from pathlib import Path
import os
import re
import shutil
import subprocess
import io
import logging
import enum
from typing import Any
from stat import S_IFMT, S_IFREG, S_IFDIR, S_IROTH, S_IWOTH, S_IFLNK, S_IWGRP, S_IRGRP
import asyncio
from datetime import datetime

from deepmerge import always_merger

from settings import EXTENSION, ROOMS_DIR, ADMINS, MODERATORS, PATH_HOME
from util import backup_file, tree_prune, tac, sanitize_pathname, safe_join
from bb_lib import load_chat_messages, save_chat_messages, message_to_text
from ally.cache import cache  # type: ignore # pylint: disable=wrong-import-order


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Access(enum.Enum):  # pylint: disable=too-few-public-methods
    """Access levels for a room, file, or directory."""

    NONE = 0
    READ = 1
    WRITE = 2
    READ_WRITE = 3
    MODERATE = 4
    MODERATE_READ_WRITE = 7
    ADMIN = 15


class Room:
    """A chat room object."""

    def __init__(self, name: str | None = None, path: Path | None = None):
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

    def write(self, user: str | None, content: str) -> None:
        """
        Write a message to a room.
        We don't convert to HTML here, a follower process does that.
        """
        access = self.check_access(user).value
        if not access & Access.WRITE.value:
            raise PermissionError("You are not allowed to post to this room.")

        # support narration by moderators
        if content.startswith("--") and access & Access.MODERATE.value == Access.MODERATE.value:
            user = None
            content = content[2:]

        content = "\n".join(line.rstrip() for line in content.rstrip().splitlines())

        if content == "":
            # touch the markdown_file, to poke some attention
            self.touch()
            return

        user_tc: str | None = None

        if user and user == user.lower():
            user_tc = user.title()
        else:
            user_tc = user

        #         options = self.get_options(user)

        #         # timestamps option
        #         if options.get("timestamps"):
        #             now = datetime.now()
        #             timestamp = now.strftime("%Y-%m-%dT%H:%M:%SZ")
        #             human_time = now.strftime("%Y-%m-%d %H:%M:%S")
        #             content = f"""<time datetime="{timestamp}">{human_time}</time>{content}"""

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
            if not access & Access.MODERATE.value == Access.MODERATE.value:
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
            if not access & Access.ADMIN.value == Access.ADMIN.value:
                raise PermissionError("You are not allowed to clear this room.")
            if backup:
                backup_file(str(self.path))
            # If there is a base file, copy it to the room
            # e.g. foo.bb => foo.bb.base
            # else, truncate the file
            # The template can be foo.bb.base or .foo.bb.base
            template_file_1 = self.path.with_suffix(".bb.base")
            template_file_2 = template_file_1.parent / ("." + template_file_1.name)
            for template_file in (template_file_1, template_file_2):
                if template_file.exists():
                    shutil.copy(template_file, self.path)
                    break
            else:
                # self.path.write_text("")
                self.path.unlink()
        elif op == "clean":
            await self.clean(user)
        elif op == "render":
            if not access & Access.MODERATE.value == Access.MODERATE.value:
                raise PermissionError("You are not allowed to re-render this room.")
            content = self.path.read_text(encoding="utf-8")
            await overwrite_file(user, self.name + EXTENSION, content, delay=0.2, noclobber=False)
        else:
            raise ValueError(f"Unknown operation: {op}")

    async def undo(self, user, n=1, backup=True, delay: float = 0.2):
        """Remove the last n messages from a room."""
        # Messages are delimited by blank lines, and the file should end with a blank line.
        if n <= 0:
            return

        access = self.check_access(user).value
        if n > 1 and not access & Access.ADMIN.value == Access.ADMIN.value:
            raise PermissionError("You are not allowed to undo multiple messages in this room.")

        if not access & Access.MODERATE.value == Access.MODERATE.value:
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

        if delay:
            await asyncio.sleep(delay)

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
        if not access & Access.MODERATE.value == Access.MODERATE.value:
            raise PermissionError("You are not allowed to clean this room.")
        messages = load_chat_messages(self.path)
        # TODO don't hard-code the agent names!!!
        # TODO it would be better to do this as a view
        exclude = ["Illu", "Pixi", "Atla", "Chaz", "Brie", "Morf", "Pliny", "Sia", "Sio", "Summar", "Summi"]
        narrators = ["Nova", "Jily", "Hily", "Yoni", "Poni", "Coni", "Boni", "Bigi", "Pigi", "Dily", "Wili"]

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

    def check_access(self, user: str | None) -> Access:
        """Check access for a user."""
        return check_access(user, self.name + EXTENSION)

    def find_resource_file(self, ext, name=None, create=False, try_room_name=True) -> str|None:
        """Find a resource file for the chat room.
        Tries to find the file in the following order:
        1. room_name.ext
        2. .room_name.ext
        3. room_name_without_number.ext (if applicable)
        4. .room_name_without_number.ext (if applicable)
        5. specified_name.ext (if name provided)
        6. .specified_name.ext (if name provided)

        If name starts with '/', the path will be relative to ROOMS_DIR.
        """
        parent = self.path.parent
        stem = self.path.stem
        possible_paths = []

        # Handle absolute paths (relative to ROOMS_DIR)
        if name and name.startswith('/'):
            parent = Path(ROOMS_DIR)
            name = name[1:]

        # Collect all possible paths
        if try_room_name:
            possible_paths.append(parent / f"{stem}.{ext}")
            possible_paths.append(parent / f".{stem}.{ext}")

            # Check stem without number
            stem_no_num = re.sub(r"-\d+$", "", stem)
            if stem_no_num != stem:
                possible_paths.append(parent / f"{stem_no_num}.{ext}")
                possible_paths.append(parent / f".{stem_no_num}.{ext}")

        if name:
            possible_paths.append(parent / f"{name}.{ext}")
            possible_paths.append(parent / f".{name}.{ext}")

        # Try each path in order
        for path in possible_paths:
            if path.exists():
                return str(path)

        # If create flag is True, return the first non-hidden path even if it doesn't exist
        if create and possible_paths:
            # Find first non-hidden path
            for path in possible_paths:
                if not path.name.startswith('.'):
                    return str(path)

        return None

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
        options = {}
        if options_file:
            try:
                options = cache.load(options_file)
            except Exception as e:
                logger.error("Error loading options file %s: %s", options_file, e)
        return options

    def set_options(self, user, new_options):
        """Set the options for a room."""
        access = self.check_access(user).value
        if not access & Access.MODERATE.value == Access.MODERATE.value:
            raise PermissionError("You are not allowed to set options for this room.")
        options_file = self.find_resource_file("yml", "options", create=True)

        # access control for mission option: user setting the mission must have access to the resolved mission file
        # It's a bit wack, because it could resolve to a different file later. But good enough I guess.
        mission_new = new_options.get("mission")
        if mission_new:
            mission_file = self.find_resource_file("m", mission_new, try_room_name=False)
            if not mission_file:
                logger.warning("set_options: mission not resolved: %s", mission_new)
                del new_options["mission"]
            elif not check_access(user, mission_file).value & Access.READ.value:
                logger.warning("set_options: mission access denied: %s", mission_new)
                del new_options["mission"]

        if options_file:
            logger.debug("options file: %s", options_file)
            options = cache.load(options_file) or {}
            logger.debug("old options: %r", options)
            logger.debug("new options: %r", new_options)

            # otherwise they double up
            if "mediator" in new_options:
                new_options["mediator"] = []

            always_merger.merge(options, new_options)  # modifies options
            logger.debug("merged options: %r", options)
            options = tree_prune(options)
            logger.debug("pruned options: %r", options)
            cache.save(options_file, options)
        else:
            raise FileNotFoundError("Options file not found.")

    def get_last_room_number(self, user: str) -> str:
        """Get the last room number."""
        access = check_access(user, str(self.parent)+"/").value
        if not access & Access.READ.value:
            raise PermissionError("You are not allowed to get the last room number.")

        # chop off any number
        name = self.name
        name = re.sub(r"-\d+$", "", name)

        # chop off trailing slash for folders
        name = name.rstrip("/")
        # TODO what happens with top dir?

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
        files = [int(f) for f in files if re.match(r'[0-9]+$', f)]

        # find the maximum
        last = max(files, default=-1)

        last = "" if last == -1 else str(last)

        return last


def check_access(user: str | None, pathname: Path | str) -> Access:
    """Check if the user has access to the path, and log the access."""
    if isinstance(pathname, Path):
        pathname = str(pathname)
    try:
        access, _reason = _check_access_2(user, pathname)
    except PermissionError as _e:
        access, _reason = Access.NONE, "PermissionError"
    logger.debug("check_access: User: %s, pathname: %s, Access: %s, Reason: %s", user, pathname, access, _reason)

    # experiment: allow anyone who can write to moderate
    if access.value & Access.WRITE.value:
        access = Access(access.value | Access.MODERATE_READ_WRITE.value)

    return access


# pylint: disable=too-many-branches, too-many-return-statements, too-many-statements
def _check_access_2(user: str | None, pathname: str) -> tuple[Access, str]:
    """Check if the user has access to the path"""
    # TODO make a wrapper method in the room class
    # user has access to the top-level dir, all files at the top-level
    # their own directory (/username/), and all files in their own directory (/username/*)
    # TODO detailed access control via files for exceptions

    # TODO What's the difference between a moderator and an admin?
    #      Do we need both?

    users_path = str(PATH_HOME/"users.txt")
    users = cache.load(users_path).strip().split("\n")

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
        return Access.NONE, "invalid_path_hidden_or_not_sanitized"

    try:
        path = safe_join(Path(ROOMS_DIR), Path(pathname))
    except ValueError:
        return Access.NONE, "invalid_path"

    if is_dir:
        dir_path = path
    else:
        dir_path = path.parent

    access_conf = load_config(dir_path, "access.yml")
    agent_names = read_agents_lists(path)

    # find overlapping names
    overlapping_names = set(agent_names).intersection(set(users))

    # log warning if there are overlaps
    if overlapping_names:
        logging.warning(f"Found overlapping agent and user names: {', '.join(sorted(overlapping_names))}")

    # remove overlapping names
    agent_names = list(set(agent_names) - set(users))

    logger.debug("path %r access %r", path, access_conf)

    if user is not None:
        user = user.lower()

    logger.debug("check_access: User: %s, pathname: %s, Path: %s", user, pathname, path)

    # Admins have access to everything
    if user in ADMINS:
        return Access.ADMIN, "admin"

    # Moderators have moderation on the root
    if user in MODERATORS and pathname == "":
        return Access.MODERATE_READ_WRITE, "moderator"

    # Denied users have no access
    if user in access_conf.get("deny", []):
        return Access.NONE, "deny"

    # Users have admin on their own directory, and files in their own directory
    if (
        user is not None
        and re.match(rf"{user}\.[a-z]+$", pathname, flags=re.IGNORECASE)
        or pathname == user
        or pathname.startswith(f"{user}/")
    ):
        return Access.ADMIN, "user_dir"

    # Users have admin on their top-level room, or a file with their name and any extension
    if user is not None and re.match(rf"{user}\.[a-z]+$", pathname, flags=re.IGNORECASE):
        return Access.ADMIN, "user_top"

    exists = True
    try:
        stats = path.lstat()
    except FileNotFoundError:
        exists = False

    entry_is_dir = exists and S_IFMT(stats.st_mode) == S_IFDIR
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

    # Allowed users have access
    logger.debug("access: %s", access_conf)
    if user in access_conf.get("allow", []):
        return Access.READ_WRITE, "allow"

    # Agents have access if allowed
    if access_conf.get("allow_agents") and user in agent_names:
        return Access.READ_WRITE, "allow_agents"

    # Users have access to the root
    if pathname == "":
        return Access.READ, "root"

    # Users have access to files in the root, check is a file
    if not "/" in pathname and (is_file or is_symlink):
        return Access.READ_WRITE, "user_root_file"


    # users have access to files in a shared folder
    # stat if dir_path is group readable
    try:
        dir_stat = dir_path.lstat()
    except FileNotFoundError:
        return Access.NONE, "dir_not_found"

    dir_mode = dir_stat.st_mode
    logger.debug(f"path: {path}, entry_is_dir: {entry_is_dir}, dir_path: {dir_path}, dir_mode: {dir_mode:#o}, S_IWGRP: {S_IWGRP:#o}, S_IRGRP: {S_IRGRP:#o}")
    if not entry_is_dir and dir_mode & S_IWGRP:
        return Access.READ_WRITE, "shared_public_writable"

    if not exists:
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


def load_config(dir_path: Path, filename: str, check_hidden=True) -> dict[str, Any]:
    """Load YAML configuration from files."""
    if filename.startswith("."):
        check_hidden = False

    # list of folders from dir_path up to ROOMS_DIR
    rel_path = dir_path.relative_to(ROOMS_DIR)
    folders = [rel_path] + list(rel_path.parents)
    # Go top-down from ROOMS_DIR to the folder containing the file
    config_all = {}

    for folder in reversed(folders):
        # Check regular file
        config_path = ROOMS_DIR / folder / filename
        hidden_config_path = ROOMS_DIR / folder / f".{filename}"

        paths_to_check = [config_path]
        if check_hidden:
            paths_to_check.append(hidden_config_path)

        for path in paths_to_check:
            if not path.exists():
                continue
            config = cache.load(path)
            if config.get("reset"):
                config_all = config
            else:
                # We only merge at the top level
                config_all.update(config)
            break
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

    agent_names.extend(read_agents_list(top_dir / ".agents_global.yml"))

    return list(set(agent_names))


# pylint: disable=too-many-arguments, too-many-positional-arguments
async def overwrite_file(user: str | None, file: str, content: str, backup: bool = True, delay: float = 0.2, noclobber: bool = False, remove_empty=False):
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
    # if the file is now empty, remove it (optional)
    if remove_empty and not content:
        os.unlink(path)


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
    if not clobber and dest_path.exists() and dest_path.stat().st_size != 0:
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
        raise PermissionError(f"Error moving file: {e}") from e


def name_to_path(name: str) -> Path:
    """Convert a filename to a path."""
    name = sanitize_pathname(name)
    assert isinstance(name, str)
    assert not name.startswith("/")
    assert not name.endswith("/")
    return Path(ROOMS_DIR) / name


def safe_path_for_local_file(file: str, url: str) -> tuple[str, str]:
    """Resolve a local file path, ensuring it's safe and within the rooms directory."""
    room = Room(path=Path(file))
    if url.startswith("/"):
        path2 = Path(url[1:])
    else:
        path2 = (Path(room.name).parent) / url
    safe_path = safe_join(Path(ROOMS_DIR), path2)
    rel_path = safe_path.relative_to(Path(ROOMS_DIR))
    safe_path_s = str(safe_path)
    rel_path_s = str(rel_path)
    if url.endswith("/"):
        safe_path_s += "/"
        rel_path_s += "/"
    return safe_path_s, rel_path_s
