"""Method 2 report PDF — the deliverable someone actually reads.

    python build_report.py "<run folder>" [--brand "#F96302"] [--brand-source "..."]

Renders report.md in the company's brand colours, with the exhibits built from
model.py and statements.csv rather than retyped: the football field, the ten-year
revenue and margin history, the sensitivity grid and the scenario range.

Two rules this enforces rather than trusts:
  - The rating, target and expected return come from decision.md front-matter.
    Where report.md disagrees, the front-matter wins and the difference is
    reported on stderr.
  - No sentence naming local plumbing reaches the page. Sentences are dropped
    individually, because a plumbing clause often sits at the end of a paragraph
    worth keeping. Every dropped sentence is printed so it can be read back.
"""

import argparse
import importlib.util
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import m2brand
import m2config
import m2md

try:
    from reportlab.graphics.shapes import Drawing, Line, Rect, String
    from reportlab.lib.colors import HexColor
    from reportlab.lib.enums import TA_CENTER, TA_LEFT
    from reportlab.lib.pagesizes import LETTER
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.units import mm
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.platypus import (BaseDocTemplate, Frame, KeepTogether,
                                    PageBreak, PageTemplate, Paragraph, Spacer,
                                    Table, TableStyle)
except ImportError:  # pragma: no cover
    sys.exit("reportlab is not available in this interpreter.")

PAGE_W, PAGE_H = LETTER
MARGIN = 16 * mm
CW = PAGE_W - 2 * MARGIN
HEAD_H = 15 * mm

FONT_DIR = m2config.CONFIG["fonts"]["dir"]
DISPLAY_FILES = [("M2Display", m2config.CONFIG["fonts"]["display_regular"]),
                 ("M2Display-Bold", m2config.CONFIG["fonts"]["display_bold"])]
ANALYST = m2config.ANALYST

DROPPED = []


# ------------------------------------------------------------------- fonts --

FONT_NOTE = ""


def register_fonts():
    """The configured display face where it loads, Helvetica otherwise.

    Reportlab's TTFont reads TrueType glyf outlines only. An OpenType file with
    CFF outlines, which most licensed display faces ship as, cannot be parsed and
    the build falls back to Helvetica. The fallback is fine; silence about it is
    not, so this says which font actually got used. Leave the font settings empty
    to run on Helvetica deliberately.
    """
    global FONT_NOTE
    if not FONT_DIR or not all(f for _, f in DISPLAY_FILES):
        FONT_NOTE = "no display font configured; set in Helvetica"
        return "Helvetica", "Helvetica-Bold"
    try:
        for name, fname in DISPLAY_FILES:
            path = os.path.join(FONT_DIR, fname)
            if not os.path.exists(path):
                FONT_NOTE = "%s not found in %s" % (fname, FONT_DIR)
                return "Helvetica", "Helvetica-Bold"
            pdfmetrics.registerFont(TTFont(name, path))
        return "M2Display", "M2Display-Bold"
    except Exception as exc:                            # noqa: BLE001
        FONT_NOTE = ("the display font did not register (%s); an OTF with CFF "
                     "outlines cannot be read by reportlab. Set in Helvetica."
                     % type(exc).__name__)
        return "Helvetica", "Helvetica-Bold"


DISPLAY, DISPLAY_B = register_fonts()
BODY_F, BODY_B, BODY_I = "Helvetica", "Helvetica-Bold", "Helvetica-Oblique"


# ------------------------------------------------------------------ styles --

def make_styles(pal):
    ink = HexColor(pal.ink)
    grey = HexColor(pal.grey)
    brandtext = HexColor(pal.text)
    S = {}
    S["body"] = ParagraphStyle("body", fontName=BODY_F, fontSize=8.6, leading=12.4,
                               textColor=ink, spaceAfter=5, alignment=TA_LEFT)
    S["lead"] = ParagraphStyle("lead", parent=S["body"], fontSize=9.6, leading=14)
    S["h1"] = ParagraphStyle("h1", fontName=DISPLAY_B, fontSize=15, leading=18,
                             textColor=brandtext, spaceBefore=12, spaceAfter=5)
    S["h2"] = ParagraphStyle("h2", fontName=DISPLAY_B, fontSize=11, leading=14,
                             textColor=ink, spaceBefore=9, spaceAfter=3)
    S["h3"] = ParagraphStyle("h3", fontName=BODY_B, fontSize=9, leading=12,
                             textColor=ink, spaceBefore=7, spaceAfter=2)
    S["bullet"] = ParagraphStyle("bullet", parent=S["body"], leftIndent=9,
                                 bulletIndent=2, spaceAfter=2)
    S["quote"] = ParagraphStyle("quote", parent=S["body"], leftIndent=10,
                                fontName=BODY_I, textColor=grey)
    S["caption"] = ParagraphStyle("caption", fontName=BODY_B, fontSize=7.6,
                                  leading=9.6, textColor=ink, spaceBefore=4,
                                  spaceAfter=1)
    S["source"] = ParagraphStyle("source", fontName=BODY_F, fontSize=6.6,
                                 leading=8.4, textColor=grey, spaceAfter=7)
    S["cover_t"] = ParagraphStyle("cover_t", fontName=DISPLAY_B, fontSize=27,
                                  leading=31, textColor=ink, alignment=TA_LEFT)
    S["cover_s"] = ParagraphStyle("cover_s", fontName=BODY_F, fontSize=10.5,
                                  leading=14, textColor=grey)
    S["disc"] = ParagraphStyle("disc", fontName=BODY_F, fontSize=7.2, leading=9.6,
                               textColor=grey, spaceAfter=5)
    S["cell"] = ParagraphStyle("cell", fontName=BODY_F, fontSize=7.4, leading=9.4,
                               textColor=ink)
    S["cellb"] = ParagraphStyle("cellb", parent=S["cell"], fontName=BODY_B)
    S["badge"] = ParagraphStyle("badge", fontName=BODY_B, fontSize=13, leading=15,
                                textColor=HexColor(pal.on_chrome),
                                alignment=TA_CENTER)
    return S


ESC = {"&": "&amp;", "<": "&lt;", ">": "&gt;"}


def markup(text):
    """Inline markdown to reportlab's mini-markup, escaped."""
    out = []
    for chunk, bold, italic, mono in m2md.inline_runs(text):
        s = "".join(ESC.get(c, c) for c in chunk)
        if mono:
            s = '<font face="Courier" size="7.6">%s</font>' % s
        if bold:
            s = "<b>%s</b>" % s
        if italic:
            s = "<i>%s</i>" % s
        out.append(s)
    return "".join(out)


# ---------------------------------------------------------------- exhibits --

_EX = [0]


def caption(S, title, source):
    _EX[0] += 1
    return [Paragraph("Exhibit %d — %s" % (_EX[0], markup(title)), S["caption"]),
            Paragraph(markup(source), S["source"])]


def grid(rows, pal, S, widths=None, header=True, highlight=None, align_right=True):
    """A data table with the house look: banded header, hairline rules, zebra."""
    if not rows:
        return None
    ncol = len(rows[0])
    widths = widths or [CW * 0.30] + [(CW * 0.70) / max(1, ncol - 1)] * (ncol - 1)
    data = []
    for i, row in enumerate(rows):
        line = []
        for j, cell in enumerate(row):
            st = S["cellb"] if (i == 0 and header) or j == 0 else S["cell"]
            line.append(Paragraph(markup(str(cell)), st))
        data.append(line)

    style = [("GRID", (0, 0), (-1, -1), 0.4, HexColor(pal.rule)),
             ("VALIGN", (0, 0), (-1, -1), "TOP"),
             ("LEFTPADDING", (0, 0), (-1, -1), 4),
             ("RIGHTPADDING", (0, 0), (-1, -1), 4),
             ("TOPPADDING", (0, 0), (-1, -1), 3),
             ("BOTTOMPADDING", (0, 0), (-1, -1), 3)]
    if header:
        style.append(("BACKGROUND", (0, 0), (-1, 0), HexColor(pal.pale)))
    if align_right and ncol > 1:
        style.append(("ALIGN", (1, 0), (-1, -1), "RIGHT"))
    for r in range(1 if header else 0, len(data)):
        if (r - (1 if header else 0)) % 2 == 1:
            style.append(("BACKGROUND", (0, r), (-1, r), HexColor("#FAFAFA")))
    if highlight is not None:
        style.append(("BACKGROUND", (0, highlight), (-1, highlight),
                      HexColor(pal.pale)))
        style.append(("FONTNAME", (0, highlight), (-1, highlight), BODY_B))

    t = Table(data, colWidths=widths, hAlign="LEFT")
    t.setStyle(TableStyle(style))
    return t


def football_field(model, price, target, pal, w=CW, h=None):
    """Every method's valuation range against the reference price."""
    rows = list(getattr(model, "FOOTBALL", []) or [])
    if not rows:
        return None
    h = h or (26 + 17 * len(rows))
    vals = [v for _, lo, hi in rows for v in (lo, hi) if isinstance(v, (int, float))]
    vals += [price] + ([target] if target else [])
    lo_v, hi_v = min(vals), max(vals)
    pad = (hi_v - lo_v) * 0.08 or 1.0
    lo_v, hi_v = lo_v - pad, hi_v + pad

    d = Drawing(w, h)
    x0, x1 = 84.0, w - 16.0

    def px(v):
        return x0 + (v - lo_v) / (hi_v - lo_v) * (x1 - x0)

    y = h - 16
    for label, lo, hi in rows:
        d.add(String(2, y + 2, str(label)[:22], fontName=BODY_B, fontSize=6.8,
                     fillColor=HexColor(pal.ink)))
        if isinstance(lo, (int, float)) and isinstance(hi, (int, float)):
            left, right = px(min(lo, hi)), px(max(lo, hi))
            d.add(Rect(left, y - 1, max(right - left, 1.6), 9,
                       fillColor=HexColor(pal.mark), strokeColor=None))
            d.add(String(left - 3, y + 1, "%.0f" % min(lo, hi), fontName=BODY_F,
                         fontSize=5.8, fillColor=HexColor(pal.grey),
                         textAnchor="end"))
            d.add(String(right + 3, y + 1, "%.0f" % max(lo, hi), fontName=BODY_F,
                         fontSize=5.8, fillColor=HexColor(pal.grey)))
        y -= 17

    base = 14
    d.add(Line(x0, base, x1, base, strokeColor=HexColor(pal.rule), strokeWidth=0.6))
    d.add(Line(px(price), base - 2, px(price), h - 6,
               strokeColor=HexColor(pal.ink), strokeWidth=0.9, strokeDashArray=[2, 2]))
    d.add(String(px(price), h - 4, "Price %.2f" % price, fontName=BODY_B,
                 fontSize=6.2, fillColor=HexColor(pal.ink), textAnchor="middle"))
    if target:
        d.add(Line(px(target), base - 2, px(target), h - 6,
                   strokeColor=HexColor(pal.text), strokeWidth=1.4))
        d.add(String(px(target), base - 10, "Target %.2f" % target,
                     fontName=BODY_B, fontSize=6.2, fillColor=HexColor(pal.text),
                     textAnchor="middle"))
    return d


def history_chart(years, income, ratios, pal, w=CW, h=150):
    """Ten years of revenue as bars with operating margin as a line over it."""
    rev = _find(income, ("revenue", "net sales", "total revenue", "sales"))
    margin = _find(ratios, ("operating margin",))
    if not rev or not years:
        return None
    pts = [(y, v) for y, v in zip(years, rev) if isinstance(v, (int, float))]
    if len(pts) < 2:
        return None

    d = Drawing(w, h)
    x0, x1, y0, y1 = 40.0, w - 40.0, 26.0, h - 14.0
    hi = max(v for _, v in pts) * 1.12
    span = (x1 - x0) / len(pts)
    bw = span * 0.62

    for i in range(5):
        gy = y0 + (y1 - y0) * i / 4.0
        d.add(Line(x0, gy, x1, gy, strokeColor=HexColor(pal.rule), strokeWidth=0.35))
        d.add(String(x0 - 4, gy - 2, "%.0f" % (hi * i / 4.0 / 1000.0),
                     fontName=BODY_F, fontSize=5.6, fillColor=HexColor(pal.grey),
                     textAnchor="end"))

    for i, (year, val) in enumerate(pts):
        cx = x0 + span * i + (span - bw) / 2.0
        bh = (val / hi) * (y1 - y0)
        d.add(Rect(cx, y0, bw, bh, fillColor=HexColor(pal.mark), strokeColor=None))
        d.add(String(cx + bw / 2.0, y0 - 9, str(year)[-4:], fontName=BODY_F,
                     fontSize=5.6, fillColor=HexColor(pal.grey), textAnchor="middle"))

    mpts = [(i, m) for i, m in enumerate(margin or []) if isinstance(m, (int, float))]
    if len(mpts) >= 2:
        mvals = [m for _, m in mpts]
        mlo, mhi = min(mvals) * 0.9, max(mvals) * 1.1
        prev = None
        for i, m in mpts:
            cx = x0 + span * i + span / 2.0
            cy = y0 + (m - mlo) / (mhi - mlo or 1) * (y1 - y0) * 0.85
            if prev:
                d.add(Line(prev[0], prev[1], cx, cy, strokeColor=HexColor(pal.ink),
                           strokeWidth=1.1))
            prev = (cx, cy)
        d.add(String(x1 + 3, prev[1] - 2, "op margin", fontName=BODY_B, fontSize=5.8,
                     fillColor=HexColor(pal.ink)))
    d.add(String(x0 - 4, y1 + 3, "revenue, $bn", fontName=BODY_B, fontSize=5.8,
                 fillColor=HexColor(pal.grey), textAnchor="end"))
    return d


def _find(items, names):
    for item, _unit, vals in (items or []):
        if item.strip().lower() in names:
            return vals
    return None


def sensitivity_table(model, pal, S):
    sens = getattr(model, "SENSITIVITY", None)
    if not sens:
        return None
    cols = sens.get("col_values", [])
    rows = [[sens.get("row_label", "")] + ["%s" % c for c in cols]]
    for label, line in zip(sens.get("row_values", []), sens.get("grid", [])):
        rows.append([str(label)] + ["%.0f" % v if isinstance(v, (int, float))
                                    else str(v) for v in line])
    return grid(rows, pal, S)


def scenario_table(model, pal, S, price):
    sc = getattr(model, "SCENARIOS", None)
    if not sc:
        return None
    rows = [["Scenario", "Probability", "Target", "Return", "Key assumption"]]
    for key in ("bull", "base", "bear"):
        s = sc.get(key)
        if not s:
            continue
        t = s.get("target", 0) or 0
        rows.append([key.title(), "%.0f%%" % (100 * (s.get("probability") or 0)),
                     "%.2f" % t, "%+.1f%%" % (100 * (t / price - 1)) if price else "",
                     (s.get("note") or "")])
    w = getattr(model, "WEIGHTED", {}) or {}
    rows.append(["Probability-weighted", "100%", "%.2f" % (w.get("target") or 0),
                 "%+.1f%%" % (100 * (w.get("expected_total_return") or 0)),
                 "Total return includes dividends"])
    widths = [CW * 0.16, CW * 0.11, CW * 0.11, CW * 0.10, CW * 0.52]
    return grid(rows, pal, S, widths=widths, highlight=len(rows) - 1)


# --------------------------------------------------------------- page frame --

class Doc(BaseDocTemplate):
    def __init__(self, path, pal, meta, **kw):
        BaseDocTemplate.__init__(self, path, pagesize=LETTER,
                                 leftMargin=MARGIN, rightMargin=MARGIN,
                                 topMargin=MARGIN + HEAD_H, bottomMargin=MARGIN,
                                 title="%s — Method 2 equity research"
                                       % meta.get("company", ""),
                                 author=ANALYST, **kw)
        self.pal, self.meta = pal, meta
        frame = Frame(MARGIN, MARGIN, CW, PAGE_H - 2 * MARGIN - HEAD_H, id="body")
        cover = Frame(MARGIN, MARGIN, CW, PAGE_H - 2 * MARGIN, id="cover")
        self.addPageTemplates([
            PageTemplate(id="cover", frames=[cover], onPage=self._cover_chrome),
            PageTemplate(id="body", frames=[frame], onPage=self._chrome)])

    def _cover_chrome(self, canv, doc):
        pal = self.pal
        canv.saveState()
        canv.setFillColor(HexColor(pal.chrome))
        canv.rect(0, PAGE_H - 8 * mm, PAGE_W, 8 * mm, stroke=0, fill=1)
        canv.setFillColor(HexColor(pal.grey))
        canv.setFont(BODY_F, 7)
        canv.drawCentredString(PAGE_W / 2, 10 * mm,
                               "Educational and research use only. Not investment advice.")
        canv.restoreState()

    def _chrome(self, canv, doc):
        pal, meta = self.pal, self.meta
        canv.saveState()
        canv.setFillColor(HexColor(pal.chrome))
        canv.rect(0, PAGE_H - HEAD_H, PAGE_W, HEAD_H, stroke=0, fill=1)
        canv.setFillColor(HexColor(pal.on_chrome))
        canv.setFont(DISPLAY_B, 9.5)
        canv.drawString(MARGIN, PAGE_H - HEAD_H + 5.2 * mm,
                        "%s (%s)" % (meta.get("company", ""), meta.get("ticker", "")))
        canv.setFont(BODY_F, 8)
        canv.drawRightString(PAGE_W - MARGIN, PAGE_H - HEAD_H + 5.2 * mm,
                             "%s  ·  target %s%s  ·  %s"
                             % (meta.get("rating", ""), meta.get("symbol", "$"),
                                meta.get("target", ""), meta.get("run_date", "")))
        canv.setStrokeColor(HexColor(pal.rule))
        canv.setLineWidth(0.5)
        canv.line(MARGIN, MARGIN - 4, PAGE_W - MARGIN, MARGIN - 4)
        canv.setFillColor(HexColor(pal.grey))
        canv.setFont(BODY_F, 6.8)
        canv.drawString(MARGIN, MARGIN - 11,
                        "Method 2 multi-agent research · educational and research use "
                        "only, not investment advice")
        canv.drawRightString(PAGE_W - MARGIN, MARGIN - 11, "%d" % canv.getPageNumber())
        canv.restoreState()


# ------------------------------------------------------------------ content --

_SECNUM = re.compile(r"^\s*(\d{2})\b[\s.:—-]*(.*)$")


def render_blocks(blocks, S, pal, story):
    for b in blocks:
        kind = b["type"]
        if kind == "heading":
            lvl = b["level"]
            style = S["h1"] if lvl <= 2 else (S["h2"] if lvl == 3 else S["h3"])
            story.append(Paragraph(markup(b["text"]), style))
        elif kind == "para":
            story.append(Paragraph(markup(b["text"]), S["body"]))
        elif kind == "list":
            for indent, text in b["items"]:
                st = ParagraphStyle("li", parent=S["bullet"],
                                    leftIndent=9 + 9 * min(indent, 3))
                story.append(Paragraph(markup(text), st, bulletText="•"))
        elif kind == "table":
            t = grid([b["header"]] + b["rows"], pal, S)
            if t is not None:
                story.append(Spacer(1, 3))
                story.append(t)
                story.append(Spacer(1, 6))
        elif kind == "quote":
            story.append(Paragraph(markup(b["text"]), S["quote"]))
        elif kind == "callout":
            head = b["title"] or b["kind"].title()
            story.append(Paragraph("<b>%s</b> — %s" % (markup(head),
                                                       markup(b["text"])), S["quote"]))
        elif kind == "code":
            story.append(Paragraph('<font face="Courier" size="7">%s</font>'
                                   % "".join(ESC.get(c, c) for c in b["text"]),
                                   S["body"]))


def split_sections(blocks):
    """Group blocks under their top-level heading, keyed by leading section number."""
    out, cur, key = [], [], None
    for b in blocks:
        if b["type"] == "heading" and b["level"] <= 2:
            if cur:
                out.append((key, cur))
            m = _SECNUM.match(b["text"])
            key = m.group(1) if m else None
            cur = [b]
        else:
            cur.append(b)
    if cur:
        out.append((key, cur))
    return out


def cover_page(S, pal, meta, fm, story):
    story.append(Spacer(1, 42 * mm))
    story.append(Paragraph("METHOD 2 · MULTI-AGENT EQUITY RESEARCH",
                           ParagraphStyle("k", parent=S["cover_s"], fontName=BODY_B,
                                          fontSize=8, textColor=HexColor(pal.text))))
    story.append(Spacer(1, 5 * mm))
    story.append(Paragraph(markup(meta.get("company", "")), S["cover_t"]))
    story.append(Spacer(1, 2 * mm))
    story.append(Paragraph("%s · %s · %s" % (meta.get("ticker", ""),
                                             meta.get("exchange", ""),
                                             meta.get("run_date", "")), S["cover_s"]))
    story.append(Spacer(1, 9 * mm))

    price = m2md.num(fm, "reference_price") or 0
    tgt = m2md.num(fm, "target") or 0
    ret = m2md.num(fm, "expected_total_return")
    rows = [["Rating", "Twelve-month target", "Reference price", "Expected total return"],
            [fm.get("rating", ""), "%s%.2f" % (meta.get("symbol", "$"), tgt),
             "%s%.2f" % (meta.get("symbol", "$"), price),
             "%+.1f%%" % (100 * ret) if ret is not None else ""]]
    t = grid(rows, pal, S, widths=[CW / 4.0] * 4, align_right=False)
    story.append(t)
    story.append(Spacer(1, 6 * mm))

    bits = []
    if fm.get("conviction"):
        bits.append("Conviction %s." % fm["conviction"])
    if str(fm.get("marginal", "")).lower() == "true":
        bits.append("The call sits within five points of a band edge.")
    if fm.get("decided_by"):
        bits.append("Carried by the %s work." % fm["decided_by"])
    if bits:
        story.append(Paragraph(" ".join(bits), S["lead"]))

    story.append(Spacer(1, 8 * mm))
    story.append(Paragraph(
        "Produced by a fan-out of specialist agents: four analysts gathering "
        "evidence independently, a valuation agent building a base case, a bull "
        "and a bear attacking it on the same model, a judge ruling on the evidence "
        "rather than on the argument, and a portfolio risk gate. The rating scale "
        "is three-tier and the bands are on the probability-weighted twelve-month "
        "total return.", S["body"]))
    story.append(Spacer(1, 4 * mm))
    story.append(Paragraph("Analyst: %s · Prepared %s"
                           % (ANALYST, meta.get("run_date", "")), S["cover_s"]))
    story.append(PageBreak())


def disclosures(S, pal, fm, story):
    story.append(PageBreak())
    story.append(Paragraph("Disclosures", S["h1"]))

    story.append(Paragraph("Rating scale", S["h3"]))
    rows = [["Rating", "Band on the probability-weighted twelve-month total return"],
            ["BUY", "Above +15%"], ["HOLD", "−15% to +15%"], ["SELL", "Below −15%"]]
    story.append(grid(rows, pal, S, widths=[CW * 0.18, CW * 0.82], align_right=False))
    story.append(Spacer(1, 5))
    story.append(Paragraph(
        "Three ratings only. There is no fourth tier and no paired label. Where a "
        "call is marginal, the report states how marginal it is and names the single "
        "assumption that would move it to the neighbouring band.", S["disc"]))

    story.append(Paragraph("Analyst certification", S["h3"]))
    story.append(Paragraph(
        "I, %s, certify that the views expressed in this report " % ANALYST +
        "accurately reflect my personal views about the subject security and issuer, "
        "and that no part of my compensation was, is, or will be directly or "
        "indirectly related to the specific recommendation or views expressed here.",
        S["disc"]))

    story.append(Paragraph("Ownership and conflicts", S["h3"]))
    pos = fm.get("position")
    if pos and str(pos).strip().lower() not in ("null", "none", ""):
        story.append(Paragraph(
            "Position held at the time of this report: %s." % markup(str(pos).replace("\n", "; ")),
            S["disc"]))
    else:
        story.append(Paragraph(
            "No position is held in this security. The holdings snapshot this "
            "statement is drawn from is recorded in the run file for this report.",
            S["disc"]))
    story.append(Paragraph(
        "No investment banking relationship, no market-making position, and no "
        "compensation of any kind from the subject company.", S["disc"]))

    story.append(Paragraph("Disclaimer", S["h3"]))
    story.append(Paragraph(
        "This report is produced for educational and research purposes only and is "
        "not investment advice, an offer, or a solicitation to buy or sell any "
        "security. Past performance does not guarantee future results. Figures are "
        "drawn from public filings and market data believed reliable but not "
        "independently audited. Consult a licensed financial adviser before making "
        "an investment decision.", S["disc"]))


# --------------------------------------------------------------------- main --

def load_model(path):
    if not os.path.exists(path):
        return None
    spec = importlib.util.spec_from_file_location("m2model_pdf", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def load_statements(path):
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import build_workbook
    return build_workbook.load_statements(path)


def build(run_dir, brand=None, brand_source="", out_path=None):
    run_dir = os.path.abspath(run_dir)
    report_path = os.path.join(run_dir, "report.md")
    if not os.path.exists(report_path):
        sys.exit("No report.md in %s — stage 6 has not run." % run_dir)

    fm, _ = m2md.read_note(os.path.join(run_dir, "decision.md"))
    _, blocks = m2md.read_note(report_path, strip_plumbing=True)
    model = load_model(os.path.join(run_dir, "model.py"))
    years, stmts = load_statements(os.path.join(run_dir, "statements.csv"))

    pal = m2brand.Palette(brand, brand_source) if brand else m2brand.DEFAULT
    S = make_styles(pal)

    meta = dict(getattr(model, "META", {}) or {})
    for key in ("ticker", "company", "exchange", "run_date"):
        meta.setdefault(key, fm.get(key, ""))
    meta["rating"] = fm.get("rating", "")
    meta["target"] = fm.get("target", "")
    meta["symbol"] = "C$" if str(meta.get("exchange", "")).upper() in ("TSX", "TSXV") else "$"

    price = m2md.num(fm, "reference_price") or (meta.get("price") or 0)
    target = m2md.num(fm, "target") or 0

    story = []
    cover_page(S, pal, meta, fm, story)

    for key, sec in split_sections(blocks):
        render_blocks(sec, S, pal, story)

        if key == "04" and years:
            ch = history_chart(years, stmts.get("income"), stmts.get("ratio"), pal)
            if ch is not None:
                story.append(Spacer(1, 4))
                story.extend(caption(S, "Revenue and operating margin, ten fiscal years",
                                     "Company filings; author's analysis."))
                story.append(ch)
        elif key == "05" and model:
            ff = football_field(model, price, target, pal)
            if ff is not None:
                story.append(Spacer(1, 4))
                story.extend(caption(S, "Valuation ranges against the current price",
                                     "Author's valuation; street targets and "
                                     "fifty-two-week range from market data."))
                story.append(ff)
            st = sensitivity_table(model, pal, S)
            if st is not None:
                story.append(Spacer(1, 6))
                story.extend(caption(S, "Sensitivity of the twelve-month target",
                                     "Author's model."))
                story.append(st)
        elif key == "08" and model:
            sc = scenario_table(model, pal, S, price)
            if sc is not None:
                story.append(Spacer(1, 4))
                story.extend(caption(S, "Scenarios and the probability-weighted target",
                                     "Author's model; probabilities defended in the text."))
                story.append(sc)

    disclosures(S, pal, fm, story)

    if out_path is None:
        exports = os.path.join(run_dir, "exports")
        os.makedirs(exports, exist_ok=True)
        out_path = os.path.join(exports, "%s_Method2_Report_%s.pdf"
                                % (meta.get("ticker") or "RUN",
                                   meta.get("run_date") or "undated"))

    doc = Doc(out_path, pal, meta)
    doc.build(story)
    return out_path, pal, meta


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("run_dir")
    ap.add_argument("--brand", default=None, help="brand hex, e.g. '#F96302'")
    ap.add_argument("--brand-source", default="", help="where the hex came from")
    ap.add_argument("-o", "--out", default=None)
    args = ap.parse_args()
    out, pal, meta = build(args.run_dir, args.brand, args.brand_source, args.out)
    print("wrote %s" % out)
    print("fonts: %s display, %s body" % (DISPLAY, BODY_F))
    if FONT_NOTE:
        print("       %s" % FONT_NOTE)
    print("palette checks:")
    for r in pal.report():
        print("   %-18s %-18s %-34s %s" % r)
    if m2md.DROPPED:
        print("dropped %d sentence(s) naming local plumbing — read every one:"
              % len(m2md.DROPPED))
        for s in m2md.DROPPED:
            print("   -", s)
    else:
        print("dropped no sentences")
    for line in m2config.MISSING:
        print("config: %s" % line)


if __name__ == "__main__":
    main()
