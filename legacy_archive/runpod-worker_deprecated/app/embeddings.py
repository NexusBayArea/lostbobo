from sentence_transformers import SentenceTransformer
import faiss
import pickle
import os
import argparse

def build_index(dataset_path, output_dir):
    """Builds a FAISS index from a text dataset."""
    if not os.path.exists(dataset_path):
        print(f"Error: Dataset not found at {dataset_path}")
        return

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    print(f"Loading embedding model...")
    model = SentenceTransformer("all-MiniLM-L6-v2")

    print(f"Reading dataset...")
    with open(dataset_path, "r", encoding="utf-8") as f:
        docs = f.read().split("\n\n")
    
    # Filter empty docs
    docs = [d.strip() for d in docs if d.strip()]
    
    print(f"Generating embeddings for {len(docs)} documents...")
    embeddings = model.encode(docs)

    # Derive dimension dynamically from embeddings shape
    dimension = embeddings.shape[1]
    index = faiss.IndexFlatL2(dimension)
    index.add(embeddings)

    print(f"Saving index and docs to {output_dir}...")
    faiss.write_index(index, os.path.join(output_dir, "index.faiss"))
    with open(os.path.join(output_dir, "docs.pkl"), "wb") as f:
        pickle.dump(docs, f)

    print("RAG Index build complete.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", default="/workspace/rag_data/dataset.txt")
    parser.add_argument("--output", default="/workspace/embeddings")
    args = parser.parse_args()
    
    build_index(args.dataset, args.output)
