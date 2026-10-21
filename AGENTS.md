# Repository Guidelines

## Scope and Verified State

Read the parent `../AGENTS.md` together with this file. These instructions apply to this repository and its descendants. Verified against the local files on 2026-10-21: this is a Python CLI repository, with no React/Vite application, architecture packet, or G00 implementation in this directory. The parent document's descriptions of those assets do not describe the current repository.

## Project Structure

- `scraper.py`: interactive novel chapter downloader using Requests and Beautiful Soup; saves UTF-8 TXT files in `novel_<book_id>/` relative to the working directory.
- `txt_to_epub.py`: standard-library TXT-to-EPUB converter with interactive and command-line chapter selection.
- `requirements.txt`: scraper dependencies.
- `README.md`: usage instructions; update when command behavior changes.
- `venv/` and `__pycache__/`: local generated directories; do not commit them.
- `../evidence/` and `../worktree/`: workspace directories outside this repository. Preserve evidence originals.

## Commands

Run from `E:\Projects\Scraper_Navel\Scraper_Navel`:

```powershell
py -m pip install -r requirements.txt
py scraper.py
py txt_to_epub.py --help
py txt_to_epub.py "E:\path\to\novel_folder" --start 310 --end 533
git status -sb
git diff --check
git diff --cached --check
```

Running the scraper makes network requests and writes chapter files. Running the converter writes an EPUB into the selected folder. Use temporary fixture folders for verification. The converter requires no third-party packages. No automated test suite, build scripts, lint configuration, or coverage target is currently present.

## Coding Conventions

Follow the existing Python style: four-space indentation, `snake_case` functions and variables, uppercase module constants, type annotations, and small focused helpers. Preserve UTF-8 text handling, Windows-compatible paths, and import-safe entry points. Keep dependencies in `requirements.txt`; prefer the standard library for EPUB conversion. Keep Markdown concise and distinguish observed behavior from proposals.

## Behavior and Validation

Preserve inclusive chapter ranges, chapter-number ordering, handling of unknown chapter numbers, and clear invalid-input messages. The scraper uses heuristic catalog lock detection and static HTML parsing; do not describe either as guaranteed or claim support for JavaScript-rendered content without implementation and verification. Keep request pacing and graceful interruption behavior.

For scraper changes, verify parsing, duplicate links, range selection, missing content, and request failures with local HTML fixtures or mocked requests. For converter changes, verify natural ordering, empty files, range boundaries, text escaping, EPUB ZIP/XML structure, and numbered output names that preserve existing EPUBs. Use temporary files and avoid modifying downloaded novels during checks. Report exact validation commands and any checks not run.

## Git and Change Management

Inspect staged and unstaged changes before editing; preserve unrelated user work. At inspection, this repository was on an unborn `main` branch with existing staged files. Do not assume the parent document's reconciliation commit exists here. Follow the parent's `dev` or feature-branch convention for development, and do not force-push. Use imperative commit subjects and describe scope and validation in pull requests. Do not commit downloaded chapters, generated EPUBs, or virtual environments. Draft documentation alone does not authorize implementation or publication.
