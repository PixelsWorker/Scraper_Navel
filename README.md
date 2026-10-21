# Scraper Navel

## TXT folder to EPUB

Run `python txt_to_epub.py` from this directory, then paste the folder containing your TXT chapters. No extra packages are required. Alternatively, run `python txt_to_epub.py "E:\\path\\to\\novel_folder"`.

The converter creates one EPUB inside that folder, with a table of contents and each chapter starting on a new page. EPUB pages reflow with reader font and screen settings, so long chapters can span several pages. Files sort by an explicit `Chapter N` in the filename, then by the first filename number, with natural filename ordering for ties. Empty files are skipped, subfolders are excluded, and existing EPUBs receive a numbered alternative filename.

In interactive mode, choose **A** for all chapters or **R** for a start/end chapter range. Leave the end blank to include all remaining chapters. Ranges include both endpoints and use chapter numbers from filenames, not file positions. Unnumbered files are excluded from ranges. For example: `python txt_to_epub.py "E:\\path\\to\\novel_folder" --start 310 --end 533`, or omit `--end` for chapter 310 onward. Range exports have the range in their EPUB filename.

A small command-line tool that asks for one novel page URL, derives the catalog URL, and saves detected chapter text as UTF-8 text files.

## Run

From this directory, install dependencies and start the scraper:

```powershell
py -m pip install -r requirements.txt
py scraper.py
```

When prompted, enter the novel page URL, for example:

The scraper also asks for **A** (all chapters) or **R** (a chapter range). For chapter 310 onward, choose R, enter 310, and leave the end blank. Chapters are sorted and numbered by detected chapter number. Unknown chapter numbers are excluded from range downloads. Ctrl+C stops cleanly and keeps files already saved.

```text
https://www.example.com/book/example_35964974408530205
```

The scraper derives `https://www.example.com/book/35964974408530205/catalog` and saves chapter files into `novel_35964974408530205/`.

Catalog-based lock detection is heuristic and depends on the site's HTML. Sites that render the catalog or chapter text only with JavaScript need a site-specific browser adapter. Download only content you are allowed to access, and keep requests at a reasonable rate.
