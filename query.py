import chromadb
import requests

DB_PATH = "./chroma_db"
COLLECTION_NAME = "vw_articles"
OLLAMA_URL = "http://localhost:11434/api/embeddings"
MODEL = "nomic-embed-text"
N_RESULTS = 5


def embed_question(text: str):
    resp = requests.post(OLLAMA_URL, json={"model": MODEL, "prompt": text}, timeout=60)
    resp.raise_for_status()
    return resp.json()["embedding"]


def main():
    client = chromadb.PersistentClient(path=DB_PATH)
    collection = client.get_collection(COLLECTION_NAME)

    question = input("Ask a question: ")
    query_embedding = embed_question(question)

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=N_RESULTS,
    )

    docs = results["documents"][0]
    metas = results["metadatas"][0]
    dists = results["distances"][0]

    for doc, meta, dist in zip(docs, metas, dists):
        print(f"\n--- {meta['title']} (distance: {dist:.3f}) ---")
        print(f"{meta['source_url']}")
        print(doc[:300])


if __name__ == "__main__":
    main()
