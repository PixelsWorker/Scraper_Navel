from __future__ import annotations

import argparse
from datetime import datetime, timezone
from html import escape
from pathlib import Path
import re
import uuid
from zipfile import ZIP_DEFLATED, ZIP_STORED, ZipFile


def chapter_order(path: Path) -> tuple:
    chapter_match = re.search(r"\bchapter\s*(\d+)", path.stem, re.I)
    first_number = re.search(r"\d+", path.stem)
    number = int(chapter_match.group(1)) if chapter_match else (
        int(first_number.group()) if first_number else float("inf")
    )
    natural_name = tuple(
        (0, int(part)) if part.isdigit() else (1, part.casefold())
        for part in re.split(r"(\d+)", path.name)
    )
    return number, natural_name


def read_chapter(path: Path) -> tuple[str, str]:
    content = path.read_text(encoding="utf-8-sig").strip()
    if not content:
        return "", ""
    title, _, body = content.partition("\n")
    title = title.strip()
    body = body.strip()
    if not body:
        title, body = path.stem, content
    body = re.sub(r"\A[=\-]{3,}\s*\n", "", body)
    paragraphs = [escape(part.strip()) for part in re.split(r"\n\s*\n", body) if part.strip()]
    paragraphs = [part.replace("\n", "<br/>") for part in paragraphs]
    return title, "\n".join(f"<p>{part}</p>" for part in paragraphs)


def convert(folder: Path, start: int | None = None, end: int | None = None) -> Path:
    if start is not None and start < 1 or end is not None and end < 1:
        raise ValueError("Chapter numbers must be at least 1.")
    if start is not None and end is not None and start > end:
        raise ValueError("Start chapter must not exceed end chapter.")
    if not folder.is_dir():
        raise ValueError(f"Folder does not exist: {folder}")
    files = sorted(
        (path for path in folder.iterdir() if path.is_file() and path.suffix.lower() == ".txt"),
        key=chapter_order,
    )
    if not files:
        raise ValueError("No TXT files found directly inside this folder.")
    if start is not None or end is not None:
        files = [path for path in files if chapter_order(path)[0] != float("inf")
                 and (start is None or chapter_order(path)[0] >= start)
                 and (end is None or chapter_order(path)[0] <= end)]
        if not files:
            raise ValueError("No TXT files match the selected chapter range.")
    chapters = []
    for path in files:
        title, body = read_chapter(path)
        if body:
            chapters.append((path, title, body))
        else:
            print(f"Skipping empty file: {path.name}")
    if not chapters:
        raise ValueError("All TXT files are empty.")

    range_label = f"_chapters_{start or 1}-{end or 'last'}" if start is not None or end is not None else ""
    output_stem = f"{folder.name}{range_label}"
    output = folder / f"{output_stem}.epub"
    suffix = 2
    while output.exists():
        output = folder / f"{output_stem}_{suffix}.epub"
        suffix += 1
    book_title = escape(folder.name)
    identifier = str(uuid.uuid4())
    modified = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    manifest = []
    spine = []
    navigation = []
    with ZipFile(output, "x", compression=ZIP_DEFLATED) as book:
        book.writestr("mimetype", "application/epub+zip", compress_type=ZIP_STORED)
        book.writestr("META-INF/container.xml", '''<?xml version="1.0" encoding="utf-8"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
<rootfiles><rootfile full-path="EPUB/package.opf" media-type="application/oebps-package+xml"/></rootfiles>
</container>''')
        for index, (path, title, body) in enumerate(chapters, 1):
            filename = f"chapter_{index:04d}.xhtml"
            manifest.append(f'<item id="chapter_{index}" href="{filename}" media-type="application/xhtml+xml"/>')
            spine.append(f'<itemref idref="chapter_{index}"/>')
            navigation.append(f'<li><a href="{filename}">{escape(title)}</a></li>')
            book.writestr(f"EPUB/{filename}", f'''<?xml version="1.0" encoding="utf-8"?>
<html xmlns="http://www.w3.org/1999/xhtml" lang="en">
<head><title>{escape(title)}</title><link rel="stylesheet" href="style.css"/></head>
<body><section><h1>{escape(title)}</h1>{body}</section></body></html>''')
            print(f"{index:03d}. {path.name}")
        book.writestr("EPUB/style.css", "body { line-height: 1.5; margin: 5%; } h1 { font-size: 1.5em; } section { break-before: page; page-break-before: always; } p { margin: 0 0 1em; }")
        book.writestr("EPUB/nav.xhtml", f'''<?xml version="1.0" encoding="utf-8"?>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops" lang="en">
<head><title>Contents</title></head><body>
<nav epub:type="toc"><h1>{book_title}</h1><ol>{''.join(navigation)}</ol></nav>
</body></html>''')
        book.writestr("EPUB/package.opf", f'''<?xml version="1.0" encoding="utf-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="book-id">
<metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
<dc:identifier id="book-id">urn:uuid:{identifier}</dc:identifier>
<dc:title>{book_title}</dc:title><dc:language>en</dc:language>
<meta property="dcterms:modified">{modified}</meta></metadata>
<manifest><item id="nav" href="nav.xhtml" media-type="application/xhtml+xml" properties="nav"/>
<item id="style" href="style.css" media-type="text/css"/>{''.join(manifest)}</manifest>
<spine>{''.join(spine)}</spine></package>''')
    print(f"\nCreated EPUB with {len(chapters)} chapters: {output}")
    return output


def main() -> int:
    parser = argparse.ArgumentParser(description="Convert a folder of TXT chapters into one EPUB.")
    parser.add_argument("folder", nargs="?", help="Folder containing chapter TXT files")
    parser.add_argument("--start", type=int, help="First chapter to include (inclusive)")
    parser.add_argument("--end", type=int, help="Last chapter to include (inclusive)")
    args = parser.parse_args()
    try:
        value = args.folder or input("Paste TXT folder path: ")
        start, end = args.start, args.end
        if args.folder is None and start is None and end is None:
            choice = input("Convert [A]ll chapters or a [R]ange? [A]: ").strip().lower()
            if choice in {"r", "range"}:
                start_value = input("Start chapter (blank = first): ").strip()
                end_value = input("End chapter (blank = last): ").strip()
                start = int(start_value) if start_value else None
                end = int(end_value) if end_value else None
            elif choice not in {"", "a", "all"}:
                raise ValueError("Choose A for all chapters or R for a range.")
        convert(Path(value.strip().strip('\"').strip("'")).expanduser().resolve(), start, end)
    except (ValueError, OSError, UnicodeError) as error:
        print(f"Could not create EPUB: {error}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
