#!/usr/bin/env python3-allemande
"""
Vector database management using Faiss and sentence-transformers.
Allows adding, removing, searching and listing vectors from text.
"""

import logging
import pickle
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator
import argparse

from sentence_transformers import SentenceTransformer
import numpy as np
import faiss


logger = logging.getLogger(__name__)


@dataclass
class VectorDB:
    """Wrapper for Faiss index and metadata"""

    index: faiss.Index  # type: ignore
    texts: list[str]
    embedding_size: int


def create_db(embedding_size: int = 384) -> VectorDB:
    """Create a new empty vector database"""
    index = faiss.IndexFlatL2(embedding_size)  # type: ignore
    return VectorDB(index=index, texts=[], embedding_size=embedding_size)


def load_db(path: Path) -> VectorDB:
    """Load vector database from disk"""
    with open(path, "rb") as f:
        return pickle.load(f)


def save_db(db: VectorDB, path: Path) -> None:
    """Save vector database to disk"""
    with open(path, "wb") as f:
        pickle.dump(db, f)


def get_embeddings(model: SentenceTransformer, texts: list[str]) -> np.ndarray:
    """Generate embeddings for a list of texts"""
    if not texts:
        return np.array([], dtype=np.float32).reshape(0, model.get_sentence_embedding_dimension())
    return model.encode(texts, normalize_embeddings=True)


def add_texts(db: VectorDB, texts: list[str], model: SentenceTransformer) -> None:
    """Add texts to the database"""
    embeddings = get_embeddings(model, texts)
    db.index.add(embeddings)
    db.texts.extend(texts)


def remove_texts(db: VectorDB, indices: list[int], model: SentenceTransformer) -> None:
    """Remove texts at given indices from database"""
    # Faiss doesn't support direct removal, so we rebuild the index
    remaining_texts = [t for i, t in enumerate(db.texts) if i not in indices]
    if not remaining_texts:
        db.index.reset()
        db.texts = []
        return

    embeddings = get_embeddings(model, remaining_texts)

    new_index = faiss.IndexFlatL2(db.embedding_size)
    new_index.add(embeddings)

    db.index = new_index
    db.texts = remaining_texts


def search_similar(db: VectorDB, query: str, k: int, model: SentenceTransformer) -> list[tuple[int, float, str]]:
    """Search for k most similar texts to query"""
    query_embedding = get_embeddings(model, [query])
    distances, indices = db.index.search(query_embedding, k)

    results = []
    for idx, dist in zip(indices[0], distances[0]):
        if idx != -1:  # Faiss returns -1 for not enough results
            results.append((idx, float(dist), db.texts[idx]))
    return results


def split_file_texts(file_paths: list[Path], delimiter: str = "\n\n") -> Iterator[str]:
    """Read and split texts from files"""
    for path in file_paths:
        text = path.read_text()
        yield from (t.strip() for t in text.split(delimiter) if t.strip())


def cli_add(db: VectorDB, texts: list[str], model: SentenceTransformer) -> None:
    """CLI handler for adding texts"""
    add_texts(db, texts, model)
    print(f"Added {len(texts)} texts to database")


def cli_remove(db: VectorDB, indices: list[int], model: SentenceTransformer) -> None:
    """CLI handler for removing texts"""
    remove_texts(db, indices, model)
    print(f"Removed texts at indices {indices}")


def cli_search(db: VectorDB, query: str, k: int, model: SentenceTransformer) -> None:
    """CLI handler for searching"""
    results = search_similar(db, query, k, model)
    for idx, dist, text in results:
        print(f"\nIndex: {idx}, Distance: {dist:.4f}")
        print(f"Text: {text}")


def cli_list(db: VectorDB) -> None:
    """CLI handler for listing all texts"""
    for idx, text in enumerate(db.texts):
        print(f"\nIndex: {idx}")
        print(f"Text: {text}")


def cli_index_files(db: VectorDB, file_paths: list[Path], delimiter: str, model: SentenceTransformer) -> None:
    """CLI handler for indexing files"""
    texts = list(split_file_texts(file_paths, delimiter))
    add_texts(db, texts, model)
    print(f"Indexed {len(texts)} texts from {len(file_paths)} files")


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", type=Path, required=True, help="Path to vector database file")

    subparsers = parser.add_subparsers(dest="command", required=True)

    # Add command
    add_parser = subparsers.add_parser("add", help="Add texts to database")
    add_parser.add_argument("texts", nargs="+", help="Texts to add")

    # Remove command
    remove_parser = subparsers.add_parser("remove", help="Remove texts by index")
    remove_parser.add_argument("indices", type=int, nargs="+", help="Indices to remove")

    # Search command
    search_parser = subparsers.add_parser("search", help="Search for similar texts")
    search_parser.add_argument("query", help="Query text")
    search_parser.add_argument("-k", type=int, default=5, help="Number of results")

    # List command
    subparsers.add_parser("list", help="List all texts")

    # Index command
    index_parser = subparsers.add_parser("index", help="Index texts from files")
    index_parser.add_argument("files", type=Path, nargs="+", help="Files to index")
    index_parser.add_argument("--delimiter", default="\n\n", help="Text delimiter")

    args = parser.parse_args()

    # Load or create database
    if args.db.exists():
        db = load_db(args.db)
    else:
        db = create_db()

    # Initialize model once
    model = SentenceTransformer("all-MiniLM-L6-v2")

    try:
        if args.command == "add":
            cli_add(db, args.texts, model)
        elif args.command == "remove":
            cli_remove(db, args.indices, model)
        elif args.command == "search":
            cli_search(db, args.query, args.k, model)
        elif args.command == "list":
            cli_list(db)
        elif args.command == "index":
            cli_index_files(db, args.files, args.delimiter, model)
    finally:
        save_db(db, args.db)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
