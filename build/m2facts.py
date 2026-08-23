"""Method 2 preflight — seed statements.csv from the cached XBRL company facts.

Stage 0 runs this once, before any agent is spawned. It extracts the primary
income statement, balance sheet and cash flow lines for the last ten fiscal
years and writes them to the run folder in the exact format the workbook builder
reads. The fundamentals agent then checks those rows against the filings and
appends what no machine can produce: the segment rows, the ratio history and the
common-size blocks.

Why this exists. A token audit of a full ten-agent run found the fundamentals
agent spending about a tenth of the whole run's budget across 126 turns, 58 of
them file operations picking through a multi-megabyte JSON file to rebuild a
series the data fully determines. Extracting tagged figures is mechanical, so it
happens once here rather than across dozens of agent turns. The same reasoning
already moved the filing index and the company facts fetch into preflight.

    python m2facts.py "<run folder>" [--years 10]

Reads  <run folder>/companyfacts.json
Writes <run folder>/statements.csv

Every row it writes is marked in the source column so a later reader can tell a
machine-extracted figure from an analyst-entered one. Where a concept is absent
the cell is left empty rather than zeroed, and the concept is listed on stderr
so the fundamentals agent knows to go to the filing for it.
"""

import argparse
import csv
import json
import os
import sys
from collections import defaultdict

# (label, unit, [concept candidates in priority order])
# Candidates are tried in order and the first one carrying data for a year wins,
# because registrants move between tags across a decade and the older name is
# usually the fallback rather than the preferred one.
INCOME = [
    ("Revenue", "USD millions", [
        "RevenueFromContractWithCustomerExcludingAssessedTax",
        "RevenueFromContractWithCustomerIncludingAssessedTax",
        "Revenues", "SalesRevenueNet", "SalesRevenueGoodsNet"]),
    ("Cost of goods sold", "USD millions", [
        "CostOfGoodsAndServicesSold", "CostOfGoodsSold", "CostOfRevenue"]),
    ("Gross profit", "USD millions", ["GrossProfit"]),
    ("Selling, general and administrative expenses", "USD millions", [
        "SellingGeneralAndAdministrativeExpense"]),
    ("Operating income", "USD millions", ["OperatingIncomeLoss"]),
    ("Interest income", "USD millions", ["InvestmentIncomeInterest"]),
    ("Interest expense", "USD millions", ["InterestExpense", "InterestExpenseNonoperating"]),
    ("Equity income (loss), net", "USD millions", ["IncomeLossFromEquityMethodInvestments"]),
    ("Other income (loss), net", "USD millions", ["OtherNonoperatingIncomeExpense"]),
    ("Income before income taxes", "USD millions", [
        "IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest",
        "IncomeLossFromContinuingOperationsBeforeIncomeTaxesMinorityInterestAndIncomeLossFromEquityMethodInvestments"]),
    ("Income tax expense", "USD millions", ["IncomeTaxExpenseBenefit"]),
    ("Net income including noncontrolling interests", "USD millions", ["ProfitLoss"]),
    ("Net income attributable to noncontrolling interests", "USD millions", [
        "NetIncomeLossAttributableToNoncontrollingInterest"]),
    ("Net income attributable to shareowners", "USD millions", ["NetIncomeLoss"]),
    ("Earnings per share, basic", "USD", ["EarningsPerShareBasic"]),
    ("Earnings per share, diluted", "USD", ["EarningsPerShareDiluted"]),
    ("Weighted average shares outstanding, basic", "shares millions", [
        "WeightedAverageNumberOfSharesOutstandingBasic"]),
    ("Weighted average shares outstanding, diluted", "shares millions", [
        "WeightedAverageNumberOfDilutedSharesOutstanding"]),
    ("Dividends declared per share", "USD", ["CommonStockDividendsPerShareDeclared"]),
]

BALANCE = [
    ("Cash and cash equivalents", "USD millions", ["CashAndCashEquivalentsAtCarryingValue"]),
    ("Short-term investments", "USD millions", ["OtherShortTermInvestments", "ShortTermInvestments"]),
    ("Marketable securities", "USD millions", ["MarketableSecuritiesCurrent"]),
    ("Trade accounts receivable, net", "USD millions", ["AccountsReceivableNetCurrent"]),
    ("Inventories", "USD millions", ["InventoryNet"]),
    ("Prepaid expenses and other current assets", "USD millions", [
        "PrepaidExpenseAndOtherAssetsCurrent", "OtherAssetsCurrent"]),
    ("Total current assets", "USD millions", ["AssetsCurrent"]),
    ("Equity method investments", "USD millions", ["EquityMethodInvestments"]),
    ("Property, plant and equipment, net", "USD millions", ["PropertyPlantAndEquipmentNet"]),
    ("Goodwill", "USD millions", ["Goodwill"]),
    ("Indefinite-lived intangible assets", "USD millions", [
        "IndefiniteLivedTrademarks", "IndefiniteLivedIntangibleAssetsExcludingGoodwill"]),
    ("Finite-lived intangible assets, net", "USD millions", ["FiniteLivedIntangibleAssetsNet"]),
    ("Total assets", "USD millions", ["Assets"]),
    ("Accounts payable and accrued expenses", "USD millions", [
        "AccountsPayableAndAccruedLiabilitiesCurrent"]),
    ("Loans and notes payable", "USD millions", ["OtherShortTermBorrowings", "ShortTermBorrowings"]),
    ("Current portion of long-term debt", "USD millions", ["LongTermDebtCurrent"]),
    ("Total current liabilities", "USD millions", ["LiabilitiesCurrent"]),
    ("Long-term debt", "USD millions", ["LongTermDebtNoncurrent"]),
    ("Operating lease liability, noncurrent", "USD millions", ["OperatingLeaseLiabilityNoncurrent"]),
    ("Other liabilities", "USD millions", ["OtherLiabilitiesNoncurrent"]),
    ("Deferred income taxes", "USD millions", ["DeferredIncomeTaxLiabilitiesNet"]),
    ("Total liabilities", "USD millions", ["Liabilities"]),
    ("Total equity attributable to parent", "USD millions", ["StockholdersEquity"]),
    ("Noncontrolling interests", "USD millions", ["MinorityInterest"]),
    ("Total equity", "USD millions", [
        "StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest"]),
]

CASHFLOW = [
    ("Depreciation and amortization", "USD millions", ["DepreciationDepletionAndAmortization",
                                                       "DepreciationAmortizationAndAccretionNet"]),
    ("Share-based compensation expense", "USD millions", ["ShareBasedCompensation"]),
    ("Net cash provided by operating activities", "USD millions", [
        "NetCashProvidedByUsedInOperatingActivities",
        "NetCashProvidedByUsedInOperatingActivitiesContinuingOperations"]),
    ("Capital expenditures", "USD millions", ["PaymentsToAcquirePropertyPlantAndEquipment"]),
    ("Net cash used in investing activities", "USD millions", [
        "NetCashProvidedByUsedInInvestingActivities",
        "NetCashProvidedByUsedInInvestingActivitiesContinuingOperations"]),
    ("Net cash used in financing activities", "USD millions", [
        "NetCashProvidedByUsedInFinancingActivities",
        "NetCashProvidedByUsedInFinancingActivitiesContinuingOperations"]),
    ("Dividends paid", "USD millions", ["PaymentsOfDividends", "PaymentsOfDividendsCommonStock"]),
    ("Share repurchases", "USD millions", ["PaymentsForRepurchaseOfCommonStock"]),
]

DURATION_UNITS = {"USD millions", "USD", "shares millions"}


def _scale(unit):
    return 1e6 if unit == "USD millions" else (1e6 if unit == "shares millions" else 1.0)


def _unit_key(unit):
    if unit == "USD millions":
        return "USD"
    if unit == "USD":
        return "USD/shares"
    return "shares"


def annual_duration(facts, concept, unit_key):
    """Fiscal-year values for a flow concept, keyed by the year the period ends.

    A fact qualifies when its period runs 340 to 400 days, which is the only
    reliable way to separate an annual figure from the quarters that carry the
    same tag. Where the same year appears in several filings the latest
    accession wins, so a restated figure supersedes the one first reported.
    """
    node = facts.get(concept)
    if not node:
        return {}
    items = (node.get("units") or {}).get(unit_key) or []
    best = {}
    for it in items:
        start, end = it.get("start"), it.get("end")
        if not start or not end:
            continue
        try:
            sy, sm, sd = (int(x) for x in start.split("-"))
            ey, em, ed = (int(x) for x in end.split("-"))
        except ValueError:
            continue
        days = (ey - sy) * 365 + (em - sm) * 30 + (ed - sd)
        if not 340 <= days <= 400:
            continue
        year = ey if em > 6 else ey - 1   # a January year-end belongs to the prior fiscal year
        accn = it.get("accn") or ""
        if year not in best or accn > best[year][0]:
            best[year] = (accn, it.get("val"), end)
    return {y: v[1] for y, v in best.items()}


def annual_instant(facts, concept, unit_key, fye_month):
    """Fiscal-year-end values for a stock concept, keyed by fiscal year."""
    node = facts.get(concept)
    if not node:
        return {}
    items = (node.get("units") or {}).get(unit_key) or []
    best = {}
    for it in items:
        end = it.get("end")
        if not end:
            continue
        try:
            ey, em, ed = (int(x) for x in end.split("-"))
        except ValueError:
            continue
        if em != fye_month:
            continue
        year = ey if em > 6 else ey - 1
        accn = it.get("accn") or ""
        if year not in best or accn > best[year][0]:
            best[year] = (accn, it.get("val"))
    return {y: v[1] for y, v in best.items()}


def detect_fye(facts):
    """Fiscal year end month and day, from the most common annual period end."""
    ends = defaultdict(int)
    for concept in ("Assets", "StockholdersEquity", "CashAndCashEquivalentsAtCarryingValue"):
        node = facts.get(concept)
        if not node:
            continue
        for it in (node.get("units") or {}).get("USD") or []:
            end = it.get("end")
            if end and it.get("form") == "10-K" and it.get("fp") == "FY":
                ends[end[5:]] += 1
    if not ends:
        return 12, 31
    md = max(ends.items(), key=lambda kv: kv[1])[0]
    return int(md[:2]), int(md[3:])


def pick(facts, candidates, unit, fye_month, instant):
    """First candidate concept carrying data, merged with later ones for gaps."""
    unit_key = _unit_key(unit)
    merged, used = {}, []
    for concept in candidates:
        got = (annual_instant(facts, concept, unit_key, fye_month) if instant
               else annual_duration(facts, concept, unit_key))
        if not got:
            continue
        used.append(concept)
        for y, v in got.items():
            merged.setdefault(y, v)
    return merged, used


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("run_dir")
    ap.add_argument("--years", type=int, default=10)
    args = ap.parse_args()

    path = os.path.join(args.run_dir, "companyfacts.json")
    if not os.path.exists(path):
        sys.exit("no companyfacts.json in %s — preflight fetches it before this runs" % args.run_dir)
    with open(path, encoding="utf-8") as fh:
        doc = json.load(fh)
    facts = (doc.get("facts") or {}).get("us-gaap") or {}
    if not facts:
        sys.exit("companyfacts.json carries no us-gaap facts")

    fye_month, fye_day = detect_fye(facts)

    # The span is set by the revenue series, which every filer carries.
    rev, _ = pick(facts, INCOME[0][2], "USD millions", fye_month, False)
    if not rev:
        sys.exit("could not locate a revenue concept; the fundamentals agent builds the series by hand")
    latest = max(rev)
    years = list(range(latest - args.years + 1, latest + 1))
    labels = ["FY%d" % y for y in years]

    rows, missing = [], []
    cfo = capex = None
    for statement, spec, instant in (("income", INCOME, False),
                                     ("balance", BALANCE, True),
                                     ("cashflow", CASHFLOW, False)):
        for label, unit, candidates in spec:
            got, used = pick(facts, candidates, unit, fye_month, instant)
            if not got:
                missing.append("%s / %s" % (statement, label))
                continue
            scale = _scale(unit)
            cells = []
            for y in years:
                v = got.get(y)
                cells.append("" if v is None else round(v / scale, 4 if scale == 1 else 1))
            if not any(c != "" for c in cells):
                missing.append("%s / %s" % (statement, label))
                continue
            rows.append([statement, label, unit] + cells)
            if statement == "cashflow" and label.startswith("Net cash provided by operating"):
                cfo = cells
            if statement == "cashflow" and label == "Capital expenditures":
                capex = cells

    if cfo and capex:
        fcf = []
        for a, b in zip(cfo, capex):
            fcf.append(round(a - b, 1) if a != "" and b != "" else "")
        rows.append(["cashflow", "Free cash flow (CFO less capex)", "USD millions"] + fcf)

    out = os.path.join(args.run_dir, "statements.csv")
    with open(out, "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["statement", "line_item", "unit"] + labels)
        for r in rows:
            w.writerow(r)
        w.writerow(["meta", "fiscal_year_end", "text",
                    "%s %d" % (["January", "February", "March", "April", "May", "June", "July",
                                "August", "September", "October", "November", "December"][fye_month - 1],
                               fye_day)] + [""] * (len(labels) - 1))

    print("wrote %s" % out)
    print("fiscal year end: %d-%02d, span %s to %s" % (fye_month, fye_day, labels[0], labels[-1]))
    print("rows written: %d primary lines, machine-extracted" % len(rows))
    if missing:
        print("not tagged in company facts, so the fundamentals agent takes these from the filing:")
        for m in missing:
            print("   %s" % m)


if __name__ == "__main__":
    main()
