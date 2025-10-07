#!/usr/bin/env python3-allemande

"""
A RAG (Retrieval-Augmented Generation) system using FAISS for similarity search.
"""

import sys
from pathlib import Path
from typing import TextIO

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

from ally import main, logs  # type: ignore

__version__ = "0.1.0"

logger = logs.get_logger()


class FaissRAG:
    """FAISS-based retrieval system for text similarity search."""

    def __init__(self, db_path: str | None = None):
        """Initialize the RAG system, optionally loading from a database file."""
        self.encoder = SentenceTransformer('all-MiniLM-L6-v2')
        self.dimension = self.encoder.get_sentence_embedding_dimension()
        self.index = faiss.IndexFlatIP(self.dimension)  # Changed to Inner Product
        self.texts = []

        if db_path and Path(db_path).exists():
            self.load(db_path)

    def add_entry(self, text: str) -> None:
        """Add a text entry to the index."""
        embedding = self.encoder.encode([text])[0]
        # Normalize the embedding vector
        normalized = embedding / np.linalg.norm(embedding)
        self.index.add(np.array([normalized]).astype('float32'))
        self.texts.append(text)

    def query(self, question: str, k: int = 3) -> list[str]:
        """Find the k most similar texts to the query."""
        if not self.texts:
            return []

        k = min(k, len(self.texts))
        query_vector = self.encoder.encode([question])[0]
        # Normalize the query vector
        normalized = query_vector / np.linalg.norm(query_vector)
        distances, indices = self.index.search(
            np.array([normalized]).astype('float32'), k
        )
        return [self.texts[i] for i in indices[0] if i >= 0]

    def save(self, path: str) -> None:
        """Save the index and texts to files."""
        faiss.write_index(self.index, f"{path}.index")
        with open(f"{path}.texts", "w", encoding="utf-8") as f:
            f.write("\n\n".join(self.texts))

    def load(self, path: str) -> None:
        """Load the index and texts from files."""
        self.index = faiss.read_index(f"{path}.index")
        with open(f"{path}.texts", encoding="utf-8") as f:
            self.texts = f.read().split("\n\n")


def process_input(istream: TextIO, ostream: TextIO, rag: FaissRAG, num_results: int) -> None:
    """Process queries from input stream and write results to output stream."""
    for query in istream:
        query = query.strip()
        if not query:
            continue

        results = rag.query(query, k=num_results)
        ostream.write("\n\n".join(results))
        ostream.write("\n\n")


def rag_main(
    istream: TextIO,
    ostream: TextIO,
    db_path: str = "db.faiss",
    num_results: int = 3,
    import_file: str | None = None,
) -> None:
    """Main function for the RAG system."""
    rag = FaissRAG(db_path)

    if import_file:
        with open(import_file, encoding="utf-8") as f:
            texts = f.read().split("\n\n")
            for text in texts:
                if text.strip():
                    rag.add_entry(text.strip())
        rag.save(db_path)
        return

    process_input(istream, ostream, rag, num_results)


def setup_args(arg):
    """Set up command-line arguments."""
    arg("db_path", nargs="?", default="db.faiss", help="path to the FAISS database")
    arg("-n", "--num-results", type=int, default=3, help="number of results to return")
    arg("-i", "--import-file", help="import text from file (delimited by blank lines)")


if __name__ == "__main__":
    main.go(rag_main, setup_args)
