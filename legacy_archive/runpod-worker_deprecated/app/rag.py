import os

_model = None

def get_model():
    """Lazy-load the embedding model."""
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer
        EMBEDDING_MODEL = "all-MiniLM-L6-v2"
        _model = SentenceTransformer(EMBEDDING_MODEL)
    return _model

INDEX_PATH = "/workspace/embeddings/index.faiss"
DOCS_PATH = "/workspace/embeddings/docs.pkl"

def query_rag(question):
    """Retrieves relevant engineering context from the vector store."""
    if not os.path.exists(INDEX_PATH) or not os.path.exists(DOCS_PATH):
        return "Warning: RAG index not found. Proceeding without engineering context."

    # Load index and docs
    import faiss
    import pickle
    index = faiss.read_index(INDEX_PATH)
    with open(DOCS_PATH, "rb") as f:
        docs = pickle.load(f)

    # Encode question using lazy-loaded model
    model = get_model()
    emb = model.encode([question])

    # Search top 4 matches
    D, I = index.search(emb, 4)

    results = []
    for i in I[0]:
        if i != -1 and i < len(docs):
            results.append(docs[i])

    return "\n\n".join(results)
