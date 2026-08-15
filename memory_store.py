import json
import chromadb
from sentence_transformers import SentenceTransformer
from datetime import datetime

CHROMA_PATH = "./chroma_db"
MEMORY_COLLECTION = "resolved_issues_memory"

_model = None
_collection = None


def _get_model():
    global _model
    if _model is None:
        _model = SentenceTransformer("all-MiniLM-L6-v2")
    return _model


def _get_collection():
    global _collection
    if _collection is None:
        client = chromadb.PersistentClient(path=CHROMA_PATH)
        _collection = client.get_or_create_collection(MEMORY_COLLECTION)
    return _collection


def store_resolved_issue(issue_title: str, requirements: dict, fix: dict, review: dict):
    model = _get_model()
    collection = _get_collection()

    summary_text = f"{issue_title} {requirements['summary']} {fix['proposed_approach']}"
    embedding = model.encode([summary_text]).tolist()

    record_id = f"memory_{datetime.now().timestamp()}"
    metadata = {
        "issue_title": issue_title,
        "fix_approach": fix["proposed_approach"][:500],
        "code_snippet": fix["code_snippet"][:1000],
        "approved": review["approved"],
        "timestamp": datetime.now().isoformat()
    }

    collection.add(
        ids=[record_id],
        documents=[summary_text],
        metadatas=[metadata],
        embeddings=embedding
    )
    print(f"[Memory] Stored resolved issue: {issue_title[:60]}...", flush=True)


def recall_similar_issues(query_text: str, n_results: int = 2) -> list[dict]:
    model = _get_model()
    collection = _get_collection()

    if collection.count() == 0:
        return []

    query_embedding = model.encode([query_text]).tolist()
    results = collection.query(
        query_embeddings=query_embedding,
        n_results=min(n_results, collection.count())
    )

    memories = []
    for meta in results["metadatas"][0]:
        memories.append(meta)
    return memories