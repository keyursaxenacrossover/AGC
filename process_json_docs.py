import os
import hashlib
import json
import time
from config import docdir, chunkdir

# Input directory containing the JSON files
DATA_DIR = docdir

# Output directory for processed chunks
CHUNKS_DIR = chunkdir
os.makedirs(CHUNKS_DIR, exist_ok=True)

# Metadata file to track document hashes and corresponding chunks
METADATA_PATH = os.path.join(CHUNKS_DIR, r"metadata/chunk_metadata.txt")
os.makedirs(os.path.dirname(METADATA_PATH), exist_ok=True)

# Model-specific token limit (set lower for safety)
TOKEN_LIMIT = 2000
TOKEN_OVERLAP = 200

def generate_short_filename(filename):
    """Generate a shorter filename using a hash."""
    hash_object = hashlib.md5(filename.encode())  # Use MD5 for shorter hashes
    return hash_object.hexdigest()

def hash_document(content):
    """Compute a hash for the entire document content."""
    return hashlib.sha256(content.encode("utf-8")).hexdigest()

def load_existing_metadata():
    """Load existing metadata mapping document hashes to chunk filenames."""
    metadata = {}
    if os.path.exists(METADATA_PATH):
        with open(METADATA_PATH, "r", encoding="utf-8") as file:
            for line in file:
                doc_hash, chunk_files = line.strip().split("\t")
                metadata[doc_hash] = chunk_files.split(",")
    return metadata

def save_metadata(metadata):
    """Save updated metadata back to the file."""
    with open(METADATA_PATH, "w", encoding="utf-8") as file:
        for doc_hash, metadata_entry in metadata.items():
            chunks = metadata_entry["chunks"]
            additional_fields = json.dumps({
                "url": metadata_entry.get("url", ""),
                "html_url": metadata_entry.get("html_url", ""),
                "title": metadata_entry.get("title", ""),
                "outdated": metadata_entry.get("outdated", False)
            })
            file.write(f"{doc_hash}\t{','.join(chunks)}\t{additional_fields}\n")

def remove_obsolete_chunks(obsolete_chunks):
    """Remove obsolete chunks from the filesystem."""
    for chunk in obsolete_chunks:
        chunk_path = os.path.join(CHUNKS_DIR, chunk)
        if os.path.exists(chunk_path):
            os.remove(chunk_path)

def chunk_text_with_tiktoken(text, max_tokens=1200, overlap_tokens=300):
    """
    Splits text into chunks based on token count using tiktoken.
    Args:
        text (str): The input text to be split.
        max_tokens (int): Maximum tokens per chunk.
        overlap_tokens (int): Number of tokens to overlap between chunks.
    Returns:
        list: A list of text chunks.
    """
    import tiktoken
    tokenizer = tiktoken.encoding_for_model("text-embedding-3-large")
    tokens = tokenizer.encode(text)

    chunks = []
    start = 0
    max_iterations = len(tokens) // (max_tokens - overlap_tokens) + 2

    for iteration in range(max_iterations):
        if start >= len(tokens):
            break

        end = min(start + max_tokens, len(tokens))
        chunk = tokens[start:end]

        if len(chunk) < max_tokens * 0.5 and chunks:
            merged_tokens = tokenizer.encode(chunks[-1]) + chunk
            if len(merged_tokens) <= max_tokens:
                chunks[-1] = tokenizer.decode(merged_tokens)
            else:
                chunks.append(tokenizer.decode(chunk))
        else:
            chunks.append(tokenizer.decode(chunk))

        start = end - overlap_tokens

    return chunks

def process_json_files():
    """Processes JSON files into token-based chunks for embedding."""
    metadata = load_existing_metadata()

    print(f"Processing JSON files in {DATA_DIR}...")
    file_count = 0
    new_chunk_count = 0
    updated_chunk_count = 0
    obsolete_chunk_count = 0
    current_metadata = {}

    for filename in os.listdir(DATA_DIR):
        if filename.endswith(".json"):
            filepath = os.path.join(DATA_DIR, filename)
            print(f"[INFO] Processing file: {filename}")

            try:
                with open(filepath, "r", encoding="utf-8") as file:
                    json_content = json.load(file)
                
                # Extract required fields
                content = json_content.get("body", "")
                url = json_content.get("url", "")
                html_url = json_content.get("html_url", "")
                title = json_content.get("title", "")
                outdated = json_content.get("outdated", False)

                if not content:
                    print(f"[SKIPPED] No 'body' field found in {filename}")
                    continue

                doc_hash = hash_document(content)

                if doc_hash in metadata:
                    current_metadata[doc_hash] = metadata[doc_hash]
                    print(f"[SKIPPED] No changes detected for {filename}")
                    continue

                chunks = chunk_text_with_tiktoken(content)
                short_name = generate_short_filename(filename)
                new_chunks = [f"{short_name}_chunk_{i}.txt" for i in range(len(chunks))]

                for chunk_filename, chunk_content in zip(new_chunks, chunks):
                    chunk_path = os.path.join(CHUNKS_DIR, chunk_filename)
                    with open(chunk_path, "w", encoding="utf-8") as chunk_file:
                        chunk_file.write(chunk_content)

                # Save additional metadata
                metadata_entry = {
                    "chunks": new_chunks,
                    "url": url,
                    "html_url": html_url,
                    "title": title,
                    "outdated": outdated
                }
                current_metadata[doc_hash] = metadata_entry

                if doc_hash in metadata:
                    obsolete_chunks = set(metadata[doc_hash]["chunks"]) - set(new_chunks)
                    remove_obsolete_chunks(obsolete_chunks)
                    obsolete_chunk_count += len(obsolete_chunks)
                    updated_chunk_count += len(new_chunks)
                else:
                    new_chunk_count += len(new_chunks)

                file_count += 1
            except Exception as e:
                print(f"[ERROR] Error processing {filename}: {e}")

    save_metadata(current_metadata)

    print("\nProcessing complete:")
    print(f"{file_count} files processed.")
    print(f"{new_chunk_count} new chunks created.")
    print(f"{updated_chunk_count} chunks updated.")
    print(f"{obsolete_chunk_count} obsolete chunks removed.")

if __name__ == "__main__":
    process_json_files()
