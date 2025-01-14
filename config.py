import os

# Get the directory where the current file (config.py) is located
base_dir = os.path.dirname(os.path.abspath(__file__))

# Define paths relative to the base_dir
docdir = os.path.join(base_dir, "ag2_docs")
chunkdir = os.path.join(base_dir, "ag2_chunks")
embeddir = os.path.join(base_dir, "ag2_embeds")
imagedir = os.path.join(base_dir, "images")
imagetodeletedir = os.path.join(base_dir, "images_to_delete")
