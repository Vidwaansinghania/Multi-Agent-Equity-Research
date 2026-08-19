"""Method 2 workpapers — every agent's full output in one Word document.

    python build_workpapers.py "<run folder>" [-o OUT.docx]

The audit trail, not the deliverable. Nothing is summarised, shortened or
stripped: what the agent wrote is what lands in the file, in stage order, one
section per agent. The point is that a disputed line in the report can be traced
back to the agent that produced it without opening ten files.

Reads whatever exists. A run missing a stage produces a document missing that
section and a line saying so, rather than a failed build.
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import m2md

try:
    from docx import Document
    from docx.enum.section import WD_SECTION
    from docx.enum.table import WD_TABLE_ALIGNMENT
    from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn
    from docx.shared import Inches, Pt, RGBColor
except ImportError:  # pragma: no cover
    sys.exit("python-docx is not available in this interpreter.")

INK = RGBColor(0x1A, 0x1A, 0x1A)
GREY = RGBColor(0x6B, 0x6B, 0x6B)
RULE = "D8D8D8"
BAND = "F2F2F2"

# (filename, section title, stage label) in the order a run produces them.
SECTIONS = [
    ("run.md", "Preflight and run context", "Stage 0 · orchestrator"),
    ("analyst-fundamentals.md", "Fundamentals analyst", "Stage 1 · Sonnet"),
    ("analyst-market.md", "Market analyst", "Stage 1 · Sonnet"),
    ("analyst-news.md", "News and events analyst", "Stage 1 · Sonnet"),
    ("analyst-industry.md", "Industry analyst", "Stage 1 · Sonnet"),
    ("valuation.md", "Valuation — base case", "Stage 2 · Opus"),
    ("bull.md", "Bull attack", "Stage 3 · Opus"),
    ("bear.md", "Bear attack", "Stage 3 · Opus"),
    ("decision.md", "Judgment — the decision record", "Stage 4 · Opus"),
    ("risk.md", "Risk gate", "Stage 5 · Opus"),
    ("report.md", "Report as published", "Stage 6 · Opus"),
    ("comparison.md", "Comparison against Method 1", "Stage 7 · orchestrator"),
]


# ------------------------------------------------------------------ styling --

def _shade(cell, hexfill):
    el = OxmlElement("w:shd")
    el.set(qn("w:val"), "clear")
    el.set(qn("w:fill"), hexfill)
    cell._tc.get_or_add_tcPr().append(el)


def _borders(table):
    tbl = table._tbl.tblPr
    borders = OxmlElement("w:tblBorders")
    for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
        e = OxmlElement("w:" + edge)
        e.set(qn("w:val"), "single")
        e.set(qn("w:sz"), "4")
        e.set(qn("w:color"), RULE)
        borders.append(e)
    tbl.append(borders)


def setup_styles(doc):
    normal = doc.styles["Normal"]
    normal.font.name = "Calibri"
    normal.font.size = Pt(10)
    normal.font.color.rgb = INK
    pf = normal.paragraph_format
    pf.space_after = Pt(6)
    pf.line_spacing = 1.15

    for name, size, colour in (("Heading 1", 16, INK), ("Heading 2", 13, INK),
                               ("Heading 3", 11, INK), ("Heading 4", 10, GREY)):
        st = doc.styles[name]
        st.font.name = "Cambria"
        st.font.size = Pt(size)
        st.font.color.rgb = colour
        st.font.bold = True
        st.paragraph_format.space_before = Pt(12)
        st.paragraph_format.space_after = Pt(4)
        st.paragraph_format.keep_with_next = True

    for sec in doc.sections:
        sec.left_margin = sec.right_margin = Inches(0.9)
        sec.top_margin = Inches(0.8)
        sec.bottom_margin = Inches(0.8)


def footer_text(doc, text):
    for sec in doc.sections:
        p = sec.footer.paragraphs[0]
        p.text = text
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        for run in p.runs:
            run.font.size = Pt(7.5)
            run.font.color.rgb = GREY


# ------------------------------------------------------------------ writing --

def add_runs(par, text):
    for chunk, bold, italic, mono in m2md.inline_runs(text):
        if not chunk:
            continue
        r = par.add_run(chunk)
        r.bold, r.italic = bold, italic
        if mono:
            r.font.name = "Consolas"
            r.font.size = Pt(9)


def render(doc, blocks, base_level=2):
    """Render parsed blocks, pushing headings below the section heading."""
    for b in blocks:
        kind = b["type"]

        if kind == "heading":
            level = min(base_level + b["level"] - 1, 4)
            p = doc.add_paragraph(style="Heading %d" % level)
            add_runs(p, b["text"])

        elif kind == "para":
            p = doc.add_paragraph()
            add_runs(p, b["text"])

        elif kind == "list":
            for indent, text in b["items"]:
                style = "List Number" if b["ordered"] else "List Bullet"
                try:
                    p = doc.add_paragraph(style=style)
                except KeyError:
                    p = doc.add_paragraph()
                    text = ("- " if not b["ordered"] else "") + text
                p.paragraph_format.left_indent = Inches(0.25 + 0.25 * min(indent, 3))
                p.paragraph_format.space_after = Pt(2)
                add_runs(p, text)

        elif kind == "table":
            cols = max(1, len(b["header"]))
            t = doc.add_table(rows=1, cols=cols)
            t.alignment = WD_TABLE_ALIGNMENT.CENTER
            t.autofit = True
            _borders(t)
            for j, head in enumerate(b["header"]):
                cell = t.rows[0].cells[j]
                cell.text = ""
                p = cell.paragraphs[0]
                r = p.add_run(head)
                r.bold = True
                r.font.size = Pt(8.5)
                _shade(cell, BAND)
            for row in b["rows"]:
                cells = t.add_row().cells
                for j, val in enumerate(row[:cols]):
                    cells[j].text = ""
                    p = cells[j].paragraphs[0]
                    p.paragraph_format.space_after = Pt(1)
                    add_runs(p, val)
                    for r in p.runs:
                        r.font.size = Pt(8.5)
            doc.add_paragraph().paragraph_format.space_after = Pt(2)

        elif kind == "code":
            p = doc.add_paragraph()
            p.paragraph_format.left_indent = Inches(0.25)
            p.paragraph_format.space_after = Pt(6)
            r = p.add_run(b["text"])
            r.font.name = "Consolas"
            r.font.size = Pt(8)

        elif kind == "quote":
            p = doc.add_paragraph()
            p.paragraph_format.left_indent = Inches(0.3)
            add_runs(p, b["text"])
            for r in p.runs:
                r.italic = True
                r.font.color.rgb = GREY

        elif kind == "callout":
            p = doc.add_paragraph()
            p.paragraph_format.left_indent = Inches(0.3)
            head = b["title"] or b["kind"].title()
            r = p.add_run(head + " — ")
            r.bold = True
            add_runs(p, b["text"])

        elif kind == "rule":
            p = doc.add_paragraph()
            p.paragraph_format.space_before = Pt(2)
            p.paragraph_format.space_after = Pt(6)


def frontmatter_table(doc, fm):
    """Render decision.md's typed fields as a table so the call is visible."""
    keep = [("rating", "Rating"), ("target", "Twelve-month target"),
            ("reference_price", "Reference price"),
            ("expected_total_return", "Expected total return"),
            ("conviction", "Conviction"), ("marginal", "Marginal"),
            ("decided_by", "Decided by"),
            ("alpha_vantage_calls", "Market-data calls")]
    rows = [(label, str(fm[key])) for key, label in keep if key in fm]
    if not rows:
        return
    t = doc.add_table(rows=0, cols=2)
    _borders(t)
    for label, val in rows:
        cells = t.add_row().cells
        cells[0].text = ""
        r = cells[0].paragraphs[0].add_run(label)
        r.bold = True
        r.font.size = Pt(9)
        _shade(cells[0], BAND)
        cells[1].text = ""
        r2 = cells[1].paragraphs[0].add_run(val)
        r2.font.size = Pt(9)
    doc.add_paragraph()


def cover(doc, meta, present, missing):
    for _ in range(3):
        doc.add_paragraph()

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run("METHOD 2 — WORKPAPERS")
    r.font.name = "Cambria"
    r.font.size = Pt(11)
    r.font.color.rgb = GREY
    r.bold = True

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run(meta.get("company") or meta.get("ticker", "Unknown"))
    r.font.name = "Cambria"
    r.font.size = Pt(24)
    r.bold = True

    sub = " · ".join(x for x in (meta.get("ticker"), meta.get("exchange"),
                                meta.get("run_date")) if x)
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run(sub)
    r.font.size = Pt(11)
    r.font.color.rgb = GREY

    if meta.get("rating"):
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        bits = [meta["rating"]]
        if meta.get("target"):
            bits.append("target %s%s" % (meta.get("_cur", "$"), meta["target"]))
        r = p.add_run("   ".join(bits))
        r.font.size = Pt(13)
        r.bold = True

    doc.add_paragraph()
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run("Every agent's full output, in stage order, unedited. "
                  "Educational and research use only; not investment advice.")
    r.font.size = Pt(9)
    r.font.color.rgb = GREY
    r.italic = True

    doc.add_paragraph()
    doc.add_paragraph()

    p = doc.add_paragraph(style="Heading 3")
    p.add_run("Contents")
    for title, stage in present:
        q = doc.add_paragraph()
        q.paragraph_format.space_after = Pt(1)
        q.paragraph_format.left_indent = Inches(0.2)
        r = q.add_run(title)
        r.font.size = Pt(9.5)
        r2 = q.add_run("   " + stage)
        r2.font.size = Pt(8.5)
        r2.font.color.rgb = GREY

    if missing:
        q = doc.add_paragraph()
        q.paragraph_format.left_indent = Inches(0.2)
        r = q.add_run("Not present in this run: " + ", ".join(missing))
        r.font.size = Pt(8.5)
        r.font.color.rgb = GREY
        r.italic = True


# --------------------------------------------------------------------- main --

def build(run_dir, out_path=None):
    run_dir = os.path.abspath(run_dir)
    if not os.path.isdir(run_dir):
        sys.exit("No such run folder: %s" % run_dir)

    meta, _ = m2md.read_note(os.path.join(run_dir, "decision.md"))
    if not meta.get("ticker"):
        meta.setdefault("ticker", os.path.basename(os.path.dirname(
            os.path.dirname(run_dir))) or "RUN")
    meta.setdefault("run_date", os.path.basename(run_dir))

    present, missing = [], []
    for fname, title, stage in SECTIONS:
        if os.path.exists(os.path.join(run_dir, fname)):
            present.append((title, stage))
        else:
            missing.append(title)

    doc = Document()
    setup_styles(doc)
    footer_text(doc, "Method 2 workpapers · %s · %s · educational and research use only"
                % (meta.get("ticker", ""), meta.get("run_date", "")))
    cover(doc, meta, present, missing)

    for fname, title, stage in SECTIONS:
        path = os.path.join(run_dir, fname)
        if not os.path.exists(path):
            continue

        doc.add_paragraph().add_run().add_break(WD_BREAK.PAGE)
        h = doc.add_paragraph(style="Heading 1")
        h.add_run(title)
        s = doc.add_paragraph()
        s.paragraph_format.space_after = Pt(10)
        r = s.add_run("%s · %s" % (stage, fname))
        r.font.size = Pt(8.5)
        r.font.color.rgb = GREY

        fm, blocks = m2md.read_note(path)
        if fname == "decision.md" and fm:
            frontmatter_table(doc, fm)
        render(doc, blocks, base_level=2)

    csv_path = os.path.join(run_dir, "statements.csv")
    if os.path.exists(csv_path):
        doc.add_paragraph().add_run().add_break(WD_BREAK.PAGE)
        doc.add_paragraph(style="Heading 1").add_run("Ten-year statements")
        p = doc.add_paragraph()
        r = p.add_run("The full series is in the model workbook for this run. "
                      "Line-item counts by statement:")
        r.font.size = Pt(9.5)
        counts = {}
        with open(csv_path, "r", encoding="utf-8-sig") as fh:
            next(fh, None)
            for line in fh:
                key = line.split(",", 1)[0].strip()
                if key:
                    counts[key] = counts.get(key, 0) + 1
        for key in sorted(counts):
            q = doc.add_paragraph()
            q.paragraph_format.left_indent = Inches(0.25)
            q.paragraph_format.space_after = Pt(1)
            rr = q.add_run("%s — %d line items" % (key, counts[key]))
            rr.font.size = Pt(9)

    if out_path is None:
        exports = os.path.join(run_dir, "exports")
        os.makedirs(exports, exist_ok=True)
        out_path = os.path.join(exports, "%s_Method2_Workpapers_%s.docx"
                                % (meta.get("ticker", "RUN"),
                                   meta.get("run_date", "undated")))
    doc.save(out_path)
    return out_path, len(present), missing


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("run_dir", help="the run folder, e.g. 'Home Depot/runs/2026-08-17'")
    ap.add_argument("-o", "--out", default=None, help="output .docx path")
    args = ap.parse_args()
    out, n, missing = build(args.run_dir, args.out)
    print("wrote %s" % out)
    print("sections: %d" % n)
    if missing:
        print("absent: %s" % ", ".join(missing))


if __name__ == "__main__":
    main()
