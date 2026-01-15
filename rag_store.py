# rag_store.py
import re
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer


class ResumeRAGStore:
    """
    Simple in-memory FAISS-based RAG store
    """

    def __init__(self):
        self.embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
        self.index = None
        self.chunks = []

    def _chunk_text(self, text: str, chunk_size=400, overlap=80):
        words = text.split()
        chunks = []
        i = 0

        while i < len(words):
            chunk = words[i : i + chunk_size]
            chunks.append(" ".join(chunk))
            i += chunk_size - overlap

        return chunks

    def build_index(self, document_text: str):
        if not document_text.strip():
            return

        clean_text = re.sub(r"\s+", " ", document_text)
        self.chunks = self._chunk_text(clean_text)

        embeddings = self.embedding_model.encode(self.chunks)
        embeddings = np.array(embeddings).astype("float32")

        self.index = faiss.IndexFlatL2(embeddings.shape[1])
        self.index.add(embeddings)

    def retrieve(self, query: str, top_k: int = 5) -> str:
        if self.index is None:
            return ""

        query_embedding = self.embedding_model.encode([query]).astype("float32")
        _, indices = self.index.search(query_embedding, top_k)

        retrieved_chunks = [self.chunks[i] for i in indices[0]]
        return "\n\n".join(retrieved_chunks)
