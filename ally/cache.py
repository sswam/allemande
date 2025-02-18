"""
Cache module providing file loading and saving with modification tracking.
"""

import csv
import json
import logging
import os
from typing import Any

import yaml


__VERSION__ = "0.1.5"


logger = logging.getLogger(__name__)


class FileCache:
    """Loads and saves file content with modification tracking."""

    def __init__(self):
        self._last_modified: dict[str, float] = {}
        self._cache: dict[str, Any] = {}

    def load(self, path: str, fmt: str | None = None, **kwargs) -> Any:
        """
        Loads and caches content from a file, reloading only if modified.

        Args:
            path: Path to the file or module name
            fmt: Format type ('text', 'json', 'yaml', 'csv')
            **kwargs: Additional arguments (e.g., delimiter for CSV)

        Returns:
            Loaded content
        """
        if not os.path.exists(path):
            logger.error("File not found: %s", path)
            return None

        if fmt is None:
            _, ext = os.path.splitext(path)
            fmt = ext.lstrip(".").lower()

        current_mtime = os.path.getmtime(path)
        if current_mtime <= self._last_modified.get(path, 0):
            return self._cache[path]

        content = self._load_file(path, fmt, **kwargs)
        self._cache[path] = content
        self._last_modified[path] = current_mtime
        return content

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
            fmt = ext.lstrip(".").lower()

        if os.path.exists(path):
            current_mtime = os.path.getmtime(path)
            if noclobber and current_mtime > self._last_modified.get(path, 0):
                raise FileExistsError(f"File {path} has been modified externally")

        if path in self._cache and self._deep_compare(self._cache[path], content):
            return

        self._save_file(path, content, fmt, **kwargs)
        self._cache[path] = content
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
        with open(path, "w", encoding="utf-8") as file:
            if fmt == "txt":
                file.write(str(content))
            elif fmt == "json":
                json.dump(content, file, **kwargs)
            elif fmt in ["yaml", "yml"]:
                yaml.safe_dump(content, file, **kwargs)
            elif fmt in ["csv", "tsv"]:
                delimiter = "\t" if fmt == "tsv" else kwargs.get("delimiter", ",")
                writer = csv.writer(file, delimiter=delimiter)
                writer.writerows(content)
            else:
                raise ValueError(f"Unsupported format: {fmt}")

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
            return
        self._cache.pop(path, None)
        self._last_modified.pop(path, None)


cache = FileCache()
