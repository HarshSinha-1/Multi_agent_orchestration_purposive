from typing import Optional
from shared.vector_store.client import get_or_create_collection
from shared.utils.logging import get_logger

logger = get_logger(__name__)

def embed_and_store(text: str, doc_id: str, collection_name: str, metadata: Optional[dict] = None) -> bool:
    """Chunks text (if large) and stores it in the specified ChromaDB collection."""
    if not text:
        logger.warning(f"No text to store for doc_id {doc_id} in {collection_name}")
        return False
    
    try:
        collection = get_or_create_collection(collection_name)
        # Split into simple paragraph/sentence chunks for better retrieval if very large
        # For prototype, we'll keep it simple: store the whole text, but chunk if over 2000 chars
        chunks = []
        if len(text) > 2000:
            # Simple paragraph split
            raw_chunks = text.split("\n\n")
            current_chunk = ""
            for rc in raw_chunks:
                if len(current_chunk) + len(rc) < 2000:
                    current_chunk += rc + "\n\n"
                else:
                    if current_chunk:
                        chunks.append(current_chunk.strip())
                    current_chunk = rc + "\n\n"
            if current_chunk:
                chunks.append(current_chunk.strip())
        else:
            chunks = [text.strip()]
        
        ids = [f"{doc_id}_chunk_{i}" for i in range(len(chunks))]
        metadatas = [metadata or {} for _ in chunks]
        
        # Store in ChromaDB
        collection.add(
            documents=chunks,
            ids=ids,
            metadatas=metadatas
        )
        logger.info(f"Successfully stored {len(chunks)} chunks for {doc_id} in collection '{collection_name}'")
        return True
    except Exception as e:
        logger.error(f"Error storing embeddings in ChromaDB: {e}")
        return False

def similarity_search(query: str, collection_name: str, n_results: int = 3) -> list[dict]:
    """Queries ChromaDB collection for top-k matches."""
    try:
        collection = get_or_create_collection(collection_name)
        results = collection.query(
            query_texts=[query],
            n_results=n_results
        )
        
        # Format results nicely
        formatted_matches = []
        if results and 'documents' in results and results['documents']:
            docs = results['documents'][0]
            ids = results['ids'][0]
            metadatas = results['metadatas'][0] if 'metadatas' in results and results['metadatas'] else [{}] * len(docs)
            distances = results['distances'][0] if 'distances' in results and results['distances'] else [0.0] * len(docs)
            
            for doc, id_val, meta, dist in zip(docs, ids, metadatas, distances):
                formatted_matches.append({
                    "id": id_val,
                    "content": doc,
                    "metadata": meta,
                    "distance": dist
                })
        return formatted_matches
    except Exception as e:
        logger.error(f"Error searching ChromaDB collection '{collection_name}': {e}")
        return []
