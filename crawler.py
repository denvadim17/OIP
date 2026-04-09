import argparse
import re
import time
from collections import deque
from pathlib import Path
from typing import Deque, Set
from urllib.parse import urljoin, urlparse, urldefrag

import requests


DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
)


def read_seed_urls(path: Path) -> Deque[str]:
    queue: Deque[str] = deque()
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if line and not line.startswith("#"):
            queue.append(line)
    return queue


def is_allowed_url(url: str, language_host: str) -> bool:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        return False
    if parsed.netloc != language_host:
        return False
    if not parsed.path.startswith("/wiki/"):
        return False
    if ":" in parsed.path:
        return False
    return True


def extract_links(html: str, page_url: str, language_host: str) -> Set[str]:
    links: Set[str] = set()
    for href in re.findall(r'href=["\'](.*?)["\']', html, flags=re.IGNORECASE):
        absolute = urljoin(page_url, href)
        absolute, _ = urldefrag(absolute)
        absolute = absolute.rstrip("/")
        if is_allowed_url(absolute, language_host):
            links.add(absolute)
    return links


def build_output_dirs(base_dir: Path) -> None:
    base_dir.mkdir(parents=True, exist_ok=True)
    (base_dir / "pages").mkdir(parents=True, exist_ok=True)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Download at least N text HTML pages and build index.txt"
    )
    parser.add_argument("--seeds", default="seeds.txt", help="Path to seeds file")
    parser.add_argument("--output", default="output", help="Output directory")
    parser.add_argument("--max-pages", type=int, default=100, help="Pages limit")
    parser.add_argument(
        "--host",
        default="ru.wikipedia.org",
        help="Single-language host filter (default: ru.wikipedia.org)",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=0.2,
        help="Delay between requests in seconds",
    )
    args = parser.parse_args()

    output_dir = Path(args.output)
    seeds_path = Path(args.seeds)
    build_output_dirs(output_dir)

    queue = read_seed_urls(seeds_path)
    visited: Set[str] = set()
    downloaded = 0

    session = requests.Session()
    # Ignore system proxy variables to avoid proxy restrictions in some environments.
    session.trust_env = False
    session.headers.update(
        {
            "User-Agent": DEFAULT_USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "ru-RU,ru;q=0.9",
        }
    )

    index_lines = []
    pages_dir = output_dir / "pages"

    while queue and downloaded < args.max_pages:
        url = queue.popleft()
        normalized, _ = urldefrag(url.rstrip("/"))

        if normalized in visited:
            continue
        visited.add(normalized)

        if not is_allowed_url(normalized, args.host):
            continue

        try:
            response = session.get(normalized, timeout=15)
            content_type = response.headers.get("Content-Type", "")
            if response.status_code != 200:
                continue
            if "text/html" not in content_type:
                continue
            html = response.text
            if not html.strip():
                continue
        except requests.RequestException:
            continue

        file_number = downloaded + 1
        filename = f"{file_number:03d}.txt"
        (pages_dir / filename).write_text(html, encoding="utf-8")
        index_lines.append(f"{file_number:03d}\t{normalized}")
        downloaded += 1

        for link in extract_links(html, normalized, args.host):
            if link not in visited:
                queue.append(link)

        time.sleep(args.delay)

    (output_dir / "index.txt").write_text("\n".join(index_lines) + "\n", encoding="utf-8")

    print(f"Downloaded pages: {downloaded}")
    print(f"Output directory: {output_dir.resolve()}")
    print(f"Index file: {(output_dir / 'index.txt').resolve()}")


if __name__ == "__main__":
    main()
