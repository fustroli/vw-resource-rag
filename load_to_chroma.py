import json

import chromadb

INPUT_FILE = "chunks_embedded.json"
DB_PATH = "./chroma_db"
COLLECTION_NAME = "vw_articles"
BATCH_SIZE = 200


def main():
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        chunks = json.load(f)

    client = chromadb.PersistentClient(path=DB_PATH)
    collection = client.get_or_create_collection(COLLECTION_NAME)

    for start in range(0, len(chunks), BATCH_SIZE):
        batch = chunks[start:start + BATCH_SIZE]

        ids = [c["id"] for c in batch]
        embeddings = [c["embedding"] for c in batch]
        documents = [c["text"] for c in batch]
        metadatas = [
            {
                "source": c["source"],
                "title": c["title"],
                "source_url": c["source_url"] or "",
                "chunk_index": c["chunk_index"],
                "total_chunks": c["total_chunks"],
            }
            for c in batch
        ]

        collection.upsert(
            ids=ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas,
        )
        print(f"Upserted {start + len(batch)}/{len(chunks)}")

    print(f"Done. Collection '{COLLECTION_NAME}' now has {collection.count()} items in {DB_PATH}")


if __name__ == "__main__":
    main()
