import os
import chromadb
from chromadb.api.types import EmbeddingFunction, Documents, Embeddings
from shared.utils.logging import get_logger

logger = get_logger(__name__)

class HashEmbeddingFunction(EmbeddingFunction):
    """
    A lightweight, zero-dependency fallback embedding function.
    Generates a deterministic 128-dimensional vector from word hashes.
    Useful when network issues prevent downloading ML models.
    """
    def __call__(self, input: Documents) -> Embeddings:
        embeddings = []
        for text in input:
            vector = [0.0] * 128
            words = text.lower().split()
            if not words:
                embeddings.append(vector)
                continue
            for word in words:
                # Use a simple deterministic hash function
                h = abs(hash(word)) % 128
                vector[h] += 1.0
            # Normalize the vector
            norm = sum(x**2 for x in vector)**0.5
            if norm > 0:
                vector = [x / norm for x in vector]
            embeddings.append(vector)
        return embeddings

def get_chroma_client():
    """Returns a persistent ChromaDB client."""
    persist_dir = os.getenv("CHROMA_PERSIST_DIR", "./chroma_db")
    os.makedirs(persist_dir, exist_ok=True)
    return chromadb.PersistentClient(path=persist_dir)

def get_embedding_function():
    """Tries to load the default Chroma embedding function, falling back to HashEmbedding if it fails."""
    try:
        from chromadb.utils import embedding_functions
        # Default embedding function downloads all-MiniLM-L6-v2
        return embedding_functions.DefaultEmbeddingFunction()
    except Exception as e:
        logger.warning(f"Failed to load default Chroma embedding function, using fallback: {e}")
        return HashEmbeddingFunction()

def get_or_create_collection(name: str):
    """Retrieves or creates a ChromaDB collection with the appropriate embedding function."""
    client = get_chroma_client()
    emb_fn = get_embedding_function()
    # Note: ChromaDB requires the embedding function to be passed during collection retrieval/creation
    return client.get_or_create_collection(name=name, embedding_function=emb_fn)
