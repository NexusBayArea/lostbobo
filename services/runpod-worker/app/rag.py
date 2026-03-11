from sentence_transformers import SentenceTransformer
import faiss
import pickle
import os

# Load model for embeddings
# Note: Using small model for Alpha efficiency
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
model = SentenceTransformer(EMBEDDING_MODEL)

INDEX_PATH = "/workspace/embeddings/index.faiss"
DOCS_PATH = "/workspace/embeddings/docs.pkl"

def query_rag(question):
    """Retrieves relevant engineering context from the vector store."""
    if not os.path.exists(INDEX_PATH) or not os.path.exists(DOCS_PATH):
        return "Warning: RAG index not found. Proceeding without engineering context."

    # Load index and docs
    index = faiss.read_index(INDEX_PATH)
    with open(DOCS_PATH, "rb") as f:
        docs = pickle.load(f)

    # Encode question
    emb = model.encode([question])

    # Search top 4 matches
    D, I = index.search(emb, 4)

    results = []
    for i in I[0]:
        if i != -1 and i < len(docs):
            results.append(docs[i])

    return "\n\n".join(results)
