from __future__ import annotations

import argparse
from pathlib import Path

import requests
from pypdf import PdfReader


SOURCES = [
    {
        "grade": 9,
        "name": "nie_grade9_english_teachers_guide",
        "url": "https://www.nie.lk/pdffiles/tg/eGr09TG%20English.pdf",
    },
    {
        "grade": 10,
        "name": "nie_grade10_english_teachers_guide",
        "url": "https://www.nie.lk/pdffiles/tg/e10tim107.pdf",
    },
]


def download(url: str, path: Path) -> None:
    response = requests.get(url, timeout=90)
    response.raise_for_status()
    path.write_bytes(response.content)


def split_pdf(pdf_path: Path, output_dir: Path, grade: int, source_url: str, pages_per_doc: int) -> int:
    reader = PdfReader(str(pdf_path))
    count = 0
    for start in range(0, len(reader.pages), pages_per_doc):
        end = min(start + pages_per_doc, len(reader.pages))
        text = "\n".join(reader.pages[index].extract_text() or "" for index in range(start, end))
        if len(text.strip()) < 150:
            continue
        header = (
            f"# Grade {grade} English Teachers Guide — pages {start + 1}-{end}\n\n"
            f"Official source: {source_url}\n\n"
        )
        filename = f"official_grade{grade}_pages_{start + 1:03d}_{end:03d}.md"
        (output_dir / filename).write_text(header + text, encoding="utf-8")
        count += 1
    return count


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pages-per-doc", type=int, default=8)
    parser.add_argument("--keep-pdfs", action="store_true")
    args = parser.parse_args()

    project_root = Path(__file__).resolve().parents[1]
    pdf_dir = project_root / "data" / "official_sources"
    knowledge_dir = project_root / "data" / "knowledge_base"
    pdf_dir.mkdir(parents=True, exist_ok=True)

    total = 0
    for source in SOURCES:
        pdf_path = pdf_dir / f"{source['name']}.pdf"
        print(f"Downloading {source['url']}")
        download(source["url"], pdf_path)
        output_dir = knowledge_dir / f"grade{source['grade']}" / "official"
        output_dir.mkdir(parents=True, exist_ok=True)
        produced = split_pdf(
            pdf_path,
            output_dir,
            source["grade"],
            source["url"],
            args.pages_per_doc,
        )
        total += produced
        print(f"Created {produced} retrieval documents for Grade {source['grade']}")
        if not args.keep_pdfs:
            pdf_path.unlink(missing_ok=True)

    print(f"Done. Created {total} official page-range documents.")
    if total < 20:
        print("Tip: rerun with --pages-per-doc 5 to create more than 20 documents.")


if __name__ == "__main__":
    main()
