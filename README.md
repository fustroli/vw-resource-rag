# VW Resource RAG

A local RAG (Retrieval-Augmented Generation) assistant for aircooled Volkswagen repair questions, built as a learning project for the full RAG pipeline. Answers are grounded in content scraped from [vw-resource.com](http://www.vw-resource.com/) — "Rob and Dave's Aircooled Volkswagen Pages."

Runs entirely locally via [Ollama](https://ollama.com) (CPU, no GPU needed) and [Chroma](https://www.trychroma.com/) as the vector store.

## Pipeline

1. `scrape_vw.py` — scrapes articles from vw-resource.com into `vw_articles/*.txt`
2. `chunk_articles.py` — splits articles into ~500-token chunks (100-token overlap), with title/source URL metadata, into `chunks.json`
3. `embed_chunks.py` — embeds each chunk with Ollama's `nomic-embed-text` model into `chunks_embedded.json`
4. `load_to_chroma.py` — loads embedded chunks into a local Chroma collection (`./chroma_db`)
5. `query.py` — CLI: embeds a question, prints the top-5 most similar chunks
6. `ask.py` — CLI: full RAG flow — retrieves chunks, streams an answer from Ollama's `llama3.2:3b` chat model, prints sources

## Setup

```bash
python3 -m venv vw-scraper-env
source vw-scraper-env/bin/activate
pip install requests beautifulsoup4 chromadb

ollama pull nomic-embed-text
ollama pull llama3.2:3b
```

## Usage

Run the pipeline in order (steps 1-4 are one-time setup; re-run only if the article set changes):

```bash
python3 scrape_vw.py
python3 chunk_articles.py
python3 embed_chunks.py
python3 load_to_chroma.py
```

Then ask questions:

```bash
python3 ask.py
```

## Known limitations

- Small local chat model (`llama3.2:3b`) can occasionally blend content from unrelated articles or produce inconsistent answer length/detail.
- Fixed-size chunking can split a multi-step procedure across chunk boundaries, occasionally dropping a step from an answer.
