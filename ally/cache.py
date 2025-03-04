"""
Cache module providing file loading and saving with modification tracking.
"""

import csv
import json
import logging
import os
from typing import Any
import time
from copy import deepcopy
import io

import yaml


__VERSION__ = "0.1.6"


logger = logging.getLogger(__name__)


class FileCache:
    """Loads and saves file content with modification tracking."""

    def __init__(self):
        self._last_modified: dict[str, float] = {}
        self._last_check_time: dict[str, float] = {}
        self._cache: dict[str, Any] = {}

    def load(self, path: str, fmt: str | None = None, no_stat_time_s: float | None = 1, **kwargs) -> Any:
        """
        Loads and caches content from a file, reloading only if modified.

        Args:
            path: Path to the file or module name
            fmt: Format type ('text', 'json', 'yaml', 'csv')
            no_stat_time_s: If set, skip stat checks if last check was within this many seconds
            **kwargs: Additional arguments (e.g., delimiter for CSV)

        Returns:
            Loaded content
        """
        current_time = time.time()

        # If we have a recent check and no_stat_time_s is set, return cached content
        if no_stat_time_s is not None and current_time - self._last_check_time.get(path, 0) < no_stat_time_s:
            return deepcopy(self._cache.get(path))

        # Store the check time
        self._last_check_time[path] = current_time

        if not os.path.exists(path):
            logger.error("File not found: %s", path)
            return None

        if fmt is None:
            _, ext = os.path.splitext(path)
            fmt = ext.lstrip(".").lower() or "txt"

        current_mtime = os.path.getmtime(path)
        if current_mtime <= self._last_modified.get(path, 0):
            content = self._cache[path]
            return deepcopy(self._cache[path])

        content = self._load_file(path, fmt, **kwargs)
        self._cache[path] = content
        self._last_modified[path] = current_mtime
        return deepcopy(content)

    def save(self, path: str, content: Any, fmt: str | None = None, noclobber: bool = True, **kwargs):
        """
        Saves content to a file, only writing if content has changed.

        Args:
            path: Path to save the file
            content: Content to save
            fmt: Format type ('json', 'yaml', 'txt', etc)
            noclobber: If True, refuse to save if file was externally modified
            **kwargs: Additional arguments for specific formats
        """
        if fmt is None:
            _, ext = os.path.splitext(path)
            fmt = ext.lstrip(".").lower() or "txt"

        if os.path.exists(path):
            current_mtime = os.path.getmtime(path)
            if noclobber and current_mtime > self._last_modified.get(path, 0):
                raise FileExistsError(f"File {path} has been modified externally")

        if path in self._cache and self._deep_compare(self._cache[path], content):
            logger.debug("Content is identical (1st check), skipping save")
            return

        if not self._save_file(path, content, fmt, **kwargs):
            logger.debug("Content is identical (2nd check), skipping save")
            return
        self._cache[path] = deepcopy(content)
        self._last_modified[path] = os.path.getmtime(path)
        logger.info("Saved %s file: %s", fmt, path)

    def _load_file(self, path: str, fmt: str, **kwargs) -> Any:
        """Load file content based on format"""
        with open(path, "r", encoding="utf-8") as file:
            if fmt == "txt":
                return file.read()
            if fmt == "json":
                return json.load(file)
            if fmt in ["yaml", "yml"]:
                return yaml.safe_load(file)
            if fmt == "tsv":
                return list(csv.reader(file, delimiter="\t"))
            if fmt == "csv":
                delimiter = kwargs.get("delimiter", ",")
                return list(csv.reader(file, delimiter=delimiter))
            raise ValueError(f"Unsupported format: {fmt}")

    def _save_file(self, path: str, content: Any, fmt: str, **kwargs):
        """Save content to file based on format"""
        # First format the content to string based on format
        formatted_content = ""
        if fmt in ["txt", "md", "html"]:
            formatted_content = str(content)
        elif fmt == "json":
            formatted_content = json.dumps(content, **kwargs)
        elif fmt in ["yaml", "yml"]:
            formatted_content = yaml.safe_dump(content, **kwargs)
        elif fmt in ["csv", "tsv"]:
            output = io.StringIO()
            delimiter = "\t" if fmt == "tsv" else kwargs.get("delimiter", ",")
            writer = csv.writer(output, delimiter=delimiter)
            writer.writerows(content)
            formatted_content = output.getvalue()
            output.close()
        else:
            raise ValueError(f"Unsupported format: {fmt}")

        # Remove existing symlink
        if os.path.islink(path):
            os.remove(path)

        # Check if file exists and compare contents
        try:
            with open(path, "r", encoding="utf-8") as file:
                current_content = file.read()
                if current_content == formatted_content:
                    return False  # Content is identical, no need to write
        except FileNotFoundError:
            current_content = None

        # Write to file if content is different or file doesn't exist
        with open(path, "w", encoding="utf-8") as file:
            file.write(formatted_content)

        return True

    def _deep_compare(self, a: Any, b: Any) -> bool:
        """Compare two values recursively for equality"""
        if not isinstance(a, type(b)) or not isinstance(b, type(a)):
            return False
        if isinstance(a, (list, tuple)):
            return len(a) == len(b) and all(self._deep_compare(x, y) for x, y in zip(a, b))
        if isinstance(a, dict):
            return len(a) == len(b) and all(k in b and self._deep_compare(v, b[k]) for k, v in a.items())
        return a == b

    def clear(self, path: str | None = None):
        """
        Clear the cache for a specific path or all cached items.

        Args:
            path: Specific path to clear, or None for all
        """
        if path is None:
            self._cache.clear()
            self._last_modified.clear()
            self._last_check_time.clear()
            return
        self._cache.pop(path, None)
        self._last_modified.pop(path, None)
        self._last_check_time.pop(path, None)

    def symlink(self, src: str, dst: str):
        """
        Create a symbolic link from source to destination.
        If destination exists and is a link to the source, do nothing.

        Args:
            src: Source path
            dst: Destination path
        """
        if os.path.lexists(dst):
            # read the link, check same
            if os.path.islink(dst) and os.readlink(dst) == src:
                return
            os.remove(dst)
        os.symlink(src, dst)

    def chmod(self, path: str, mode: int):
        """
        Change the mode of a file.
        If the file already has the specified mode, do nothing.
        """
        if os.path.exists(path) and os.stat(path).st_mode == mode:
            return
        os.chmod(path, mode)

    def remove(self, path: str):
        """
        Remove a file or symlink.
        Also remove it from the cache.
        """
        try:
            os.remove(path)
        except FileNotFoundError:
            pass
        self.clear(path)

cache = FileCache()
