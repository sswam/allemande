#!/usr/bin/env python3-allemande

"""
A RAG (Retrieval-Augmented Generation) system using FAISS for similarity search.
"""

from pathlib import Path
from typing import TextIO
from itertools import chain

import faiss
import numpy as np
from tqdm import tqdm

from ally import main, logs  # type: ignore
from ally.lazy import lazy  # type: ignore

# Lazy imports for slow modules
lazy("sentence_transformers", "SentenceTransformer")

__version__ = "0.1.4"

logger = logs.get_logger()


EXTENSION_INDEX = ".index"
EXTENSION_TEXTS = ".texts"


class FaissRAG:
    """FAISS-based retrieval system for text similarity search."""

    def __init__(self, db_path: str | None = None):
        """Initialize the RAG system, optionally loading from a database file."""
        self.encoder = SentenceTransformer('all-MiniLM-L6-v2')
        self.dimension = self.encoder.get_sentence_embedding_dimension()
        self.index = faiss.IndexFlatIP(self.dimension)
        self.texts = []

        if db_path and db_path.endswith(EXTENSION_INDEX):
            db_path = db_path[:-len(EXTENSION_INDEX)]
        if db_path and Path(f"{db_path}{EXTENSION_INDEX}").exists():
            self.load(db_path)

    def add_entry(self, text: str) -> None:
        """Add a text entry to the index."""
        embedding = self.encoder.encode([text])[0]
        norm = np.linalg.norm(embedding)
        if norm < 1e-10:  # Protect against zero-norm vectors
            logger.warning("Near-zero norm vector encountered, skipping entry")
            return
        normalized = embedding / norm
        # Convert to correct shape and type for FAISS
        vector = np.array([normalized], dtype=np.float32)
        self.index.add(vector)  # type: ignore # FAISS type hints are incomplete
        self.texts.append(text)

    def query(self, question: str, k: int = 10) -> list[str]:
        """Find the k most similar texts to the query."""
        if not self.texts:
            return []

        k = max(0, min(k, len(self.texts)))  # Ensure k is between 0 and len(texts)
        if k == 0:
            return []
        query_vector = self.encoder.encode([question])[0]
        norm = np.linalg.norm(query_vector)
        if norm < 1e-10:
            return []
        normalized = query_vector / norm
        vector = np.array([normalized], dtype=np.float32)
        # FAISS search returns (distances, indices)
        distances, indices = self.index.search(vector, k)  # type: ignore # FAISS type hints are incomplete
        return [self.texts[i] for i in indices[0] if i >= 0]

    def save(self, path: str) -> None:
        """Save the index and texts to files."""
        faiss.write_index(self.index, f"{path}{EXTENSION_INDEX}")
        with open(f"{path}{EXTENSION_TEXTS}", "w", encoding="utf-8") as f:
            f.write("\n\n".join(self.texts))

    def load(self, path: str) -> None:
        """Load the index and texts from files."""
        self.index = faiss.read_index(f"{path}{EXTENSION_INDEX}")
        with open(f"{path}{EXTENSION_TEXTS}", encoding="utf-8") as f:
            self.texts = f.read().split("\n\n")


def process_input(istream: TextIO, ostream: TextIO, rag: FaissRAG, num_results: int, show_progress: bool) -> None:
    """Process queries from input stream and write results to output stream."""
    for query in istream:
        query = query.strip()
        if not query:
            continue
        results = rag.query(query, k=num_results)
        ostream.write("\n\n".join(results))
        ostream.write("\n\n")


def import_texts(
    istream: TextIO,
    rag: 'FaissRAG',
    db_path: str,
    show_progress: bool = False,
) -> None:
    """Import texts from input stream into the RAG system."""
    total_lines = 0
    current_text = []

    # Try to count lines first if stream is seekable
    if istream.seekable():
        total_lines = sum(1 for _ in istream)
        istream.seek(0)

    progress_bar = None
    if show_progress:
        progress_bar = tqdm(total=total_lines if total_lines else None,
                        desc="Importing texts")

    for line in chain(istream, ['']):
        line = line.strip()
        if line:
            current_text.append(line)
        elif current_text:
            text = " ".join(current_text)
            if text.strip():
                rag.add_entry(text)
                if show_progress:
                    progress_bar.update(len(current_text) + 1)
            current_text = []
        elif show_progress:
            progress_bar.update(1)

    if show_progress:
        progress_bar.close()

    rag.save(db_path)


def rag_main(
    istream: TextIO,
    ostream: TextIO,
    db_path: str = "db",
    num_results: int = 10,
    do_import: bool = False,
    show_progress: bool = False,
) -> None:
    """Main function for the RAG system."""
    rag = FaissRAG(db_path)

    if do_import:
        import_texts(istream, rag, db_path, show_progress)
        return

    process_input(istream, ostream, rag, num_results, show_progress)


def setup_args(arg):
    """Set up command-line arguments."""
    arg("db_path", nargs="?", default="db", help="path to the FAISS database")
    arg("-n", "--num-results", type=int, default=10, help="number of results to return")
    arg("-i", "--import", help="import text from stdin (delimited by blank lines)", dest="do_import", action="store_true")
    arg("-p", "--progress", help="show progress bar", dest="show_progress", action="store_true")


if __name__ == "__main__":
    main.go(rag_main, setup_args)
