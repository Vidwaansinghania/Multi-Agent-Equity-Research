"""Method 2 model workbook — the numbers, open and inspectable.

    python build_workbook.py "<run folder>" [-o OUT.xlsx]

Reads statements.csv (ten fiscal years, written by the fundamentals agent) and
model.py (the valuation, written by the valuation agent). Writes one sheet per
thing a reader might want to check, with the source of every assumption beside
it.

Nothing here is retyped from a memo. If a figure in the report is wrong, it is
wrong in one of these two inputs, and this workbook is how that gets found.
"""

import argparse
import csv
import importlib.util
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import m2md

try:
    from openpyxl import Workbook
    from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
    from openpyxl.utils import get_column_letter
except ImportError:  # pragma: no cover
    sys.exit("openpyxl is not available in this interpreter.")

INK = "1A1A1A"
GREY = "6B6B6B"
BAND = "F2F2F2"
HEAD = "E4E4E4"
RULE = "D8D8D8"

H1 = Font(name="Calibri", size=14, bold=True, color=INK)
H2 = Font(name="Calibri", size=11, bold=True, color=INK)
BODY = Font(name="Calibri", size=10, color=INK)
SMALL = Font(name="Calibri", size=8.5, color=GREY)
BOLD = Font(name="Calibri", size=10, bold=True, color=INK)

THIN = Side(style="thin", color=RULE)
BOX = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)
WRAP = Alignment(wrap_text=True, vertical="top")
RIGHT = Alignment(horizontal="right")

FMT = {
    "usd millions": "#,##0.0",
    "usd": "#,##0.00",
    "shares millions": "#,##0.0",
    "percent": "0.0%",
    "ratio": "0.00",
    "days": "0.0",
    "text": "@",
}


# ------------------------------------------------------------------ helpers --

def title(ws, text, sub=None):
    ws["A1"] = text
    ws["A1"].font = H1
    if sub:
        ws["A2"] = sub
        ws["A2"].font = SMALL
    ws.freeze_panes = "A4"
    return 4


def header_row(ws, row, values, widths=None):
    for j, val in enumerate(values, start=1):
        c = ws.cell(row=row, column=j, value=val)
        c.font = H2
        c.fill = PatternFill("solid", fgColor=HEAD)
        c.border = BOX
        c.alignment = Alignment(horizontal="right" if j > 1 else "left",
                                wrap_text=True, vertical="bottom")
    if widths:
        for j, w in enumerate(widths, start=1):
            ws.column_dimensions[get_column_letter(j)].width = w
    return row + 1


def put_row(ws, row, label, values, fmt=None, bold=False, band=False):
    c = ws.cell(row=row, column=1, value=label)
    c.font = BOLD if bold else BODY
    c.border = BOX
    if band:
        c.fill = PatternFill("solid", fgColor=BAND)
    for j, val in enumerate(values, start=2):
        c = ws.cell(row=row, column=j, value=val)
        c.font = BOLD if bold else BODY
        c.border = BOX
        c.alignment = RIGHT
        if fmt:
            c.number_format = fmt
        if band:
            c.fill = PatternFill("solid", fgColor=BAND)
    return row + 1


def note(ws, row, text, span=8):
    ws.cell(row=row, column=1, value=text).font = SMALL
    ws.merge_cells(start_row=row, start_column=1, end_row=row, end_column=span)
    ws.cell(row=row, column=1).alignment = WRAP
    ws.row_dimensions[row].height = 26
    return row + 2


def numeric(text):
    """CSV cell to a number, or None for a genuinely absent figure."""
    if text is None:
        return None
    s = str(text).strip().replace(",", "").replace("$", "")
    if s in ("", "-", "n/a", "N/A", "na"):
        return None
    neg = s.startswith("(") and s.endswith(")")
    if neg:
        s = s[1:-1]
    pct = s.endswith("%")
    if pct:
        s = s[:-1]
    try:
        v = float(s)
    except ValueError:
        return text
    if pct:
        v /= 100.0
    return -v if neg else v


# -------------------------------------------------------------- input files --

def load_statements(path):
    """statements.csv -> (years, {statement: [(line_item, unit, [values])]})."""
    if not os.path.exists(path):
        return [], {}
    with open(path, "r", encoding="utf-8-sig", newline="") as fh:
        rows = list(csv.reader(fh))
    if not rows:
        return [], {}
    head = [h.strip() for h in rows[0]]
    try:
        first_year = head.index("unit") + 1
    except ValueError:
        first_year = 3
    years = head[first_year:]
    out = {}
    for r in rows[1:]:
        if not r or not r[0].strip():
            continue
        r = r + [""] * (len(head) - len(r))
        stmt = r[0].strip().lower()
        item = r[1].strip()
        unit = r[2].strip().lower()
        vals = [numeric(x) for x in r[first_year:first_year + len(years)]]
        out.setdefault(stmt, []).append((item, unit, vals))
    return years, out


def load_model(path):
    if not os.path.exists(path):
        return None
    spec = importlib.util.spec_from_file_location("m2model", path)
    mod = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(mod)
    except Exception as exc:                       # noqa: BLE001
        sys.exit("model.py failed to import: %s" % exc)
    return mod


# ------------------------------------------------------------------- sheets --

def sheet_readme(wb, meta, fm, has_stmt, has_model, years):
    ws = wb.active
    ws.title = "README"
    row = title(ws, "%s — Method 2 model" % meta.get("company", meta.get("ticker", "")),
                "Run %s · reference price %s as of %s"
                % (meta.get("run_date", ""), meta.get("price", ""),
                   meta.get("price_date", "")))
    ws.column_dimensions["A"].width = 34
    ws.column_dimensions["B"].width = 52

    pairs = [("Ticker", meta.get("ticker")), ("Exchange", meta.get("exchange")),
             ("Rating", fm.get("rating")), ("Twelve-month target", fm.get("target")),
             ("Expected total return", fm.get("expected_total_return")),
             ("Conviction", fm.get("conviction")),
             ("Decided by", fm.get("decided_by")),
             ("Market-data calls", fm.get("alpha_vantage_calls")),
             ("Statement years", "%d (%s)" % (len(years), ", ".join(years[:1] + years[-1:]))
              if years else "none supplied")]
    for label, val in pairs:
        if val in (None, ""):
            continue
        ws.cell(row=row, column=1, value=label).font = BOLD
        ws.cell(row=row, column=2, value=val).font = BODY
        row += 1

    row += 1
    row = note(ws, row,
               "The rating and the target come from the decision record for this run "
               "and are not recomputed here. Everything else on the other sheets is "
               "imported from the run's valuation model, so a corrected assumption "
               "moves this workbook and the report together.", span=2)
    if not has_stmt:
        row = note(ws, row, "No ten-year statement file was supplied with this run, so "
                            "the statement, common-size and ratio sheets are absent.", span=2)
    if not has_model:
        row = note(ws, row, "No valuation model was supplied with this run, so the DCF, "
                            "scenario, sensitivity and comparables sheets are absent.", span=2)
    note(ws, row, "Educational and research use only. Not investment advice.", span=2)


def sheet_statement(wb, name, years, items, subtitle):
    if not items:
        return
    ws = wb.create_sheet(name)
    row = title(ws, name, subtitle)
    widths = [40] + [12] * len(years)
    row = header_row(ws, row, ["Line item"] + years, widths)
    for item, unit, vals in items:
        row = put_row(ws, row, item, vals, fmt=FMT.get(unit, "#,##0.0"))
    note(ws, row + 1, "Source: company filings as gathered in stage 1. Blank cells are "
                      "years with no disclosed figure, never zeros.", span=len(years) + 1)


def sheet_common_size(wb, years, income):
    """Income statement as a share of revenue, computed rather than transcribed."""
    if not income:
        return
    rev = None
    for item, _unit, vals in income:
        if item.strip().lower() in ("revenue", "net sales", "total revenue",
                                    "net revenue", "sales"):
            rev = vals
            break
    if rev is None:
        return
    ws = wb.create_sheet("Common size")
    row = title(ws, "Common size — income statement",
                "Every line as a share of revenue. Computed from the statement sheet.")
    row = header_row(ws, row, ["Line item"] + years, [40] + [12] * len(years))
    for item, unit, vals in income:
        # Aggregate currency lines only. A per-share figure as a share of
        # revenue is a meaningless number that reads as a real one.
        if unit != "usd millions":
            continue
        shares = []
        for v, r in zip(vals, rev):
            shares.append(v / r if isinstance(v, (int, float))
                          and isinstance(r, (int, float)) and r else None)
        row = put_row(ws, row, item, shares, fmt="0.0%")
    note(ws, row + 1, "A line that moves steadily across a decade here is usually the "
                      "most useful thing in the file.", span=len(years) + 1)


def sheet_estimates(wb, model):
    est = getattr(model, "ESTIMATES", None)
    if not est:
        return
    ws = wb.create_sheet("Estimates")
    row = title(ws, "Financial estimates",
                "Three fiscal years actual, two estimated. Actuals from the filings; "
                "estimates from this run's valuation.")
    years = est.get("years", [])
    row = header_row(ws, row, ["Metric"] + years, [30] + [13] * len(years))
    for label, vals in est.get("rows", []):
        low = label.lower()
        fmt = "0.0%" if ("growth" in low or "margin" in low or "yield" in low) else "#,##0.00"
        row = put_row(ws, row, label, vals, fmt=fmt)
    note(ws, row + 1, "A suffix of A is an actual and E is an estimate.", span=len(years) + 1)


def sheet_dcf(wb, model, meta):
    dcf = getattr(model, "DCF", None)
    if not dcf:
        return
    ws = wb.create_sheet("DCF")
    row = title(ws, "Discounted cash flow",
                "Primary valuation method. Every assumption carries its basis.")
    ws.column_dimensions["A"].width = 32

    years = dcf.get("years", [])
    fcf = dcf.get("fcf", [])
    wacc = dcf.get("wacc")
    mid = str(dcf.get("discounting", "year-end")).lower().startswith("mid")
    if years and fcf:
        row = header_row(ws, row, ["Free cash flow"] + years, [32] + [13] * len(years))
        row = put_row(ws, row, "FCF (%s m)" % meta.get("currency", "USD"), fcf,
                      fmt="#,##0.0")
        times = dcf.get("t")
        if not times or len(times) != len(fcf):
            times = [k + (0.5 if mid else 1.0) for k in range(len(fcf))]
        row = put_row(ws, row, "Discount period (years)", times, fmt="0.00")
        if isinstance(wacc, (int, float)) and wacc:
            disc = [(1.0 + wacc) ** -t for t in times]
            row = put_row(ws, row, "Discount factor", disc, fmt="0.000")
            row = put_row(ws, row, "Present value",
                          [f * d for f, d in zip(fcf, disc)], fmt="#,##0.0")
        row = note(ws, row, "Discounting convention: %s. The periods above are the "
                            "ones the valuation agent used; this sheet discounts on "
                            "them rather than assuming a convention."
                            % ("mid-year" if mid else "year-end"),
                   span=max(2, len(years) + 1))

    stub = dcf.get("stub")
    if isinstance(stub, dict) and stub:
        row = header_row(ws, row, ["Stub period", "Value"], [32, 16])
        if stub.get("label"):
            row = put_row(ws, row, "Period", [stub["label"]], fmt="@")
        for label, key, fmt in (("Share of the full year", "fraction", "0.0%"),
                                ("Discount period (years)", "t", "0.00"),
                                ("Free cash flow", "fcf", "#,##0.0"),
                                ("Present value", "pv", "#,##0.0")):
            if stub.get(key) is None:
                continue
            row = put_row(ws, row, label, [stub[key]], fmt=fmt)
        row += 1

    terminal = [("Method", dcf.get("terminal_method"), "@"),
                ("Terminal growth", dcf.get("terminal_growth"), "0.00%"),
                ("ROIC on new capital", dcf.get("terminal_roic"), "0.0%"),
                ("Reinvestment rate", dcf.get("terminal_reinvestment_rate"), "0.0%"),
                ("Terminal value", dcf.get("terminal_value"), "#,##0.0"),
                ("PV of terminal value", dcf.get("pv_terminal"), "#,##0.0"),
                ("Share of enterprise value", dcf.get("tv_share_of_ev"), "0.0%")]
    terminal = [t for t in terminal if t[1] is not None]
    if terminal:
        row = header_row(ws, row, ["Terminal value", "Value"], [32, 16])
        for label, val, fmt in terminal:
            row = put_row(ws, row, label, [val], fmt=fmt)
        share = dcf.get("tv_share_of_ev")
        g, roic = dcf.get("terminal_growth"), dcf.get("terminal_roic")
        rr = dcf.get("terminal_reinvestment_rate")
        if all(isinstance(v, (int, float)) for v in (g, roic, rr)) and roic:
            if abs(rr - g / roic) > 0.005:
                row = note(ws, row, "Reinvestment rate %.1f%% does not reconcile to "
                                    "terminal growth over ROIC (%.1f%%). One of the "
                                    "three figures is wrong."
                                    % (rr * 100, (g / roic) * 100))
        if isinstance(share, (int, float)) and share > 0.70:
            row = note(ws, row, "Terminal value is %.0f%% of enterprise value. Above "
                                "roughly 70%% the valuation is mostly a claim about "
                                "the year after the forecast ends." % (share * 100))
        else:
            row += 1

    bridge = [("WACC", dcf.get("wacc"), "0.00%"),
              ("PV of forecast FCF", dcf.get("pv_forecast"), "#,##0.0"),
              ("PV of terminal value", dcf.get("pv_terminal"), "#,##0.0"),
              ("Enterprise value", dcf.get("enterprise_value"), "#,##0.0"),
              ("Less net debt", dcf.get("net_debt"), "#,##0.0"),
              ("Equity value", dcf.get("equity_value"), "#,##0.0"),
              ("Diluted shares (m)", meta.get("shares_diluted"), "#,##0.0"),
              ("Value per share", dcf.get("value_per_share"), "#,##0.00")]
    row = header_row(ws, row, ["Bridge to equity value", "Value"], [32, 16])
    for label, val, fmt in bridge:
        if val is None:
            continue
        last = label == "Value per share"
        row = put_row(ws, row, label, [val], fmt=fmt, bold=last, band=last)
    if dcf.get("net_debt_basis"):
        row = note(ws, row, "Net debt basis: %s" % dcf["net_debt_basis"])

    rev = dcf.get("reverse_dcf")
    if isinstance(rev, dict) and rev:
        row = header_row(ws, row, ["Reverse DCF at the market price", "Implied"],
                         [32, 16])
        for label, key, fmt in (("FCF growth", "implied_growth", "0.00%"),
                                ("Operating margin", "implied_margin", "0.0%"),
                                ("WACC", "implied_wacc", "0.00%"),
                                ("Terminal growth", "implied_terminal_growth", "0.00%")):
            if rev.get(key) is None:
                continue
            row = put_row(ws, row, label, [rev[key]], fmt=fmt)
        if rev.get("verdict"):
            row = note(ws, row, "Verdict: %s" % rev["verdict"])

    assumptions = dcf.get("assumptions") or []
    if assumptions:
        row += 1
        row = header_row(ws, row, ["Assumption", "Value", "Basis and source"],
                         [32, 16, 74])
        for a in assumptions:
            label, val, basis = (list(a) + ["", ""])[:3]
            ws.cell(row=row, column=1, value=label).font = BODY
            ws.cell(row=row, column=2, value=val).font = BODY
            c = ws.cell(row=row, column=3, value=basis)
            c.font = BODY
            c.alignment = WRAP
            for j in (1, 2, 3):
                ws.cell(row=row, column=j).border = BOX
            row += 1


def sheet_scenarios(wb, model, meta):
    sc = getattr(model, "SCENARIOS", None)
    if not sc:
        return
    ws = wb.create_sheet("Scenarios")
    row = title(ws, "Bull, base and bear",
                "Probabilities must sum to 1. The weighted target is what the rating "
                "band is applied to.")
    row = header_row(ws, row,
                     ["Scenario", "Probability", "Target", "Exit multiple", "EPS",
                      "Return vs price", "Weighted"], [16, 12, 12, 14, 10, 14, 12])
    price = meta.get("price") or 0
    total_w = 0.0
    for key in ("bull", "base", "bear"):
        s = sc.get(key)
        if not s:
            continue
        p = s.get("probability", 0) or 0
        t = s.get("target", 0) or 0
        ret = (t / price - 1) if price else None
        total_w += p * t
        vals = [p, t, s.get("exit_multiple"), s.get("eps"), ret, p * t]
        r = row
        row = put_row(ws, row, key.title(), vals)
        for col, fmt in ((2, "0%"), (3, "#,##0.00"), (4, "0.0x"), (5, "#,##0.00"),
                         (6, "+0.0%;-0.0%"), (7, "#,##0.00")):
            ws.cell(row=r, column=col).number_format = fmt

    w = getattr(model, "WEIGHTED", {}) or {}
    row += 1
    r = row
    row = put_row(ws, row, "Probability-weighted",
                  [sum((sc.get(k, {}).get("probability", 0) or 0) for k in sc),
                   w.get("target", total_w), None, None,
                   w.get("expected_total_return"), w.get("target", total_w)],
                  bold=True, band=True)
    for col, fmt in ((2, "0%"), (3, "#,##0.00"), (6, "+0.0%;-0.0%"), (7, "#,##0.00")):
        ws.cell(row=r, column=col).number_format = fmt

    row += 1
    for key in ("bull", "base", "bear"):
        s = sc.get(key) or {}
        if s.get("note"):
            row = note(ws, row, "%s — %s" % (key.title(), s["note"]), span=7)
    note(ws, row, "Expected total return includes dividends over the horizon. Bands: "
                  "above +15% BUY, -15% to +15% HOLD, below -15% SELL.", span=7)


def sheet_sensitivity(wb, model):
    sens = getattr(model, "SENSITIVITY", None)
    if not sens:
        return
    ws = wb.create_sheet("Sensitivity")
    row = title(ws, "Sensitivity",
                "%s against %s. Values are the twelve-month target."
                % (sens.get("row_label", ""), sens.get("col_label", "")))
    cols = sens.get("col_values", [])
    row = header_row(ws, row, [sens.get("row_label", "")] + [str(c) for c in cols],
                     [22] + [13] * len(cols))
    for label, line in zip(sens.get("row_values", []), sens.get("grid", [])):
        row = put_row(ws, row, label, line, fmt="#,##0.00")
    note(ws, row + 1, "Column heads are %s." % sens.get("col_label", "the second driver"),
         span=len(cols) + 1)


def sheet_comps(wb, model):
    comps = getattr(model, "COMPS", None)
    if not comps:
        return
    ws = wb.create_sheet("Comps")
    row = title(ws, "Comparable companies",
                "Secondary cross-check. Peers named by the industry analyst.")
    cols = comps.get("columns", [])
    row = header_row(ws, row, ["Company", "Ticker"] + cols,
                     [30, 10] + [13] * len(cols))
    subj = comps.get("subject")
    if subj:
        name, tick, vals = subj
        r = row
        ws.cell(row=row, column=1, value=name).font = BOLD
        ws.cell(row=row, column=2, value=tick).font = BOLD
        for j, v in enumerate(vals, start=3):
            c = ws.cell(row=row, column=j, value=v)
            c.font = BOLD
            c.alignment = RIGHT
            c.number_format = "0.00"
        for j in range(1, 3 + len(vals)):
            ws.cell(row=r, column=j).fill = PatternFill("solid", fgColor=BAND)
            ws.cell(row=r, column=j).border = BOX
        row += 1
    for name, tick, vals in comps.get("rows", []):
        ws.cell(row=row, column=1, value=name).font = BODY
        ws.cell(row=row, column=2, value=tick).font = BODY
        for j, v in enumerate(vals, start=3):
            c = ws.cell(row=row, column=j, value=v)
            c.font = BODY
            c.alignment = RIGHT
            c.number_format = "0.00"
        for j in range(1, 3 + len(vals)):
            ws.cell(row=row, column=j).border = BOX
        row += 1


def sheet_football(wb, model, meta, fm):
    ff = getattr(model, "FOOTBALL", None)
    if not ff:
        return
    ws = wb.create_sheet("Football field")
    row = title(ws, "Valuation ranges",
                "Each method's range against the reference price. Rendered as the "
                "football field exhibit in the report.")
    row = header_row(ws, row, ["Method", "Low", "High", "Midpoint",
                               "Low vs price", "High vs price"],
                     [26, 13, 13, 13, 14, 14])
    price = meta.get("price") or 0
    for entry in ff:
        label, lo, hi = (list(entry) + [None, None])[:3]
        mid = (lo + hi) / 2 if isinstance(lo, (int, float)) and isinstance(hi, (int, float)) else None
        r = row
        row = put_row(ws, row, label,
                      [lo, hi, mid,
                       (lo / price - 1) if price and lo else None,
                       (hi / price - 1) if price and hi else None])
        for col, fmt in ((2, "#,##0.00"), (3, "#,##0.00"), (4, "#,##0.00"),
                         (5, "+0.0%;-0.0%"), (6, "+0.0%;-0.0%")):
            ws.cell(row=r, column=col).number_format = fmt
    row += 1
    r = row
    row = put_row(ws, row, "Reference price", [price], bold=True, band=True)
    ws.cell(row=r, column=2).number_format = "#,##0.00"
    if fm.get("target"):
        r = row
        row = put_row(ws, row, "Twelve-month target", [m2md.num(fm, "target")],
                      bold=True, band=True)
        ws.cell(row=r, column=2).number_format = "#,##0.00"


def sheet_sources(wb, model):
    src = getattr(model, "SOURCES", None)
    if not src:
        return
    ws = wb.create_sheet("Sources")
    row = title(ws, "Sources", "Numbered as they appear in the report appendix.")
    row = header_row(ws, row, ["#", "Source", "Location"], [6, 62, 62])
    for entry in src:
        n, text, loc = (list(entry) + ["", ""])[:3]
        ws.cell(row=row, column=1, value=n).font = BODY
        for j, val in ((2, text), (3, loc)):
            c = ws.cell(row=row, column=j, value=val)
            c.font = BODY
            c.alignment = WRAP
        for j in (1, 2, 3):
            ws.cell(row=row, column=j).border = BOX
        row += 1


# --------------------------------------------------------------------- main --

def build(run_dir, out_path=None):
    run_dir = os.path.abspath(run_dir)
    if not os.path.isdir(run_dir):
        sys.exit("No such run folder: %s" % run_dir)

    fm, _ = m2md.read_note(os.path.join(run_dir, "decision.md"))
    model = load_model(os.path.join(run_dir, "model.py"))
    years, stmts = load_statements(os.path.join(run_dir, "statements.csv"))

    meta = dict(getattr(model, "META", {}) or {})
    for key in ("ticker", "company", "exchange", "run_date"):
        meta.setdefault(key, fm.get(key, ""))
    meta.setdefault("price", m2md.num(fm, "reference_price"))
    meta.setdefault("price_date", fm.get("price_date", ""))
    meta.setdefault("currency", "USD")

    wb = Workbook()
    sheet_readme(wb, meta, fm, bool(stmts), model is not None, years)
    sheet_statement(wb, "Income statement", years, stmts.get("income"),
                    "Ten fiscal years as filed.")
    sheet_statement(wb, "Balance sheet", years, stmts.get("balance"),
                    "Ten fiscal years as filed.")
    sheet_statement(wb, "Cash flow", years, stmts.get("cashflow"),
                    "Ten fiscal years as filed.")
    sheet_common_size(wb, years, stmts.get("income"))
    sheet_statement(wb, "Ratios", years, stmts.get("ratio"),
                    "Ten-year ratio history. Margins, returns, leverage, working capital.")
    sheet_statement(wb, "Segments", years, stmts.get("segment"),
                    "Segment revenue and operating income as disclosed.")
    if model:
        sheet_estimates(wb, model)
        sheet_dcf(wb, model, meta)
        sheet_scenarios(wb, model, meta)
        sheet_sensitivity(wb, model)
        sheet_comps(wb, model)
        sheet_football(wb, model, meta, fm)
        sheet_sources(wb, model)

    if out_path is None:
        exports = os.path.join(run_dir, "exports")
        os.makedirs(exports, exist_ok=True)
        out_path = os.path.join(exports, "%s_Method2_Model_%s.xlsx"
                                % (meta.get("ticker") or "RUN",
                                   meta.get("run_date") or "undated"))
    wb.save(out_path)
    return out_path, wb.sheetnames


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("run_dir")
    ap.add_argument("-o", "--out", default=None)
    args = ap.parse_args()
    out, sheets = build(args.run_dir, args.out)
    print("wrote %s" % out)
    print("sheets: %s" % ", ".join(sheets))


if __name__ == "__main__":
    main()
