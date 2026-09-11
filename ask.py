import json

import chromadb
import requests

from query import DB_PATH, COLLECTION_NAME, N_RESULTS, embed_question

CHAT_MODEL = "qwen2.5:7b"
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

    # re-sort by (source, chunk_index) so a multi-step procedure reads in its
    # original sequence instead of jumbled by similarity rank. Source order
    # follows first appearance in the ranked results - no new chunks fetched,
    # just reordering what similarity search already returned.
    source_order = []
    for meta in metas:
        if meta["source"] not in source_order:
            source_order.append(meta["source"])

    order = sorted(
        range(len(docs)),
        key=lambda i: (source_order.index(metas[i]["source"]), metas[i]["chunk_index"]),
    )
    docs = [docs[i] for i in order]
    metas = [metas[i] for i in order]
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


def stream_answer_tokens(question: str, docs: list, metas: list):
    """Yield answer text as it streams from Ollama, one piece at a time."""
    payload = {
        "model": CHAT_MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": build_prompt(question, docs, metas)},
        ],
        "stream": True,
        "options": {"num_predict": 600},
    }

    with requests.post(OLLAMA_CHAT_URL, json=payload, stream=True, timeout=300) as resp:
        resp.raise_for_status()
        for line in resp.iter_lines():
            if not line:
                continue
            chunk = json.loads(line)
            content = chunk.get("message", {}).get("content", "")
            if content:
                yield content
            if chunk.get("done"):
                break


def get_sources(metas: list):
    seen = set()
    sources = []
    for meta in metas:
        url = meta["source_url"]
        if url in seen:
            continue
        seen.add(url)
        sources.append({"title": meta["title"], "url": url})
    return sources


def print_sources(metas: list):
    print("\nSources:")
    for source in get_sources(metas):
        print(f"- {source['title']}: {source['url']}")


def main():
    question = input("Ask a question: ")
    docs, metas = retrieve(question)

    print()
    for token in stream_answer_tokens(question, docs, metas):
        print(token, end="", flush=True)
    print()
    print_sources(metas)


if __name__ == "__main__":
    main()
