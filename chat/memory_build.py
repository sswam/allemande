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


def memory_build(folder: str, agent: str, timestamps: bool=False) -> None:
    """Build a FAISS memory index from all *.<agent>.s files in the folder."""
    agent = agent.lower()
    folder_path = Path(folder)
    db_path = str(folder_path / agent)

    # Remove existing DB files, ignoring missing ones
    for ext in (rag.EXTENSION_TEXTS, rag.EXTENSION_INDEX):
        p = Path(f"{db_path}{ext}")
        if p.exists():
            p.unlink()

    # Find all matching files directly in folder (not recursive), sorted by mtime
    summary_files = list(folder_path.glob(f"*.{agent}.s"))

    # For each summary file, find the corresponding chat (.bb) file by stripping .{agent}.s and adding .bb
    # Then copy the mtime timestamp (only) from the .bb file to the summary file
    for summary_file in summary_files:
        # Strip .{agent}.s suffix and add .bb to get the corresponding chat file
        base_name = summary_file.name[: -(len(f".{agent}.s"))]
        chat_file = folder_path / f"{base_name}.bb"

        if not chat_file.exists():
            logger.warning("Chat file does not exist, cannot copy mtime: %s", chat_file)
            continue

        # Get the mtime from the chat file
        chat_mtime = chat_file.stat().st_mtime
        old_atime = summary_file.stat().st_atime
        # Copy the mtime to the summary file (atime is preserved)
        os.utime(summary_file, (old_atime, chat_mtime))

    summary_files.sort(key=lambda p: p.stat().st_mtime)

    logger.info("Building memory index from %d summary files in %s", len(summary_files), folder)

    faiss_rag = rag.FaissRAG([db_path])
    for f in summary_files:
        logger.debug("Adding entry from %s", f.name)
        faiss_rag.add_entry(f.read_text(encoding="utf-8"))

    faiss_rag.save()
    logger.info("Saved memory index to %s", db_path)


def setup_args(arg):
    """Set up command-line arguments."""
    arg("folder", help="folder containing conversation files")
    arg("agent", help="agent name, selects files matching *.<agent>.s")
    arg("-t", "--timestamps", action="store_true", help="update timestamps on summary files from chat files")


if __name__ == "__main__":
    main.go(memory_build, setup_args)
