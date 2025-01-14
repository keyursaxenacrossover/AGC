import os
import faiss
import numpy as np
from typing import Union, Dict
from config import chunkdir, embeddir

def faiss_lookup(query: str, top_k: int = 3, return_diagnostics: bool = False) -> Union[str, Dict]:
    """
    Perform local FAISS-based retrieval using the metadata file for mapping.
    
    Parameters:
        query (str): The query string to search.
        top_k (int): Number of top results to retrieve.
        return_diagnostics (bool): If True, return distances and filenames in addition to content.
    
    Returns:
        Union[str, Dict]: Combined chunk text (or an error message), optionally with diagnostic data.
    """
    EMBED_DIM = 3072
    INDEX_PATH = os.path.join(embeddir, "faiss_index")
    CHUNKS_DIR = chunkdir
    META_PATH = os.path.join(embeddir, "chunk_metadata.txt")

    if not os.path.exists(INDEX_PATH):
        return "[faiss_lookup] No local index found."

    # Load FAISS index
    index = faiss.read_index(INDEX_PATH)
    if index.d != EMBED_DIM:
        return f"[faiss_lookup] Dimension mismatch, index.d={index.d} vs {EMBED_DIM} expected."

    if not os.path.exists(META_PATH):
        return "[faiss_lookup] No local metadata found."

    # Load metadata into a list (first column is filename)
    metadata = []
    with open(META_PATH, "r", encoding="utf-8") as f:
        for line in f:
            filename, _ = line.strip().split("\t")
            metadata.append(filename)

    # Generate embedding for the query
    from openai import OpenAI  # Importing OpenAI client
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    response = client.embeddings.create(
        input=[query],
        model="text-embedding-3-large"
    )
    query_embedding = np.array(response.data[0].embedding, dtype="float32").reshape(1, -1)

    # Perform FAISS search
    distances, indices = index.search(query_embedding, top_k)

    # Resolve FAISS indices to chunk filenames
    retrieved_chunks = []
    retrieved_filenames = []
    for idx in indices[0]:
        if 0 <= idx < len(metadata):
            chunk_filename = metadata[idx]
            chunk_path = os.path.join(CHUNKS_DIR, chunk_filename)
            if os.path.exists(chunk_path):
                with open(chunk_path, "r", encoding="utf-8") as cfile:
                    retrieved_chunks.append(cfile.read().strip())
                retrieved_filenames.append(chunk_filename)
        else:
            print(f"[DEBUG] FAISS index {idx} is out of metadata bounds.")

    # Return results based on mode
    if not retrieved_chunks:
        return "[faiss_lookup] 0 results."

    if return_diagnostics:
        return {
            "content": "\n\n".join(retrieved_chunks),
            "distances": distances[0].tolist(),
            "filenames": retrieved_filenames
        }
    else:
        return "\n\n".join(retrieved_chunks)