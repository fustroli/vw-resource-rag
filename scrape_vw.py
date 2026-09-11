import requests
from bs4 import BeautifulSoup
import time
import os
from urllib.parse import urljoin, urlparse

BASE_URL = "http://www.vw-resource.com/"
INDEX_URL = BASE_URL + "mihov_index.html"
OUTPUT_DIR = "vw_articles"
DELAY_SECONDS = 1.5  # be polite

HEADERS = {
    "User-Agent": "Mozilla/5.0 (personal archiving script; contact: your-email@example.com)"
}


def get_article_urls():
    """Fetch the master index and return a deduplicated set of article URLs
    (ignoring #anchor fragments, since many entries point to the same page)."""
    resp = requests.get(INDEX_URL, headers=HEADERS, timeout=15)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    urls = set()
    for a in soup.find_all("a", href=True):
        href = a["href"]
        full_url = urljoin(BASE_URL, href)
        parsed = urlparse(full_url)

        # Only keep pages on vw-resource.com, ending in .html
        if "vw-resource.com" in parsed.netloc and parsed.path.endswith(".html"):
            # Strip the #fragment so we don't download the same page twice
            clean_url = parsed._replace(fragment="").geturl()
            urls.add(clean_url)

    return sorted(urls)


def slug_from_url(url):
    """Turn a URL into a safe filename."""
    path = urlparse(url).path
    name = path.strip("/").split("/")[-1] or "index"
    if not name.endswith(".html"):
        name += ".html"
    return name.replace(".html", ".txt")


def download_article(url):
    resp = requests.get(url, headers=HEADERS, timeout=15)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    # Strip out nav/script/style elements that aren't real article content
    for tag in soup(["script", "style", "nav"]):
        tag.decompose()

    text = soup.get_text(separator="\n", strip=True)
    # Collapse multiple blank lines
    lines = [line for line in text.splitlines() if line.strip()]
    return "\n".join(lines)


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    print("Fetching index page...")
    urls = get_article_urls()
    print(f"Found {len(urls)} unique article pages.")

    failed = []
    for i, url in enumerate(urls, 1):
        filename = slug_from_url(url)
        filepath = os.path.join(OUTPUT_DIR, filename)

        if os.path.exists(filepath):
            print(f"[{i}/{len(urls)}] Skipping (already downloaded): {filename}")
            continue

        try:
            print(f"[{i}/{len(urls)}] Downloading: {url}")
            text = download_article(url)
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(text)
        except Exception as e:
            print(f"  FAILED: {e}")
            failed.append(url)

        time.sleep(DELAY_SECONDS)

    print(f"\nDone. {len(urls) - len(failed)} succeeded, {len(failed)} failed.")
    if failed:
        with open(os.path.join(OUTPUT_DIR, "_failed_urls.txt"), "w") as f:
            f.write("\n".join(failed))
        print("Failed URLs saved to vw_articles/_failed_urls.txt — rerun the script to retry them.")


if __name__ == "__main__":
    main()
