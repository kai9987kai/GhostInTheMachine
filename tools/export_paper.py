"""
Export a Markdown paper to DOCX (pandoc) and PDF (pandoc HTML + headless Chromium).

    python tools/export_paper.py paper/Ghost_in_the_Machine_v4_Paper.md

Requirements: `pip install pypandoc_binary` (bundles pandoc) and a Chromium/Chrome
binary (set CHROME=/path/to/chrome if it is not auto-detected).
"""

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import pypandoc

CSS = """
body { font-family: 'DejaVu Serif', Georgia, serif; font-size: 10.5pt; line-height: 1.42; max-width: 44em; margin: 0 auto; color: #111; }
h1 { font-size: 17pt; line-height: 1.2; margin-top: 0; } h2 { font-size: 13.5pt; margin-top: 1.5em; } h3 { font-size: 11.5pt; }
table { border-collapse: collapse; margin: 0.8em 0; font-size: 8.3pt; width: 100%; }
th, td { border: 1px solid #bbb; padding: 3px 5px; vertical-align: top; }
th { background: #f0efec; }
code { font-family: 'DejaVu Sans Mono', monospace; font-size: 8.3pt; }
blockquote { border-left: 3px solid #bbb; margin-left: 0; padding-left: 1em; color: #333; }
img { max-width: 100%; }
@page { size: A4; margin: 18mm 16mm; }
"""

CANDIDATES = [
    os.environ.get("CHROME", ""),
    "/opt/pw-browsers/chromium-1194/chrome-linux/chrome",
    shutil.which("chromium") or "", shutil.which("chromium-browser") or "",
    shutil.which("google-chrome") or "", shutil.which("chrome") or "",
]


def main(md_path: str) -> None:
    src = Path(md_path).resolve()
    res_path = str(src.parent)
    docx = src.with_suffix(".docx")
    pypandoc.convert_file(str(src), "docx", outputfile=str(docx),
                          extra_args=[f"--resource-path={res_path}", "--toc", "--toc-depth=2"])
    print("wrote", docx)

    chrome = next((c for c in CANDIDATES if c and Path(c).exists()), None)
    if chrome is None:
        print("no Chromium found; skipping PDF")
        return
    with tempfile.TemporaryDirectory() as tmp:
        css = Path(tmp) / "paper.css"
        css.write_text(CSS, encoding="utf-8")
        html = Path(tmp) / "paper.html"
        pypandoc.convert_file(str(src), "html5", outputfile=str(html),
                              extra_args=["--standalone", "--embed-resources", f"--resource-path={res_path}",
                                          f"--css={css}", "--metadata", "pagetitle=" + src.stem])
        pdf = src.with_suffix(".pdf")
        subprocess.run([chrome, "--headless=new", "--no-sandbox", "--disable-gpu", "--no-pdf-header-footer",
                        f"--print-to-pdf={pdf}", html.as_uri()], check=True,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print("wrote", pdf)


if __name__ == "__main__":
    main(sys.argv[1])
