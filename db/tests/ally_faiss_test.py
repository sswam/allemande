import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer

from db import ally_faiss as subject

subject_name = subject.__name__

@pytest.fixture
def empty_db():
    return subject.create_db(3)  # Match mock model dimension

@pytest.fixture
def mock_model():
    model = MagicMock(spec=SentenceTransformer)
    def encode_side_effect(texts, normalize_embeddings=True):
        # Return one vector per input text, or empty array if no texts
        if not texts:
            return np.array([], dtype=np.float32).reshape(0, 3)
        return np.array([[1, 0, 0]] * len(texts), dtype=np.float32)
    model.encode.side_effect = encode_side_effect
    model.get_sentence_embedding_dimension.return_value = 3
    return model

def test_create_db():
    db = subject.create_db(384)
    assert isinstance(db.index, faiss.Index)
    assert db.texts == []
    assert db.embedding_size == 384

def test_save_load_db(tmp_path, empty_db):
    db_path = tmp_path / "test.db"
    subject.save_db(empty_db, db_path)
    loaded_db = subject.load_db(db_path)
    assert loaded_db.embedding_size == empty_db.embedding_size
    assert loaded_db.texts == empty_db.texts

def test_add_texts(empty_db, mock_model):
    texts = ["hello", "world"]
    subject.add_texts(empty_db, texts, mock_model)
    assert empty_db.texts == texts
    assert empty_db.index.ntotal == 2

def test_add_empty_texts(empty_db, mock_model):
    subject.add_texts(empty_db, [], mock_model)
    assert empty_db.texts == []
    assert empty_db.index.ntotal == 0

def test_remove_texts(empty_db, mock_model):
    # First add some texts
    texts = ["one", "two", "three"]
    subject.add_texts(empty_db, texts, mock_model)

    # Remove middle text
    subject.remove_texts(empty_db, [1], mock_model)
    assert empty_db.texts == ["one", "three"]
    assert empty_db.index.ntotal == 2

def test_remove_all_texts(empty_db, mock_model):
    texts = ["one", "two"]
    subject.add_texts(empty_db, texts, mock_model)
    subject.remove_texts(empty_db, [0, 1], mock_model)
    assert empty_db.texts == []
    assert empty_db.index.ntotal == 0

def test_search_similar(empty_db, mock_model):
    texts = ["one", "two", "three"]
    subject.add_texts(empty_db, texts, mock_model)

    # Mock index.search to return proper numpy types
    def mock_search(query, k):
        return (
            np.array([[0.0, 1.0]]),  # distances
            np.array([[0, 1]], dtype=np.int64)  # indices
        )
    empty_db.index.search = mock_search

    results = subject.search_similar(empty_db, "query", 2, mock_model)
    assert len(results) == 2
    # Fix type assertions to handle numpy types
    assert all(isinstance(int(r[0]), int) for r in results)  # Check indices
    assert all(isinstance(float(r[1]), float) for r in results)  # Check distances
    assert all(isinstance(r[2], str) for r in results)  # Check texts

def test_search_empty_db(empty_db, mock_model):
    results = subject.search_similar(empty_db, "query", 5, mock_model)
    assert results == []

def test_split_file_texts(tmp_path):
    test_file = tmp_path / "test.txt"
    test_file.write_text("First paragraph\n\nSecond paragraph\n\nThird paragraph")

    texts = list(subject.split_file_texts([test_file]))
    assert texts == ["First paragraph", "Second paragraph", "Third paragraph"]

def test_split_file_texts_empty(tmp_path):
    test_file = tmp_path / "empty.txt"
    test_file.write_text("")

    texts = list(subject.split_file_texts([test_file]))
    assert texts == []

@patch('sys.stdout')
def test_cli_list(mock_stdout, empty_db, mock_model):
    texts = ["one", "two"]
    subject.add_texts(empty_db, texts, mock_model)  # Actually add texts before listing
    subject.cli_list(empty_db)
    mock_stdout.write.assert_called()

@patch('sys.stdout')
def test_cli_list_empty(mock_stdout, empty_db):
    subject.cli_list(empty_db)
    assert mock_stdout.write.call_count == 0

def test_main_error_handling():
    with pytest.raises(SystemExit):
        with patch('sys.argv', ['vectordb.py']):
            subject.main()

if __name__ == '__main__':
    pytest.main([__file__])
