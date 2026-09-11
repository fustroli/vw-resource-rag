import json
import os
import time

import requests

CHUNKS_FILE = "chunks.json"
OUTPUT_FILE = "chunks_embedded.json"
OLLAMA_URL = "http://localhost:11434/api/embeddings"
MODEL = "nomic-embed-text"
SAVE_EVERY = 50


def load_existing():
    if os.path.exists(OUTPUT_FILE):
        with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
            existing = json.load(f)
        return {c["id"]: c for c in existing}
    return {}


def embed(text: str):
    resp = requests.post(OLLAMA_URL, json={"model": MODEL, "prompt": text}, timeout=60)
    resp.raise_for_status()
    return resp.json()["embedding"]


def main():
    with open(CHUNKS_FILE, "r", encoding="utf-8") as f:
        chunks = json.load(f)

    done = load_existing()
    if done:
        print(f"Resuming: {len(done)}/{len(chunks)} chunks already embedded")
    else:
        print(f"Embedding {len(chunks)} chunks with {MODEL}")

    results = []
    start = time.time()
    for i, chunk in enumerate(chunks, 1):
        if chunk["id"] in done:
            results.append(done[chunk["id"]])
            continue

        embedding = embed(chunk["text"])
        results.append({**chunk, "embedding": embedding})

        if i % SAVE_EVERY == 0 or i == len(chunks):
            with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
                json.dump(results, f)
            elapsed = time.time() - start
            rate = i / elapsed if elapsed > 0 else 0
            eta_min = (len(chunks) - i) / rate / 60 if rate > 0 else 0
            print(f"[{i}/{len(chunks)}] checkpoint saved - {elapsed:.0f}s elapsed, ~{eta_min:.1f} min remaining")

    print(f"Done. Wrote {len(results)} embedded chunks -> {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
