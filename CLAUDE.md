# CLAUDE.md

This is a local RAG learning project (see README.md for the pipeline overview). No framework, no build step — plain Python scripts run in sequence, each one a discrete pipeline stage.

## Architecture

Each script is a standalone pipeline stage, run manually in order (see README). There's no orchestration layer by design — this is a learning project where each step should be inspectable on its own.

- `query.py` holds shared retrieval constants/helpers (`DB_PATH`, `COLLECTION_NAME`, `N_RESULTS`, `embed_question`) that `ask.py` imports rather than duplicating.
- Chunk metadata (`id`, `source`, `title`, `source_url`, `chunk_index`, `total_chunks`) is set in `chunk_articles.py` and carried through embedding and storage unchanged — `source_url` is re-derived by re-fetching the site's index page (not stored at scrape time).
- Embedding model (`nomic-embed-text`) and chat model (`llama3.2:3b`) are independent — swapping the chat model needs no re-chunk/re-embed; swapping the embedding model does, since vectors from different models aren't compatible.

## Environment

- Python venv at `vw-scraper-env/` (gitignored) — activate with `source vw-scraper-env/bin/activate` before running any script.
- Requires a local Ollama daemon running with `nomic-embed-text` and `llama3.2:3b` pulled.
- `chunks.json`, `chunks_embedded.json`, and `chroma_db/` are all gitignored generated artifacts — regenerate via the pipeline scripts rather than expecting them to exist after a fresh clone.

## Known gotchas (already hit once, don't re-debug)

- `chunk_articles.py`'s paragraph splitter falls back to single-newline splitting when an article has no blank-line paragraph breaks (most of this site's scraped articles) — this was previously a silent bug where every article chunked to exactly 1 oversized chunk.
- A venv moved to a new path keeps stale absolute paths in `activate`/`pip` scripts (`VIRTUAL_ENV`, shebangs) — breaks silently by falling through to system Python rather than erroring. Patch the paths in place rather than assuming a moved venv still works.
- Retrieval "neighbor expansion" (pulling in adjacent chunks from the same article) was tried and reverted — it introduced regressions when the top-ranked chunk came from a long, multi-topic article (e.g. an engine-rebuild guide) where adjacent chunks cover unrelated content. If revisiting this, scope expansion tightly (e.g. only the single closest match) and test against a multi-topic source article specifically.
