import json
import os
import re

from scrape_vw import get_article_urls, slug_from_url

INPUT_DIR = "vw_articles"
OUTPUT_FILE = "chunks.json"
MAX_TOKENS = 500
OVERLAP_TOKENS = 100


def est_tokens(text: str) -> int:
    return max(1, len(text) // 4)  # rough ~4 chars/token


def split_paragraphs(text: str):
    paras = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    if len(paras) > 1:
        return paras
    # source has no blank-line paragraph breaks; fall back to single-newline lines
    return [p.strip() for p in text.split("\n") if p.strip()]


def split_oversized(unit: str, max_tokens: int):
    """Word-split a single unit that alone exceeds max_tokens."""
    words = unit.split()
    pieces = []
    current_words = []
    current_tokens = 0
    for word in words:
        word_tokens = est_tokens(word + " ")
        if current_tokens + word_tokens > max_tokens and current_words:
            pieces.append(" ".join(current_words))
            current_words = []
            current_tokens = 0
        current_words.append(word)
        current_tokens += word_tokens
    if current_words:
        pieces.append(" ".join(current_words))
    return pieces


def chunk_text(text: str, max_tokens=MAX_TOKENS, overlap_tokens=OVERLAP_TOKENS):
    paras = []
    for para in split_paragraphs(text):
        if est_tokens(para) > max_tokens:
            paras.extend(split_oversized(para, max_tokens))
        else:
            paras.append(para)

    chunks = []
    current = []
    current_tokens = 0

    for para in paras:
        para_tokens = est_tokens(para)

        if current_tokens + para_tokens > max_tokens and current:
            chunks.append("\n\n".join(current))

            # build overlap from trailing paragraphs
            overlap = []
            overlap_tok = 0
            for p in reversed(current):
                overlap_tok += est_tokens(p)
                overlap.insert(0, p)
                if overlap_tok >= overlap_tokens:
                    break
            current = overlap
            current_tokens = overlap_tok

        current.append(para)
        current_tokens += para_tokens

    if current:
        chunks.append("\n\n".join(current))

    return chunks


def build_url_map():
    """Re-fetch the index page (not the articles) to map filename base -> source URL."""
    try:
        urls = get_article_urls()
    except Exception as e:
        print(f"  WARNING: couldn't fetch index for source URLs ({e}); source_url will be null")
        return {}

    url_map = {}
    for url in urls:
        filename = slug_from_url(url)
        base = os.path.splitext(filename)[0]
        url_map[base] = url
    return url_map


def extract_title(raw: str) -> str:
    for line in raw.split("\n"):
        line = line.strip()
        if line:
            return line
    return ""


def chunk_file(path: str, url_map: dict):
    with open(path, "r", encoding="utf-8") as f:
        raw = f.read()

    base = os.path.splitext(os.path.basename(path))[0]
    title = extract_title(raw)
    source_url = url_map.get(base)
    pieces = chunk_text(raw)
    total_chunks = len(pieces)

    return [
        {
            "id": f"{base}-{i}",
            "source": base,
            "title": title,
            "source_url": source_url,
            "chunk_index": i,
            "total_chunks": total_chunks,
            "text": piece,
        }
        for i, piece in enumerate(pieces)
    ]


def main():
    print("Fetching index for source URLs...")
    url_map = build_url_map()

    all_chunks = []
    files = [f for f in os.listdir(INPUT_DIR) if f.endswith(".txt")]

    missing_urls = 0
    for fname in files:
        chunks = chunk_file(os.path.join(INPUT_DIR, fname), url_map)
        if chunks and chunks[0]["source_url"] is None:
            missing_urls += 1
        all_chunks.extend(chunks)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(all_chunks, f, indent=2, ensure_ascii=False)

    print(f"Chunked {len(files)} files into {len(all_chunks)} chunks -> {OUTPUT_FILE}")
    if missing_urls:
        print(f"  Note: {missing_urls} file(s) had no matching URL in the current index.")


if __name__ == "__main__":
    main()
