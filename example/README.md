# Worked example

`Acme/runs/2026-01-15/` is a complete run: every file the eight stages produce, plus
the three artefacts built from them.

**Acme Materials Corporation does not exist.** The ticker, the filings, the customers,
the peers and every figure are invented. The run is a fixture that exercises the
builders and shows the shape of a real run, and it is not a view on any security.

## What it covers

The numbers hang together, which is the point of a fixture. Ten fiscal years in
`statements.csv` feed the workbook's history sheets. `model.py` discounts a ten-year
free cash flow path at 8.5% on the mid-year convention to $105.09 a share, with the
terminal value at 56.9% of enterprise value. Three scenarios at 25/50/25 weight
reconcile to the $108.50 weighted target in `decision.md`, which is +10.7% including
dividends and therefore HOLD, marginal, 4.3 points inside the band edge.

It also exercises the parts that only appear in awkward cases. The judge attributes the
call to the industry analyst rather than to the valuation agent, so `decided_by` is not
the obvious value. `position` is null, so the disclosure block takes its no-position
branch. And the risk gate charges a currency round trip against the expected return,
which is the arithmetic that decides whether acting on a marginal call pays at all.

## Rebuild it

```bash
python build/build_workpapers.py example/Acme/runs/2026-01-15
```

```bash
python build/build_workbook.py example/Acme/runs/2026-01-15
```

```bash
python build/build_report.py example/Acme/runs/2026-01-15 --brand "#1F5C8B" --brand-source "investor relations stylesheet"
```

Expect twelve DOCX sections, fourteen workbook sheets and a six-page PDF. The report
build prints its contrast checks, the font it actually used, and every sentence the
plumbing strip removed.

`_generate_statements.py` wrote `statements.csv` from a handful of base series so the
derived rows and ratios stay consistent. It exists for the fixture only; a real run's
CSV is written by the fundamentals agent out of the filings.

## What is missing on purpose

`companyfacts.json`, which preflight would have saved here. It is large, reproducible
from the SEC, and gitignored.
