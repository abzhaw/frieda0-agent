import os, glob, pickle
import faiss
from sentence_transformers import SentenceTransformer

# Config
EMBED_MODEL = "all-MiniLM-L6-v2"
DOCS_DIR    = "my_docs/"
INDEX_FILE  = "faiss_index.bin"
META_FILE   = "doc_chunks.pkl"

def load_texts():
    chunks, metas = [], []
    for path in glob.glob(os.path.join(DOCS_DIR, "**/*.txt"), recursive=True):
        text = open(path, encoding="utf8").read()
        # simple paragraph chunks
        for i, part in enumerate(text.split("\n\n")):
            if part.strip():
                chunks.append(part.strip())
                metas.append({"path": path, "chunk_id": i})
    return chunks, metas

def build_index():
    print("Loading documents…")
    texts, metas = load_texts()
    print(f"{len(texts)} chunks to embed.")
    model = SentenceTransformer(EMBED_MODEL)
    if not texts:
        print("⚠️ No documents found in my_docs/. Exiting.")
        return
    embeddings = model.encode(texts, show_progress_bar=True)
    dim = embeddings.shape[1]
    idx = faiss.IndexFlatL2(dim)
    idx.add(embeddings)
    print("Saving index & metadata…")
    faiss.write_index(idx, INDEX_FILE)
    with open(META_FILE, "wb") as f:
        pickle.dump({"texts": texts, "metas": metas}, f)

if __name__ == "__main__":
    build_index()
    print("Done. Files:", INDEX_FILE, META_FILE)
