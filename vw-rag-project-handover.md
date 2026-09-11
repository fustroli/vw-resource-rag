# Project Handover: Local RAG Assistant (VW Repair Knowledge Base)

## Goal
Build a simple AI assistant, primarily as a **learning project for AI engineering**. No need for advanced models — the point is to try different things and understand the full pipeline (RAG: Retrieval-Augmented Generation), not to ship a polished product.

## What the app does
Answers questions using content scraped from `http://www.vw-resource.com/` — a large site of aircooled Volkswagen repair/maintenance articles ("Rob and Dave's Aircooled Volkswagen Pages"). The assistant should answer based on this specific content, not just general knowledge.

## Tech stack decided so far
- **Ollama** — running locally on CPU (no GPU available). Used for both the chat model and the embedding model.
  - Chat model: a small model (e.g. `llama3.2:3b`, `qwen2.5:7b`, or similar) — good enough for CPU speed and for RAG since retrieval carries most of the answer quality.
  - Embedding model: e.g. `nomic-embed-text` — small, runs fine on CPU.
- **Chroma** (planned) — lightweight local vector database to store chunk text + embeddings, no server needed.
- Plan: build the pipeline as a script first, wrap in a simple interface (CLI first, then minimal web UI) later.

## Overall step plan
1. Install Ollama & pull models
2. Collect and clean content — scrape `vw-resource.com` into `.txt` files, one per article
3. Chunk the text
4. Generate embeddings for each chunk (via Ollama's embedding model)
5. Store chunks + embeddings in Chroma (vector database)
6. Build retrieval + query logic (embed question → find similar chunks)
7. Generate the answer (retrieved chunks + question → chat model)
8. Wrap in a simple interface (CLI, then basic web UI)
9. Experiment and iterate (swap models, tune chunk size, tweak prompts)

## How to use this handover
Paste this into a new chat to pick up at any step with full context, without needing to re-explain the project from scratch.
