"""
GRACE Prototype — Document Export Helpers
Markdown → PDF and Markdown → DOCX conversion (pure Python, no native deps).
"""
import io
import re

import markdown as md_lib
from docx import Document
from docx.shared import Pt
from xhtml2pdf import pisa


_PDF_CSS = """
@page { size: A4; margin: 2cm 2.2cm; }
body {
    font-family: Helvetica, Arial, sans-serif;
    font-size: 10.5pt;
    color: #163265;
    line-height: 1.45;
}
h1 {
    color: #163265;
    border-bottom: 2px solid #2A7A8A;
    padding-bottom: 4px;
    font-size: 18pt;
    margin-top: 0;
}
h2 { color: #2A7A8A; font-size: 14pt; margin-top: 16pt; }
h3 { color: #163265; font-size: 12pt; margin-top: 12pt; }
h4 { color: #2A7A8A; font-size: 11pt; }
code {
    background: #F3F4F6;
    padding: 1px 4px;
    border-radius: 3px;
    font-family: "Courier New", monospace;
    font-size: 9.5pt;
}
pre {
    background: #F3F4F6;
    padding: 8px;
    border-left: 3px solid #2A7A8A;
    font-family: "Courier New", monospace;
    font-size: 9.5pt;
}
table { border-collapse: collapse; width: 100%; margin: 8pt 0; }
th, td { border: 1px solid #E5E7EB; padding: 5pt; text-align: left; vertical-align: top; }
th { background: #F1F5F9; color: #163265; font-weight: bold; }
blockquote {
    margin: 8pt 0;
    padding: 4pt 12pt;
    border-left: 3px solid #2A7A8A;
    background: #F9FAFB;
    color: #475569;
}
ul, ol { margin: 6pt 0 6pt 18pt; }
li { margin: 2pt 0; }
strong { color: #163265; }
"""


def markdown_to_pdf_bytes(markdown_text: str) -> bytes:
    html_body = md_lib.markdown(
        markdown_text,
        extensions=["tables", "fenced_code", "sane_lists", "nl2br"],
    )
    html = f"<html><head><style>{_PDF_CSS}</style></head><body>{html_body}</body></html>"
    buf = io.BytesIO()
    result = pisa.CreatePDF(html, dest=buf, encoding="utf-8")
    if result.err:
        raise RuntimeError(f"PDF generation failed: {result.err}")
    return buf.getvalue()


_INLINE_RE = re.compile(r"(\*\*[^*\n]+\*\*|\*[^*\n]+\*|`[^`\n]+`)")


def _add_runs_with_inline_formatting(paragraph, text: str):
    """Split a line on **bold**, *italic*, `code` and apply runs accordingly."""
    parts = _INLINE_RE.split(text)
    for part in parts:
        if not part:
            continue
        if part.startswith("**") and part.endswith("**") and len(part) >= 4:
            run = paragraph.add_run(part[2:-2])
            run.bold = True
        elif part.startswith("*") and part.endswith("*") and len(part) >= 3:
            run = paragraph.add_run(part[1:-1])
            run.italic = True
        elif part.startswith("`") and part.endswith("`") and len(part) >= 3:
            run = paragraph.add_run(part[1:-1])
            run.font.name = "Courier New"
            run.font.size = Pt(9.5)
        else:
            paragraph.add_run(part)


def markdown_to_docx_bytes(markdown_text: str) -> bytes:
    """Convert markdown to DOCX bytes. Supports headings, paragraphs, bullets,
    numbered lists, bold/italic/code inline, simple pipe tables."""
    doc = Document()
    lines = markdown_text.split("\n")
    i = 0
    while i < len(lines):
        line = lines[i].rstrip()

        if not line.strip():
            i += 1
            continue

        # Headings
        if line.startswith("#### "):
            doc.add_heading(line[5:], level=4)
        elif line.startswith("### "):
            doc.add_heading(line[4:], level=3)
        elif line.startswith("## "):
            doc.add_heading(line[3:], level=2)
        elif line.startswith("# "):
            doc.add_heading(line[2:], level=1)
        # Bullet list
        elif re.match(r"^[\-\*]\s", line):
            p = doc.add_paragraph(style="List Bullet")
            _add_runs_with_inline_formatting(p, line[2:].strip())
        # Numbered list
        elif re.match(r"^\d+\.\s", line):
            content = re.sub(r"^\d+\.\s", "", line)
            p = doc.add_paragraph(style="List Number")
            _add_runs_with_inline_formatting(p, content)
        # Blockquote
        elif line.startswith("> "):
            p = doc.add_paragraph()
            p.paragraph_format.left_indent = Pt(18)
            run = p.add_run(line[2:].strip())
            run.italic = True
        # Pipe table — accumulate consecutive lines
        elif line.startswith("|") and i + 1 < len(lines) and re.match(r"^\|[\s\-:|]+\|$", lines[i + 1].strip()):
            header_cells = [c.strip() for c in line.strip().strip("|").split("|")]
            i += 2  # skip header and separator
            rows = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                rows.append([c.strip() for c in lines[i].strip().strip("|").split("|")])
                i += 1
            ncols = len(header_cells)
            table = doc.add_table(rows=1 + len(rows), cols=ncols)
            table.style = "Light Grid"
            for c_idx, header in enumerate(header_cells):
                cell = table.rows[0].cells[c_idx]
                cell.text = ""
                p = cell.paragraphs[0]
                run = p.add_run(header)
                run.bold = True
            for r_idx, row in enumerate(rows):
                for c_idx in range(ncols):
                    cell_text = row[c_idx] if c_idx < len(row) else ""
                    table.rows[r_idx + 1].cells[c_idx].text = ""
                    _add_runs_with_inline_formatting(
                        table.rows[r_idx + 1].cells[c_idx].paragraphs[0],
                        cell_text,
                    )
            continue  # skip the i += 1 at the bottom
        # Code fence — read until closing fence
        elif line.startswith("```"):
            i += 1
            code_lines = []
            while i < len(lines) and not lines[i].startswith("```"):
                code_lines.append(lines[i])
                i += 1
            p = doc.add_paragraph()
            run = p.add_run("\n".join(code_lines))
            run.font.name = "Courier New"
            run.font.size = Pt(9.5)
        # Horizontal rule
        elif re.match(r"^[\-_*]{3,}$", line.strip()):
            doc.add_paragraph("─" * 60)
        # Plain paragraph
        else:
            p = doc.add_paragraph()
            _add_runs_with_inline_formatting(p, line)

        i += 1

    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()
