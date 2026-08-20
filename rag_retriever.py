import chromadb
from sentence_transformers import SentenceTransformer
from rag_indexer import collection_name_for

CHROMA_PATH = "./chroma_db"

_model = None


def _get_model():
    global _model
    if _model is None:
        _model = SentenceTransformer("all-MiniLM-L6-v2")
    return _model


def retrieve_relevant_code(query: str, owner: str, repo: str, n_results: int = 4) -> list[dict]:
    model = _get_model()
    client = chromadb.PersistentClient(path=CHROMA_PATH)
    coll_name = collection_name_for(owner, repo)

    try:
        collection = client.get_collection(coll_name)
    except Exception:
        return []  # index doesn't exist for this repo yet — degrade gracefully

    if collection.count() == 0:
        return []

    query_embedding = model.encode([query]).tolist()
    results = collection.query(query_embeddings=query_embedding, n_results=min(n_results, collection.count()))

    chunks = []
    for doc, meta in zip(results["documents"][0], results["metadatas"][0]):
        chunks.append({"file": meta["file"], "content": doc})
    return chunks