#!/usr/bin/env python3-allemande

"""
Builds agent memory indexes from conversation files using FAISS RAG.
"""

import os
from pathlib import Path
from typing import TextIO

from ally import main, logs  # type: ignore
import rag

os.environ["HF_HUB_OFFLINE"] = "1"

__version__ = "0.1.0"

logger = logs.get_logger()


def memory_build(folder: str, agent: str) -> None:
    """Build a FAISS memory index from all *.<agent>.s files in the folder."""
    folder_path = Path(folder)
    db_path = str(folder_path / agent)

    # Remove existing DB files, ignoring missing ones
    for ext in (rag.EXTENSION_TEXTS, rag.EXTENSION_INDEX):
        p = Path(f"{db_path}{ext}")
        if p.exists():
            p.unlink()

    # Find all matching files directly in folder (not recursive), sorted by mtime
    files = list(folder_path.glob(f"*.{agent}.s"))
    files.sort(key=lambda p: p.stat().st_mtime)

    logger.info("Building memory index from %d files in %s", len(files), folder)

    faiss_rag = rag.FaissRAG([db_path])
    for f in files:
        logger.debug("Adding entry from %s", f.name)
        faiss_rag.add_entry(f.read_text(encoding="utf-8"))

    faiss_rag.save(db_path)
    logger.info("Saved memory index to %s", db_path)


def setup_args(arg):
    """Set up command-line arguments."""
    arg("folder", help="folder containing conversation files")
    arg("agent", help="agent name, selects files matching *.<agent>.s")


if __name__ == "__main__":
    main.go(memory_build, setup_args)
