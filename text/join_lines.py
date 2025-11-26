#!/usr/bin/env python3
"""
join_lines - join separate files back into a single file

Reads files from current directory and joins them with a separator.
If a template file is provided, preserves original order and updates content.
"""

import sys
import re
# import logging # Removed unused import
from pathlib import Path
from typing import TextIO

from ally import main, logs  # type: ignore

__version__ = "0.1.4"

logger = logs.get_logger()


def join_lines(
    output: TextIO,
    template: str | None = None,
    separator: str = ":\t",
    extension: str = "",
    ignore_new: bool = False,
) -> None:
    """Join files back into a single file with separator."""

    # Find all files matching the extension pattern
    base_ext = extension.lstrip('.') if extension else None
    if extension and not extension.startswith('.'):
        pattern = f"*{base_ext}"
        ext_to_strip = base_ext
    else:
        pattern = f"*{extension}" if extension else "*"
        ext_to_strip = extension
    all_files = {}
    for f in Path('.').glob(pattern):
        if f.is_file() and (template is None or f.name != template):
            name = f.name
            if ext_to_strip and name.endswith(ext_to_strip):
                identifier = name[:-len(ext_to_strip)]
                if not identifier:
                    logger.warning("Empty identifier for file %s, skipping", f)
                    continue
                all_files[identifier] = f
            elif not extension:
                identifier = name
                all_files[identifier] = f

    identifiers_in_order = []
    existing_identifiers = set()

    # If template exists, extract identifiers and preserve order
    if template:
        template_path = Path(template)
        try:
            template_content = template_path.read_text(encoding='utf-8')
        except UnicodeDecodeError:
            logger.error("Template file %s contains binary content, exiting", template)
            sys.exit(1)
        pattern_regex = re.compile(re.escape(separator))
        for line in template_content.splitlines():
            if not line.strip():
                continue  # skip empty lines
            match = pattern_regex.split(line, 1)
            if len(match) == 2:
                identifier = match[0].strip()  # strip whitespace
                if identifier:  # skip empty identifiers
                    identifiers_in_order.append(identifier)
                    existing_identifiers.add(identifier)

    logger.warning("All files: %r", all_files)

    # Process files in order
    for identifier in identifiers_in_order:
        if identifier not in all_files:
            logger.warning("Missing file for identifier: %s", identifier)
            continue
        try:
            content = all_files[identifier].read_text(encoding='utf-8').rstrip('\n')
        except UnicodeDecodeError:
            logger.warning("Skipping binary file for identifier: %s", identifier)
            continue
        output.write(f"{identifier}{separator}{content}\n")

    # Handle new files not in template
    new_files = set(all_files.keys()) - existing_identifiers
    if new_files:
        if ignore_new:
            logger.warning("Ignoring %d new files: %s",
                        len(new_files), ', '.join(sorted(new_files)))
        else:
            for identifier in sorted(new_files):
                try:
                    content = all_files[identifier].read_text(encoding='utf-8').rstrip('\n')
                except UnicodeDecodeError:
                    logger.warning("Skipping binary file for identifier: %s", identifier)
                    continue
                output.write(f"{identifier}{separator}{content}\n")
            logger.info("Appended %d new files", len(new_files))


def setup_args(arg):
    """Set up command-line arguments."""
    arg('--template', '-t', help='template file to preserve order')
    arg('--separator', '-s', default=':\t',
        help='separator string for joining (default: ":\\t")')
    arg('--extension', '-x', default='',
        help='file extension to strip from identifiers (default: none)')
    arg('--ignore-new', action='store_true',
        help='ignore new files not in template')
    arg('--output', '-o', type=main.argparse.FileType('w'),
        default=sys.stdout, help='output file (default: stdout)')


if __name__ == '__main__':
    main.go(join_lines, setup_args)
