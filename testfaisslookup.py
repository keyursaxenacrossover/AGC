from faisslookup import faiss_lookup
# Ensure the output is encoded in utf-8
import sys
sys.stdout.reconfigure(encoding='utf-8')
print(faiss_lookup(query="disposition code 11 meaning", top_k=3))