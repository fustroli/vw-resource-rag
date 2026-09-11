import json

import chromadb
import requests

from query import DB_PATH, COLLECTION_NAME, N_RESULTS, embed_question

CHAT_MODEL = "llama3.2:3b"
OLLAMA_CHAT_URL = "http://localhost:11434/api/chat"

SYSTEM_PROMPT = (
    "You are a helpful assistant answering questions about aircooled Volkswagen "
    "repair and maintenance, using only the provided context from vw-resource.com. "
    "If the answer isn't in the context, say you don't know — don't guess or use "
    "outside knowledge. Each context block below is labeled with the article it "
    "came from. Blocks from different articles may describe different procedures "
    "or scenarios — do not merge steps from different articles into one procedure "
    "unless they are clearly describing the same one."
)


def retrieve(question: str):
    client = chromadb.PersistentClient(path=DB_PATH)
    collection = client.get_collection(COLLECTION_NAME)

    query_embedding = embed_question(question)
    results = collection.query(query_embeddings=[query_embedding], n_results=N_RESULTS)

    docs = results["documents"][0]
    metas = results["metadatas"][0]
    return docs, metas


def build_prompt(question: str, docs: list, metas: list):
    blocks = [
        f"[From: {meta['title']}]\n{doc}"
        for doc, meta in zip(docs, metas)
    ]
    context = "\n---\n".join(blocks)
    return (
        f"Context:\n{context}\n\n"
        f"Question: {question}\n\n"
        f"Answer:"
    )


def stream_answer(question: str, docs: list, metas: list):
    payload = {
        "model": CHAT_MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": build_prompt(question, docs, metas)},
        ],
        "stream": True,
    }

    with requests.post(OLLAMA_CHAT_URL, json=payload, stream=True, timeout=120) as resp:
        resp.raise_for_status()
        for line in resp.iter_lines():
            if not line:
                continue
            chunk = json.loads(line)
            content = chunk.get("message", {}).get("content", "")
            print(content, end="", flush=True)
            if chunk.get("done"):
                break
    print()


def print_sources(metas: list):
    seen = set()
    print("\nSources:")
    for meta in metas:
        url = meta["source_url"]
        if url in seen:
            continue
        seen.add(url)
        print(f"- {meta['title']}: {url}")


def main():
    question = input("Ask a question: ")
    docs, metas = retrieve(question)

    print()
    stream_answer(question, docs, metas)
    print_sources(metas)


if __name__ == "__main__":
    main()
