#!/usr/bin/env python3-allemande

"""
Manage users in the Allemande webchat system.
"""

import os
import sys
import subprocess
import getpass
import secrets
import string
from pathlib import Path
from datetime import datetime
from typing import TextIO

import sh  # type: ignore
import yaml

from ally import main, logs  # type: ignore

__version__ = "0.1.0"

logger = logs.get_logger()


def die(msg: str) -> None:
    """Exit with error message."""
    logger.error(msg)
    sys.exit(1)


def generate_password() -> str:
    """Generate a simple 6-character password without confusing characters."""
    # Similar to pwgen -B behavior - avoid ambiguous characters
    chars = string.ascii_letters + string.digits
    avoid = "0O1lI"
    chars = ''.join(c for c in chars if c not in avoid)
    return ''.join(secrets.choice(chars) for _ in range(6))


def run_command(cmd: list[str], check: bool = True, **kwargs) -> subprocess.CompletedProcess:
    """Run a shell command."""
    logger.debug("Running: %s", ' '.join(cmd))
    return subprocess.run(cmd, check=check, capture_output=True, text=True, **kwargs)


def get_user_list(htpasswd_path: Path) -> list[str]:
    """Get list of users from htpasswd file."""
    if not htpasswd_path.exists():
        return []
    with open(htpasswd_path) as f:
        users = [line.split(':')[0].lstrip('*') for line in f if ':' in line]
    return sorted(users)


def get_nsfw_users(nsfw_access_file: Path) -> list[str]:
    """Get list of NSFW users from access file."""
    if not nsfw_access_file.exists():
        return []
    with open(nsfw_access_file) as f:
        data = yaml.safe_load(f) or {}
    return sorted(data.get('allow', []))


def add_user(
    username: str,
    contact: str,
    nsfw: bool,
    istream: TextIO,
    ostream: TextIO,
) -> None:
    """Add a new user to the system."""
    if not username:
        username = input("Username: ")

    if username != username.lower():
        die("Username must be lower-case")

    if username.startswith('-'):
        die("Username cannot start with a dash")

    # Check if user exists
    htpasswd_path = Path(".htpasswd")
    existing_users = get_user_list(htpasswd_path)
    if username in existing_users:
        die(f"User {username} already exists")

    # Generate password
    password = generate_password()

    # Add to htpasswd
    run_command(["htpasswd", "-b", ".htpasswd", username, password])

    # Add system user
    result = run_command(["sudo", "chpasswd"], input=f"{username}:{password}", check=False)
    if result.returncode != 0:
        logger.warning("Failed to add system user: %s", result.stderr)

    # Create user directories
    rooms_dir = Path("rooms") / username
    rooms_dir.mkdir(parents=True, exist_ok=True)
    rooms_dir.chmod(0o750)  # g-w,o-rwx

    static_dir = Path("static/users") / username
    static_dir.mkdir(parents=True, exist_ok=True)

    # Create static files
    (static_dir / "styles.css").touch()
    (static_dir / "script.js").touch()

    # Create theme symlink
    theme_link = static_dir / "theme.css"
    if not theme_link.exists():
        theme_link.symlink_to("../../themes/dark.css")

    # Set up room files
    help_base = rooms_dir / ".help.bb.base"
    if not help_base.exists():
        help_base.symlink_to("../../rooms.dist/help.bb.base")

    if nsfw:
        run_command(["cp", "../rooms.dist/mission.m.nsfw", str(rooms_dir / "mission.m")])
        run_command(["cp", "../rooms.dist/access_nsfw.yml", str(rooms_dir / ".access.yml")])
    else:
        run_command(["cp", "../rooms.dist/mission.m.sfw", str(rooms_dir / "mission.m")])

    run_command(["cp", "../rooms.dist/.gitignore", str(rooms_dir / ".gitignore")])

    # Set up help files
    help_m = rooms_dir / ".help.m"
    if nsfw:
        with open("rooms/nsfw/.access.yml", "a") as f:
            f.write(f"- {username}\n")
        if not help_m.exists():
            help_m.symlink_to("../../doc/nsfw/guide.md")
        help_base_nsfw = rooms_dir / ".help.bb.base"
        if help_base_nsfw.exists():
            help_base_nsfw.unlink()
        help_base_nsfw.symlink_to("../../rooms.dist/help.bb.base.nsfw")
    else:
        if not help_m.exists():
            help_m.symlink_to("../../doc/guide.md")

    # Create help.bb file (delayed to avoid double detection)
    help_bb = rooms_dir / "help.bb"
    if not help_bb.exists():
        subprocess.Popen([
            "sh", "-c",
            f"sleep 1; cp {rooms_dir}/.help.bb.base {help_bb} && "
            f"touch -t 197001010000 {help_bb} && chmod o-rwx {help_bb}"
        ])

    # Add to rooms/.gitignore
    gitignore_path = Path("rooms/.gitignore")
    with open(gitignore_path, "a") as f:
        f.write(f"/{username}\n")

    # Initialize git with arcs
    os.chdir(rooms_dir)
    run_command(["sh", "-c", "yes n | arcs -i"], check=False)
    os.chdir("../..")

    # Create info.rec file
    users_dir = Path(os.environ.get("ALLEMANDE_USERS", "users"))
    user_info_dir = users_dir / username
    user_info_dir.mkdir(parents=True, exist_ok=True)

    info_rec_path = user_info_dir / "info.rec"
    if not info_rec_path.exists():
        btime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Parse contact info
        contact_type = ""
        contact_value = ""
        if contact:
            if ':' in contact:
                contact_type, contact_value = contact.split(':', 1)
            else:
                contact_value = contact

        # Build info.rec content
        info_content = []
        info_content.append(f"name:\t{username}")
        info_content.append(f"status:\tactive")
        info_content.append(f"btime:\t{btime}")

        # Add specific contact fields
        if contact_type == "reddit":
            info_content.append(f"reddit:\t{contact_value}")
        elif contact_type == "discord":
            info_content.append(f"discord:\t{contact_value}")
        elif contact_type == "facebook":
            info_content.append(f"facebook:\t{contact_value}")
        elif contact_type in ["email"]:
            info_content.append(f"email:\t{contact_value}")
        elif contact:
            info_content.append(f"contact:\t{contact}")

        # Add empty fields for completeness
        for field in ["email", "reddit", "discord", "facebook", "agents", "contact", "notes"]:
            if not any(line.startswith(f"{field}:") for line in info_content):
                info_content.append(f"{field}:\t")

        with open(info_rec_path, "w") as f:
            f.write('\n'.join(info_content) + '\n')
        info_rec_path.chmod(0o640)  # o-rwx

    # Run make
    allychat_home = os.environ.get("ALLYCHAT_HOME", ".")
    os.chdir(allychat_home)
    run_command(["make"])

    # Output welcome message
    domain = os.environ.get("ALLEMANDE_DOMAIN", "example.com")

    welcome_msg = f"""=== Welcome to Ally Chat! ===

Log in at https://{domain}
Username: {username}
Password: {password}


=== Getting Started ===

1. Say hi in the main 'Ally Chat' room
2. Press the '?' button and read the Intro
3. Open the 'help' tab and ask the AI some questions
- This is the place to get help about the app
4. Close the help with the X at top-right
"""

    if nsfw:
        welcome_msg += """
For NSFW content:

5. Do not upload or generate illegal content, i.e. CSAM or NCII.
6. Press the 'E' or enter 'nsfw' in the room field to visit the NSFW zone.
7. NSFW features also work in private chat.

"""

    welcome_msg += """
=== Beta Program ===

- Ally Chat is a power tool, and can be confusing for beginners.
- You are responsible for your own safety and behaviour.
- I can give you a demo in the app, to help you get started.
- Please participate in group chats, and give feedback.
- You can support us on Patreon if you like the app.

"""

    if nsfw:
        welcome_msg += "- https://www.patreon.com/allychat (SFW)\n"
        welcome_msg += "- https://www.patreon.com/allychatx (NSFW)\n"
    else:
        welcome_msg += "- https://www.patreon.com/allychat\n"

    ostream.write(welcome_msg)
    ostream.write(f"\n+ {username} {password}\n")


def change_password(username: str, password: str, interactive: bool) -> tuple[str, str]:
    """Change a user's password."""
    if not username:
        username = input("Username: ")

    if password == "-i" or interactive:
        while True:
            pass1 = getpass.getpass("Enter password: ")
            pass2 = getpass.getpass("Confirm password: ")
            if pass1 == pass2:
                password = pass1
                break
            print("Passwords do not match. Please try again.")
    elif not password:
        password = generate_password()

    # Update htpasswd
    run_command(["htpasswd", "-b", ".htpasswd", username, password])

    # Update system password
    result = run_command(["sudo", "chpasswd"], input=f"{username}:{password}", check=False)
    if result.returncode != 0:
        logger.warning("Failed to update system password: %s", result.stderr)

    return username, password


def remove_user(username: str) -> None:
    """Remove a user from the system."""
    if not username:
        username = input("Username: ")

    # Remove from htpasswd
    run_command(["htpasswd", "-D", ".htpasswd", username])

    # Remove from .access.yml files
    access_files = Path("rooms").rglob(".access.yml")
    for access_file in access_files:
        with open(access_file) as f:
            lines = f.readlines()
        with open(access_file, "w") as f:
            for line in lines:
                if line.strip() != f"- {username}":
                    f.write(line)

    # Move user static directory to trash
    static_dir = Path("static/users") / username
    if static_dir.exists():
        run_command(["move-rubbish", str(static_dir)], check=False)

    # Remove system user
    result = run_command(["sudo", "userdel", "--", username], check=False)
    if result.returncode != 0:
        logger.warning("Failed to remove system user: %s", result.stderr)

    # Run make
    allychat_home = os.environ.get("ALLYCHAT_HOME", ".")
    os.chdir(allychat_home)
    run_command(["make"])

    print(f"- {username}")


def disable_user(username: str, comment: str) -> None:
    """Disable a user account."""
    if not username:
        username = input("Username: ")
    if not comment:
        comment = input("Comment: ")

    htpasswd_path = Path(".htpasswd")
    with open(htpasswd_path) as f:
        lines = f.readlines()

    with open(htpasswd_path, "w") as f:
        for line in lines:
            if line.startswith(f"{username}:"):
                parts = line.strip().split(":")
                f.write(f"*{username}:*{parts[1]}:{comment}\n")
            else:
                f.write(line)

    print(f"_ {username}")


def enable_user(username: str) -> None:
    """Enable a disabled user account."""
    if not username:
        username = input("Username: ")

    htpasswd_path = Path(".htpasswd")
    with open(htpasswd_path) as f:
        lines = f.readlines()

    with open(htpasswd_path, "w") as f:
        for line in lines:
            if line.startswith(f"*{username}:*"):
                # Remove the * prefix and any trailing comment
                line = line[1:]  # Remove first *
                parts = line.split(":")
                f.write(f"{username}:{parts[1][1:]}\n")  # Remove * from password hash
            else:
                f.write(line)

    print(f"+ {username}")


def list_users(filter_str: str, nsfw_filter: str | None) -> None:
    """List users, optionally filtering by NSFW status."""
    htpasswd_path = Path(".htpasswd")
    all_users = get_user_list(htpasswd_path)

    if filter_str:
        all_users = [u for u in all_users if filter_str.lower() in u.lower()]

    if nsfw_filter is None:
        # Show all users
        for user in all_users:
            print(user)
    elif nsfw_filter == "1":
        # Show only NSFW users
        nsfw_users = get_nsfw_users(Path("rooms/nsfw/.access.yml"))
        for user in nsfw_users:
            if not filter_str or filter_str.lower() in user.lower():
                print(user)
    elif nsfw_filter == "0":
        # Show only non-NSFW users
        nsfw_users = set(get_nsfw_users(Path("rooms/nsfw/.access.yml")))
        for user in all_users:
            if user not in nsfw_users:
                print(user)


def update_missions() -> None:
    """Update mission files for all users."""
    allemande_home = os.environ.get("ALLEMANDE_HOME", ".")
    allemande_rooms = os.environ.get("ALLEMANDE_ROOMS", "rooms")

    htpasswd_path = Path(".htpasswd")
    all_users = get_user_list(htpasswd_path)
    nsfw_users = set(get_nsfw_users(Path("rooms/nsfw/.access.yml")))

    # Update SFW users
    for user in all_users:
        if user in nsfw_users:
            continue
        mission_file = Path(allemande_rooms) / user / "mission.m"
        if mission_file.exists():
            source = Path(allemande_home) / "rooms.dist/mission.m.sfw"
            print(f"Updating {user} (SFW)")
            run_command(["cp", "-v", str(source), str(mission_file)])

    # Update NSFW users
    for user in nsfw_users:
        mission_file = Path(allemande_rooms) / user / "mission.m"
        if mission_file.exists():
            source = Path(allemande_home) / "rooms.dist/mission.m.nsfw"
            print(f"Updating {user} (NSFW)")
            run_command(["cp", "-v", str(source), str(mission_file)])


def webchat_user(
    command: str,
    args: list[str],
    nsfw: bool,
    nsfw_filter: str | None,
    istream: TextIO,
    ostream: TextIO,
) -> None:
    """Main dispatcher for webchat user management commands."""
    # Change to webchat directory
    allemande_home = os.environ.get("ALLEMANDE_HOME", ".")
    os.chdir(allemande_home)

    # Source env.sh equivalent - just ensure we're in webchat dir
    os.chdir("webchat")

    if command == "add":
        username = args[0] if args else ""
        contact = args[1] if len(args) > 1 else ""
        add_user(username, contact, nsfw, istream, ostream)

    elif command == "passwd":
        username = args[0] if args else ""
        password = args[1] if len(args) > 1 else ""
        interactive = password == "-i"
        user, pwd = change_password(username, password, interactive)
        if not interactive and not (len(args) > 1 and args[1]):
            ostream.write(f"+ {user} {pwd}\n")

    elif command == "rm":
        username = args[0] if args else ""
        remove_user(username)

    elif command == "off":
        username = args[0] if args else ""
        comment = args[1] if len(args) > 1 else ""
        disable_user(username, comment)

    elif command == "on":
        username = args[0] if args else ""
        enable_user(username)

    elif command == "list":
        filter_str = args[0] if args else ""
        list_users(filter_str, nsfw_filter)

    elif command == "missions":
        update_missions()

    else:
        die(f"Unknown command: {command}\nUsage: webchat-user {{add|passwd|rm|off|on|list|missions}} [args...]")


def setup_args(arg):
    """Set up command-line arguments."""
    arg("command", help="Command to execute: add|passwd|rm|off|on|list|missions")
    arg("args", nargs="*", help="Command arguments")
    arg("--nsfw", action="store_true", help="Enable NSFW for user (add command)")
    arg("-n", "--nsfw-filter", help="Filter users: 1=NSFW only, 0=SFW only")


if __name__ == "__main__":
    main.go(webchat_user, setup_args)
