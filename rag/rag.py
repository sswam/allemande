#!/usr/bin/env python3-allemande

"""
A RAG (Retrieval-Augmented Generation) system using FAISS for similarity search.
"""

from pathlib import Path
from typing import TextIO
from itertools import chain
import re

import faiss
import numpy as np
from tqdm import tqdm

from ally import main, logs  # type: ignore
from ally.lazy import lazy  # type: ignore

# Lazy imports for slow modules
lazy("sentence_transformers", "SentenceTransformer")

__version__ = "0.1.6"

logger = logs.get_logger()


EXTENSION_INDEX = ".index"
EXTENSION_TEXTS = ".texts"


class FaissRAG:
    """FAISS-based retrieval system for text similarity search, supporting multiple DBs."""

    def __init__(self, db_paths: list[str], model: str = "all-mpnet-base-v2"):
        """Initialize the RAG system with a list of DB paths, loading each."""
        self.encoder = SentenceTransformer(model)  # noqa: F821
        self.dimension = self.encoder.get_sentence_embedding_dimension()
        self.db_paths = []
        self.indices = []
        self.texts_list = []
        # Track which DBs need a full Faiss rebuild on save (due to remove/update)
        self._dirty = set()

        for path in db_paths:
            if path.endswith(EXTENSION_INDEX):
                path = path[:-len(EXTENSION_INDEX)]
            self.db_paths.append(path)
            index = faiss.IndexFlatIP(self.dimension)
            texts = []
            if Path(f"{path}{EXTENSION_INDEX}").exists():
                index, texts = self._load(path)
            self.indices.append(index)
            self.texts_list.append(texts)

    def _load(self, path: str) -> tuple:
        """Load index and texts from files, returning (index, texts)."""
        index = faiss.read_index(f"{path}{EXTENSION_INDEX}")
        with open(f"{path}{EXTENSION_TEXTS}", encoding="utf-8") as f:
            texts = f.read().split("\n\n")
        return index, texts

    def _encode(self, text: str) -> np.ndarray | None:
        """Encode and normalize a text, returning None if near-zero norm."""
        embedding = self.encoder.encode([text])[0]
        norm = np.linalg.norm(embedding)
        if norm < 1e-10:
            return None
        return (embedding / norm).astype(np.float32)

    def db_index(self, db_path: str) -> int:
        """Look up a db_path and return its index."""
        if db_path.endswith(EXTENSION_INDEX):
            db_path = db_path[:-len(EXTENSION_INDEX)]
        return self.db_paths.index(db_path)

    def text_index(self, text: str) -> tuple[int, int] | None:
        """Look up a text exactly (linear search), returning (db_index, text_index) or None."""
        for di, texts in enumerate(self.texts_list):
            for ti, t in enumerate(texts):
                if t == text:
                    return (di, ti)
        return None

    def add_entry(self, text: str, db_index: int = 0) -> None:
        """Add a text entry to the specified DB index."""
        if not self.db_paths:
            raise ValueError("No DB paths configured")
        # Ensure no double newlines in entry, as it's the record separator.
        text = re.sub(r"\n\n+", "\n", text)
        vec = self._encode(text)
        if vec is None:
            logger.warning("Near-zero norm vector encountered, skipping entry")
            return
        self.indices[db_index].add(np.array([vec], dtype=np.float32))  # type: ignore # FAISS type hints are incomplete
        self.texts_list[db_index].append(text)

    def remove(self, db_index: int, text_index: int) -> None:
        """Remove a text entry by (db_index, text_index), replacing with '' and marking dirty."""
        self.texts_list[db_index][text_index] = ''
        self._dirty.add(db_index)

    def update(self, db_index: int, text_index: int, new_text: str) -> None:
        """Update a text entry by (db_index, text_index), marking dirty for Faiss rebuild."""
        new_text = re.sub(r"\n\n+", "\n", new_text)
        self.texts_list[db_index][text_index] = new_text
        self._dirty.add(db_index)

    def query_vector(self, question: str) -> np.ndarray | None:
        """Compute normalized query vector, returning None if near-zero norm."""
        return self._encode(question)

    def query_indices_with_vector(self, vec: np.ndarray, db_index: int, k: int) -> list[tuple[float, int, int]]:
        """Search a single DB with a precomputed vector, returning list of (distance, db_index, text_index)."""
        texts = self.texts_list[db_index]
        # Count non-empty texts for capping k
        available = sum(1 for t in texts if t != '')
        k = max(0, min(k, available))
        if k == 0:
            return []
        # We may need to fetch more from faiss if some are removed
        fetch_k = min(len(texts), k + len(self._dirty))
        search_k = max(k, fetch_k)
        distances, faiss_indices = self.indices[db_index].search(np.array([vec], dtype=np.float32), search_k)  # type: ignore # FAISS type hints are incomplete
        results = []
        for dist, idx in zip(distances[0], faiss_indices[0]):
            if idx < 0:
                continue
            if texts[idx] == '':
                continue
            results.append((float(dist), db_index, int(idx)))
            if len(results) >= k:
                break
        return results

    def query_tuple_indices(self, question: str, k: int = 10) -> list[tuple[int, int]]:
        """Find the k most similar texts across all DBs, returning list of (db_index, text_index)."""
        if not self.db_paths:
            return []
        if len(self) == 0:
            return []
        vec = self.query_vector(question)
        if vec is None:
            return []
        # Gather results from all DBs, each with full k
        all_results = []
        for di in range(len(self.db_paths)):
            all_results.extend(self.query_indices_with_vector(vec, di, k))
        # Sort by distance descending (IndexFlatIP uses inner product, higher = more similar)
        all_results.sort(key=lambda x: x[0], reverse=True)
        top = all_results[:k]
        return [(di, ti) for _, di, ti in top]

    def query_indices(self, question: str, k: int = 10) -> list[int]:
        """Find the k most similar texts across all DBs, returning list of (text_index) across all DBs."""
        tuple_indices = self.query_tuple_indices(question, k)
        # Convert (db_index, text_index) tuples to flat indices by summing the lengths
        # of all preceding DBs' text lists, mirroring the logic in __getitem__
        flat_indices = []
        for di, ti in tuple_indices:
            offset = sum(len(self.texts_list[i]) for i in range(di))
            flat_indices.append(offset + ti)
        return flat_indices

    def query(self, question: str, k: int = 10) -> list[str]:
        """Find the k most similar texts across all DBs."""
        tuple_indices = self.query_tuple_indices(question, k)
        return [self.texts_list[di][ti] for di, ti in tuple_indices]

    def save(self, db_index: int | None = None) -> None:
        """Save the index and texts to files. If db_index given, save only that DB."""
        targets = [db_index] if db_index is not None else range(len(self.db_paths))
        for di in targets:
            path = self.db_paths[di]
            texts = self.texts_list[di]
            if di in self._dirty:
                # Full rebuild: exclude removed ('') entries
                new_index = faiss.IndexFlatIP(self.dimension)
                new_texts = []
                for text in texts:
                    if text == '':
                        continue
                    vec = self._encode(text)
                    if vec is None:
                        logger.warning("Near-zero norm vector for text during rebuild, skipping")
                        continue
                    new_index.add(np.array([vec], dtype=np.float32))  # type: ignore # FAISS type hints are incomplete
                    new_texts.append(text)
                self.indices[di] = new_index
                self.texts_list[di] = new_texts
                self._dirty.discard(di)
                texts = new_texts
            faiss.write_index(self.indices[di], f"{path}{EXTENSION_INDEX}")
            with open(f"{path}{EXTENSION_TEXTS}", "w", encoding="utf-8") as f:
                f.write("\n\n".join(texts))

    def load(self, path: str) -> None:
        """Load a DB by path, replacing its current index and texts."""
        di = self.db_index(path)
        self.indices[di], self.texts_list[di] = self._load(self.db_paths[di])

    def __len__(self):
        """Total number of indexed texts across all DBs."""
        return sum(len(t) for t in self.texts_list)

    def __getitem__(self, index):
        """Retrieve texts by numeric index or slice, searching across all DBs in texts_list."""
        if isinstance(index, slice):
            total_len = sum(len(texts) for texts in self.texts_list)
            indices = range(*index.indices(total_len))
            return [self[i] for i in indices]

        # Handle negative indices
        if index < 0:
            total_len = sum(len(texts) for texts in self.texts_list)
            index += total_len

        for texts in self.texts_list:
            if index < len(texts):
                return texts[index]
            index -= len(texts)
        raise IndexError("index out of range")


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
    show_progress: bool = False,
) -> None:
    """Import texts from input stream into the RAG system (into DB 0)."""
    total_lines = 0
    current_text = []

    # Try to count lines first if stream is seekable
    if istream.seekable():
        total_lines = sum(1 for _ in istream)
        istream.seek(0)

    progress_bar: tqdm | None = None
    if show_progress:
        progress_bar = tqdm(total=total_lines if total_lines else None,
                        desc="Importing texts")

    for line in chain(istream, ['']):
        line = line.strip()
        if line:
            current_text.append(line)
        elif current_text:
            text = "\n".join(current_text)
            if text.strip():
                rag.add_entry(text)
                if progress_bar:
                    progress_bar.update(len(current_text) + 1)
            current_text = []
        elif progress_bar:
            progress_bar.update(1)

    if progress_bar:
        progress_bar.close()

    rag.save()


def rag_main(
    istream: TextIO,
    ostream: TextIO,
    db_path: list[str],
    num_results: int = 10,
    do_import: bool = False,
    show_progress: bool = False,
    model: str = "all-mpnet-base-v2",
) -> None:
    """Main function for the RAG system."""
    rag = FaissRAG(db_path, model=model)

    if do_import:
        import_texts(istream, rag, show_progress)
        return

    process_input(istream, ostream, rag, num_results, show_progress)


def setup_args(arg):
    """Set up command-line arguments."""
    arg("db_path", nargs="*", default=["db"], help="path(s) to the FAISS database")
    arg("-n", "--num-results", type=int, default=10, help="number of results to return")
    arg("-i", "--import", help="import text from stdin (delimited by blank lines)", dest="do_import", action="store_true")
    arg("-p", "--progress", help="show progress bar", dest="show_progress", action="store_true")
    arg("-m", "--model", default="all-mpnet-base-v2", help="sentence transformer model (e.g., all-mpnet-base-v2, all-MiniLM-L6-v2, all-distilroberta-v1)")


if __name__ == "__main__":
    main.go(rag_main, setup_args)
