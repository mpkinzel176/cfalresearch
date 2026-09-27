"""
CV ingestion helper for the CFAL website.

WHAT THIS DOES
--------------
Reads the PI's CV (a .docx) in true document order -- interleaving paragraphs
and tables exactly as Word lays them out -- and groups each table under the
most recent preceding heading-like paragraph. It writes the result to
scripts/cv_extract.json.

WHAT THIS DELIBERATELY DOES NOT DO
-----------------------------------
It does NOT try to automatically decide who is a "current" vs. "graduated"
student, resolve duplicate/inconsistent rows (e.g. the same person appearing
in both a "current students" and a "graduated students" table), or fabricate
missing fields (thesis URLs, LinkedIn, etc). CVs like this one mix current and
completed advisees within a single table, reuse ambiguous date formats
("(Est)"), and occasionally contain outright copy/paste errors (see
review-needed.json for a caught example). Reconciling all of that requires
human judgment -- or a careful read-through, as was done when this site was
first built -- not a heuristic that might silently misclassify someone.

HOW TO USE THIS
---------------
1. Run: python scripts/parse_cv.py path/to/CV.docx
2. Open scripts/cv_extract.json and find the section you need
   (e.g. "Ph.D. Students", "Grants/Contracts", "M.S. Students").
3. Manually add/update the corresponding entries in:
     src/data/people/faculty.json
     src/data/people/postdocs.json
     src/data/people/graduate_students.json
     src/data/people/undergraduate_students.json
     src/data/people/alumni.json
     src/data/projects.json
     src/data/sponsors.json
4. Anything you're not confident about -- add a note to
   src/data/review-needed.json instead of guessing. See existing entries
   there for the expected format.
5. Publications are handled separately by scripts/build_publications.py,
   which regenerates src/data/publications.json from the Google Scholar
   scrape (src/data/publications-raw.json).

This script requires `python-docx` (already used elsewhere in this project).
"""
import json
import sys
from pathlib import Path

import docx
from docx.oxml.ns import qn

HEADING_STYLES = {"Heading 1", "Heading 2", "Heading 3", "Title"}


def looks_like_heading(paragraph) -> bool:
    if paragraph.style and paragraph.style.name in HEADING_STYLES:
        return True
    text = paragraph.text.strip()
    if not text:
        return False
    # Short, title-cased lines with no trailing period are often section
    # headers in a CV even when no Word heading style was applied.
    return len(text) < 60 and not text.endswith(".") and text[0].isupper()


def iter_block_items(document):
    body = document.element.body
    for child in body.iterchildren():
        if child.tag == qn('w:p'):
            yield 'paragraph', docx.text.paragraph.Paragraph(child, document)
        elif child.tag == qn('w:tbl'):
            yield 'table', docx.table.Table(child, document)


def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/parse_cv.py path/to/CV.docx")
        sys.exit(1)

    cv_path = Path(sys.argv[1])
    document = docx.Document(str(cv_path))

    sections = []
    current_heading = "(preamble)"
    pending_table_index = 0

    for kind, item in iter_block_items(document):
        if kind == 'paragraph':
            if looks_like_heading(item):
                current_heading = item.text.strip()
        elif kind == 'table':
            rows = [[cell.text.strip() for cell in row.cells] for row in item.rows]
            pending_table_index += 1
            sections.append({
                "heading": current_heading,
                "table_index_in_doc": pending_table_index,
                "rows": rows,
            })

    out_path = Path(__file__).parent / "cv_extract.json"
    out_path.write_text(json.dumps(sections, indent=2), encoding="utf-8")
    print(f"Wrote {len(sections)} tables (grouped by heading) to {out_path}")
    print("Open that file and reconcile it by hand into src/data/ -- see the")
    print("docstring at the top of this script for guidance.")


if __name__ == "__main__":
    main()
