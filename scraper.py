from __future__ import annotations

import re
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup


CHAPTER_PATH = re.compile(r"^/book/[^/]+/[^/]+_\d+/?$")
LOCKED_MARKERS = re.compile(r"\b(lock(?:ed)?|vip|premium|paid|coin|paywall)\b", re.I)
CONTENT_SELECTORS = (
    ".cha-words",
    ".cha-content",
    ".chapter-content",
    ".chapter_content",
    "[class*='chapter-content']",
    "[class*='chapter_content']",
)


@dataclass(frozen=True)
class Chapter:
    title: str
    url: str
    number: int | None = None


def parse_book_url(value: str) -> tuple[str, str, str]:
    parsed = urlparse(value.strip())
    match = re.fullmatch(r"([^/]+)_(\d+)", parsed.path.strip("/").removeprefix("book/"))
    if parsed.scheme not in {"http", "https"} or not parsed.netloc or not match:
        raise ValueError("Enter a book page URL like https://site.example/book/title_123456.")
    book_id = match.group(2)
    base_url = f"{parsed.scheme}://{parsed.netloc}"
    return base_url, book_id, f"{base_url}/book/{book_id}/catalog"


def fetch(session: requests.Session, url: str) -> BeautifulSoup:
    response = session.get(url, timeout=30)
    response.raise_for_status()
    return BeautifulSoup(response.text, "html.parser")


def find_chapters(soup: BeautifulSoup, base_url: str) -> list[Chapter]:
    results: list[Chapter] = []
    seen: set[str] = set()
    for anchor in soup.find_all("a", href=True):
        url = urljoin(base_url, anchor["href"])
        parsed = urlparse(url)
        if parsed.netloc != urlparse(base_url).netloc or not CHAPTER_PATH.fullmatch(parsed.path):
            continue
        if url in seen:
            continue
        seen.add(url)
        title = anchor.get_text(" ", strip=True) or parsed.path.rsplit("/", 1)[-1]
        chapter_match = re.search(r"\bchapter\s*(\d+)", title, re.I)
        if not chapter_match:
            chapter_match = re.search(r"chapter[-_ ]*(\d+)", parsed.path.rsplit("/", 1)[-1], re.I)
        number = int(chapter_match.group(1)) if chapter_match else None
        if number is None and title.casefold() in {"read", "read now"}:
            number = 1
        results.append(Chapter(title, url, number))
    return sorted(results, key=lambda chapter: chapter.number if chapter.number is not None else float("inf"))


def is_locked(anchor: BeautifulSoup) -> bool:
    container = anchor.find_parent(["li", "div", "article"]) or anchor
    text = " ".join(container.stripped_strings)
    attrs = " ".join(str(value) for tag in container.find_all(True) for value in tag.attrs.values())
    return bool(LOCKED_MARKERS.search(text + " " + attrs))


def extract_content(soup: BeautifulSoup) -> str:
    for selector in CONTENT_SELECTORS:
        container = soup.select_one(selector)
        if container:
            paragraphs = [p.get_text(" ", strip=True) for p in container.find_all("p")]
            text = "\n\n".join(part for part in paragraphs if part)
            if text:
                return text
            return container.get_text("\n", strip=True)
    return ""


def safe_name(value: str) -> str:
    cleaned = re.sub(r"[\\/*?:\"<>|]", "", value).strip().rstrip(".")
    return (cleaned[:90] or "chapter")


def run() -> int:
    value = input("Novel URL: ").strip()
    try:
        base_url, book_id, catalog_url = parse_book_url(value)
        choice = input("Download [A]ll chapters or a [R]ange? [A]: ").strip().lower()
        start = end = None
        if choice in {"r", "range"}:
            start_value = input("Start chapter (blank = first): ").strip()
            end_value = input("End chapter (blank = last): ").strip()
            start = int(start_value) if start_value else None
            end = int(end_value) if end_value else None
            if (start is not None and start < 1) or (end is not None and end < 1):
                raise ValueError("Chapter numbers must be at least 1.")
            if start is not None and end is not None and start > end:
                raise ValueError("Start chapter must not exceed end chapter.")
        elif choice not in {"", "a", "all"}:
            raise ValueError("Choose A for all chapters or R for a range.")
    except ValueError as error:
        print(f"Invalid input: {error}", file=sys.stderr)
        return 2

    output_dir = Path(f"novel_{book_id}")
    output_dir.mkdir(parents=True, exist_ok=True)
    session = requests.Session()
    session.headers.update({"User-Agent": "ScraperNavel/0.1 (polite chapter downloader)"})

    try:
        catalog = fetch(session, catalog_url)
    except requests.RequestException as error:
        print(f"Could not load catalog {catalog_url}: {error}", file=sys.stderr)
        return 1

    links = find_chapters(catalog, base_url)
    anchors = {urljoin(base_url, anchor["href"]): anchor for anchor in catalog.find_all("a", href=True)}
    free_chapters = [chapter for chapter in links if not is_locked(anchors[chapter.url])]
    if not links:
        print("No chapter links found. The site may load its catalog with JavaScript or use a different URL structure.")
        return 1
    print(f"Found {len(links)} chapter links; {len(free_chapters)} appear free from catalog markers.")
    if start is not None or end is not None:
        free_chapters = [chapter for chapter in free_chapters if chapter.number is not None
                         and (start is None or chapter.number >= start)
                         and (end is None or chapter.number <= end)]
    print(f"Selected {len(free_chapters)} chapters.")

    saved = 0
    for chapter in free_chapters:
        number = chapter.number
        label = f"{number:04d}" if number is not None else "unknown_" + chapter.url.rsplit("_", 1)[-1].strip("/")
        print(f"Fetching chapter {number if number is not None else '?'}: {chapter.title}", flush=True)
        try:
            content = extract_content(fetch(session, chapter.url))
        except requests.RequestException as error:
            print(f"Skipping chapter {number}: {error}")
            continue
        if not content:
            print(f"Skipping {chapter.title}: no chapter text was detected (it may be locked or dynamically rendered).")
            continue
        destination = output_dir / f"{label}_{safe_name(chapter.title)}.txt"
        destination.write_text(f"{chapter.title}\n\n{content}\n", encoding="utf-8")
        saved += 1
        print(f"Saved {destination}")
        time.sleep(1.5)

    print(f"Finished: saved {saved} chapters in {output_dir.resolve()}")
    print("Free/locked status depends on catalog markers; verify results against the site.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(run())
    except KeyboardInterrupt:
        print("\nStopped by Ctrl+C. Chapters already saved remain in the output folder.")
        raise SystemExit(130)
