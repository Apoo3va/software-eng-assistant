import os
import re
import git
import chromadb
from sentence_transformers import SentenceTransformer

CHROMA_PATH = "./chroma_db"
CLONE_ROOT = "./cloned_repos"

_model = None


def _get_model():
    global _model
    if _model is None:
        _model = SentenceTransformer("all-MiniLM-L6-v2")
    return _model


def _safe_name(owner: str, repo: str) -> str:
    """Make a filesystem/collection-safe identifier from owner/repo."""
    raw = f"{owner}_{repo}"
    return re.sub(r"[^a-zA-Z0-9_]", "_", raw).lower()


def collection_name_for(owner: str, repo: str) -> str:
    return f"code_{_safe_name(owner, repo)}"


def _local_path_for(owner: str, repo: str) -> str:
    return os.path.join(CLONE_ROOT, _safe_name(owner, repo))


def _clone_repo(owner: str, repo: str) -> str:
    local_path = _local_path_for(owner, repo)
    if not os.path.exists(local_path):
        repo_url = f"https://github.com/{owner}/{repo}.git"
        print(f"[RAG] Cloning {owner}/{repo}...")
        git.Repo.clone_from(repo_url, local_path, depth=1)
    else:
        print(f"[RAG] {owner}/{repo} already cloned, skipping.")
    return local_path


def _chunk_file(filepath: str, max_chars: int = 1500) -> list[str]:
    try:
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
    except Exception:
        return []
    return [content[i:i + max_chars] for i in range(0, len(content), max_chars)]


# Extensions worth indexing — covers most common languages, not just Python
CODE_EXTENSIONS = {
    ".py", ".js", ".ts", ".jsx", ".tsx", ".java", ".go", ".rb", ".php",
    ".c", ".cpp", ".h", ".hpp", ".cs", ".rs", ".swift", ".kt", ".md"
}


def build_index(owner: str, repo: str):
    """Clone (if needed) and index a repo into its own ChromaDB collection. Safe to call repeatedly — skips work if already done."""
    local_path = _clone_repo(owner, repo)

    client = chromadb.PersistentClient(path=CHROMA_PATH)
    coll_name = collection_name_for(owner, repo)
    collection = client.get_or_create_collection(coll_name)

    if collection.count() > 0:
        print(f"[RAG] Index for {owner}/{repo} already has {collection.count()} chunks, skipping rebuild.")
        return

    model = _get_model()

    ids, documents, metadatas = [], [], []
    chunk_id = 0

    for root, dirs, files in os.walk(local_path):
        # skip hidden/vendor/dependency folders for speed and relevance
        dirs[:] = [d for d in dirs if not d.startswith(".") and d not in
                   ("node_modules", "venv", "__pycache__", "dist", "build", "vendor")]
        for fname in files:
            ext = os.path.splitext(fname)[1]
            if ext not in CODE_EXTENSIONS:
                continue
            full_path = os.path.join(root, fname)
            rel_path = os.path.relpath(full_path, local_path)
            for chunk in _chunk_file(full_path):
                if not chunk.strip():
                    continue
                ids.append(f"chunk_{chunk_id}")
                documents.append(chunk)
                metadatas.append({"file": rel_path})
                chunk_id += 1
                # Safety cap so huge repos don't take forever on first index
                if chunk_id >= 1500:
                    break
            if chunk_id >= 1500:
                break
        if chunk_id >= 1500:
            break

    if not documents:
        print(f"[RAG] No indexable code files found in {owner}/{repo}.")
        return

    print(f"[RAG] Embedding {len(documents)} chunks for {owner}/{repo}...")
    embeddings = model.encode(documents, show_progress_bar=True).tolist()

    collection.add(ids=ids, documents=documents, metadatas=metadatas, embeddings=embeddings)
    print(f"[RAG] Indexed {len(documents)} chunks for {owner}/{repo}.")


if __name__ == "__main__":
    build_index("pallets", "click")