import hashlib
import os
import faiss
import numpy as np
import time
from openai import OpenAI
from config import chunkdir, embeddir

# Directories and file paths
CHUNKS_DIR = chunkdir
EMBEDDINGS_DIR = embeddir
EMBEDDINGS_PATH = os.path.join(EMBEDDINGS_DIR, "faiss_index")
METADATA_PATH = os.path.join(EMBEDDINGS_DIR, "chunk_metadata.txt")

# NEW COMMENT: Use text-embedding-3-large, which has 3072 dimensions by default.
EMBEDDING_MODEL = "text-embedding-3-large"
EMBEDDING_SIZE = 3072

# NEW COMMENT: Adjust BATCH_SIZE as needed for performance vs. token usage.
BATCH_SIZE = 16

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
if not client.api_key:
    raise ValueError("OpenAI API key not set in config. Refer to the Readme file.")


def hash_chunk(content):
    """Compute a hash for a chunk's content to detect changes."""
    return hashlib.sha256(content.encode('utf-8')).hexdigest()


def remove_old_index_and_metadata():
    """
    Removes any old FAISS index and metadata so we always start fresh.
    This ensures no stale chunks remain in the final index.
    """
    if os.path.exists(EMBEDDINGS_PATH):
        os.remove(EMBEDDINGS_PATH)
        print(f"[INFO] Removed old index at {EMBEDDINGS_PATH}")

    if os.path.exists(METADATA_PATH):
        os.remove(METADATA_PATH)
        print(f"[INFO] Removed old metadata at {METADATA_PATH}")


def save_index_and_metadata(index, metadata):
    """
    Write the entire FAISS index and metadata to disk once at the end.
    """
    os.makedirs(EMBEDDINGS_DIR, exist_ok=True)

    # Write the FAISS index
    faiss.write_index(index, EMBEDDINGS_PATH)

    # Write metadata
    with open(METADATA_PATH, "w", encoding="utf-8") as f:
        for filename, chunk_hash in metadata.items():
            f.write(f"{filename}\t{chunk_hash}\n")

    print(f"[INFO] Saved new index to {EMBEDDINGS_PATH}")
    print(f"[INFO] Saved new metadata to {METADATA_PATH}")


def rebuild_index():
    """
    Full rebuild approach:
      1) Remove old index + metadata
      2) Create fresh index
      3) Embed all chunks in CHUNKS_DIR (in batches) and add to index
      4) Save final index + metadata
    """

    # 1) Remove old index/metadata
    remove_old_index_and_metadata()

    # 2) Create fresh index for text-embedding-3-large
    index = faiss.IndexFlatL2(EMBEDDING_SIZE)
    metadata = {}

    # Gather all .txt chunks
    chunk_files = sorted(
        f for f in os.listdir(CHUNKS_DIR) if f.endswith(".txt")
    )
    total_chunks = len(chunk_files)
    print(f"\n[INFO] Found {total_chunks} text chunks to embed.")

    # We'll do embedding in batches for efficiency
    batch_texts = []
    batch_filenames = []
    batch_hashes = []

    processed_count = 0
    start_time = time.time()

    for i, chunk_filename in enumerate(chunk_files, start=1):
        chunk_path = os.path.join(CHUNKS_DIR, chunk_filename)
        with open(chunk_path, "r", encoding="utf-8") as file:
            content = file.read().strip()

        if not content:
            print(f"[SKIPPED] Empty chunk: {chunk_filename}")
            continue

        # Compute a unique hash of the chunk content
        c_hash = hash_chunk(content)

        # Accumulate this chunk in a batch
        batch_texts.append(content)
        batch_filenames.append(chunk_filename)
        batch_hashes.append(c_hash)

        # If we reached BATCH_SIZE or it's the last chunk, embed them
        if (len(batch_texts) == BATCH_SIZE) or (i == total_chunks):
            try:
                # Call embeddings in one request
                response = client.embeddings.create(input=batch_texts, model=EMBEDDING_MODEL)
                # Gather the embedding vectors
                embeddings = [r.embedding for r in response.data]  # each r is an Embedding object

                # Convert to float32
                embeddings_np = np.array(embeddings, dtype="float32")

                # Add to FAISS index
                index.add(embeddings_np)

                # Add to metadata
                for fname, hsh in zip(batch_filenames, batch_hashes):
                    metadata[fname] = hsh

                processed_count += len(batch_texts)
                elapsed = time.time() - start_time
                remaining = total_chunks - i
                avg_time_per_chunk = (elapsed / processed_count) if processed_count else 0
                eta_sec = avg_time_per_chunk * remaining
                print(f"[BATCH] Embedded {len(batch_texts)} chunks. "
                      f"Total processed so far: {processed_count}/{total_chunks} "
                      f"(ETA: {int(eta_sec // 60)}m {int(eta_sec % 60)}s)")
            except Exception as e:
                print(f"[ERROR] Failed to process batch of {len(batch_texts)} chunks: {e}")
            finally:
                # Clear batch
                batch_texts = []
                batch_filenames = []
                batch_hashes = []

    # 4) Save final index + metadata once everything is embedded
    save_index_and_metadata(index, metadata)

    print("\n[INFO] Rebuild complete.")
    print(f"[INFO] {processed_count} total chunks embedded.")


if __name__ == "__main__":
    rebuild_index()
