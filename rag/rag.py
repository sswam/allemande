import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

class FaissRAG:
    def __init__(self):
        self.encoder = SentenceTransformer('all-MiniLM-L6-v2')
        self.dimension = 384  # Output dim for this model
        self.index = faiss.IndexFlatL2(self.dimension)
        self.texts = []

    def add_entry(self, text: str) -> None:
        embedding = self.encoder.encode([text])[0]
        self.index.add(np.array([embedding]).astype('float32'))
        self.texts.append(text)

    def query(self, question: str, k: int = 3) -> list[str]:
        query_vector = self.encoder.encode([question])[0]
        distances, indices = self.index.search(
            np.array([query_vector]).astype('float32'), k
        )
        return [self.texts[i] for i in indices[0]]

# Usage example
rag = FaissRAG()
rag.add_entry("Python is a popular programming language")
results = rag.query("What programming languages are popular?")
