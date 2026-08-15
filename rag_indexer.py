import os
import git
import chromadb
from sentence_transformers import SentenceTransformer

REPO_URL = "https://github.com/pallets/click.git"
LOCAL_PATH = "./cloned_repos/click"
CHROMA_PATH = "./chroma_db"
COLLECTION_NAME = "click_codebase"


def clone_repo():
    if not os.path.exists(LOCAL_PATH):
        print(f"Cloning {REPO_URL}...")
        git.Repo.clone_from(REPO_URL, LOCAL_PATH, depth=1)
    else:
        print("Repo already cloned, skipping.")


def chunk_file(filepath: str, max_chars: int = 1500) -> list[str]:
    with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()
    return [content[i:i + max_chars] for i in range(0, len(content), max_chars)]


def build_index():
    clone_repo()

    print("Loading embedding model (first run downloads it, ~90MB)...")
    model = SentenceTransformer("all-MiniLM-L6-v2")

    client = chromadb.PersistentClient(path=CHROMA_PATH)
    collection = client.get_or_create_collection(COLLECTION_NAME)

    if collection.count() > 0:
        print(f"Index already has {collection.count()} chunks, skipping rebuild.")
        return

    ids, documents, metadatas = [], [], []
    chunk_id = 0

    for root, _, files in os.walk(os.path.join(LOCAL_PATH, "src")):
        for fname in files:
            if not fname.endswith(".py"):
                continue
            full_path = os.path.join(root, fname)
            rel_path = os.path.relpath(full_path, LOCAL_PATH)
            for chunk in chunk_file(full_path):
                if not chunk.strip():
                    continue
                ids.append(f"chunk_{chunk_id}")
                documents.append(chunk)
                metadatas.append({"file": rel_path})
                chunk_id += 1

    print(f"Embedding {len(documents)} chunks...")
    embeddings = model.encode(documents, show_progress_bar=True).tolist()

    collection.add(ids=ids, documents=documents, metadatas=metadatas, embeddings=embeddings)
    print(f"Indexed {len(documents)} chunks into ChromaDB.")


if __name__ == "__main__":
    build_index()