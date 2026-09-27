"""
Export a Markdown paper to HTML, DOCX and PDF (LibreOffice headless).

    python tools/export_paper.py paper/Ghost_in_the_Machine_v4_Paper.md

Requires `pip install markdown` and a LibreOffice install (`soffice` on PATH).
"""

import subprocess
import sys
from pathlib import Path

import markdown

CSS = """
body { font-family: 'DejaVu Serif', Georgia, serif; font-size: 10.5pt; line-height: 1.45; max-width: 46em; margin: 2em auto; color: #111; }
h1 { font-size: 18pt; line-height: 1.2; } h2 { font-size: 14pt; margin-top: 1.6em; } h3 { font-size: 11.5pt; }
table { border-collapse: collapse; margin: 0.8em 0; font-size: 8.5pt; }
th, td { border: 1px solid #bbb; padding: 3px 6px; vertical-align: top; }
th { background: #f0efec; }
code { font-family: 'DejaVu Sans Mono', monospace; font-size: 8.5pt; }
pre { background: #f6f6f4; padding: 0.6em; font-size: 8.5pt; white-space: pre-wrap; }
blockquote { border-left: 3px solid #bbb; margin-left: 0; padding-left: 1em; color: #333; }
img { max-width: 100%; }
"""


def main(md_path: str) -> None:
    src = Path(md_path).resolve()
    html = markdown.markdown(src.read_text(encoding="utf-8"), extensions=["tables", "fenced_code", "sane_lists"])
    html = html.replace('src="../figures/', f'src="{(src.parent.parent / "figures").as_posix()}/')
    out_html = src.with_suffix(".html")
    out_html.write_text(f"<!doctype html><html><head><meta charset='utf-8'><title>{src.stem}</title>"
                        f"<style>{CSS}</style></head><body>{html}</body></html>", encoding="utf-8")
    for fmt, flt in (("docx", "docx:MS Word 2007 XML"), ("pdf", "pdf:writer_web_pdf_Export")):
        subprocess.run(["soffice", "--headless", "--convert-to", flt, "--outdir", str(src.parent), str(out_html)],
                       check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    out_html.unlink()
    print("wrote", src.with_suffix(".docx"), "and", src.with_suffix(".pdf"))


if __name__ == "__main__":
    main(sys.argv[1])
