# 05 · Output schema

Two typed files carry every number a run produces. `decision.md` front-matter holds
the call. `model.py` holds the valuation. The workbook, the PDF, the company index
and the calls-log row all read from those two and keep no copy of their own.

Keeping a rating in four hand-maintained places is how ratings drift. This is the
fix, and it only works if nothing downstream retypes a number.

## The decision front-matter contract

Every `decision.md` opens with exactly this block. Fields are required unless
marked optional. The values below are from the worked example, whose company is
invented.

```yaml
---
method: 2
ticker: ACME
exchange: NYSE
company: Acme Materials Corporation
run_date: 2026-01-15
reference_price: 100.00
price_date: 2026-01-09
rating: HOLD                        # BUY | HOLD | SELL — no other value is valid
target: 108.50
target_horizon_months: 12
expected_total_return: 0.107        # decimal, includes dividends over the horizon
conviction: moderate                # low | moderate | high
marginal: true                      # is this within 5 points of a band edge
flip_assumption: >
  The 25% bear probability, which rests on two named coatings customers
  evaluating insourcing. At 15% bear and 35% base the weighted target is $117.15
  and the expected total return is +19.4%, which is BUY.
decided_by: industry                # which stage carried the call
scenarios:
  bull:  { probability: 0.25, target: 138.00 }
  base:  { probability: 0.50, target: 112.00 }
  bear:  { probability: 0.25, target: 72.00 }
position: null                       # from the holdings snapshot, or null
models:
  analysts: claude-sonnet-5
  decision: claude-opus-5
  report: claude-opus-5
alpha_vantage_calls: 6              # total market-data calls, against the cap
---
```

Where a position exists, `position` is a mapping rather than null:

```yaml
position:
  shares: 12.4
  value: 1240.00
  currency: CAD
  portfolio_pct: 0.031
  snapshot_date: 2026-01-12
```

Rules on the fields:

| Field | Rule |
|---|---|
| `rating` | Exactly `BUY`, `HOLD` or `SELL`. A run producing anything else is a failed run, not a new rating |
| `expected_total_return` | Decimal, not a percentage string. Must be consistent with the band the rating claims |
| `marginal` | `true` when the expected return sits within 5 percentage points of +15% or −15%. When true, `flip_assumption` must be specific enough to test |
| `decided_by` | One of `fundamentals`, `market`, `news`, `industry`, `valuation`, `bull`, `bear`. This is the field that makes per-stage attribution possible after a dozen runs |
| `scenarios` | Probabilities sum to 1. The weighted target must reconcile to `target` |
| `position` | Copied from the preflight snapshot, or `null` with a note in the prose. Never inferred |
| `models` | Recorded because a call scored in twelve months is only interpretable if you know what produced it |
| `alpha_vantage_calls` | Total market-data calls across every connector. A run reporting more than the cap spent quota that belongs to another task, and the overage gets recorded in `run.md` |

## The bands

| Probability-weighted twelve-month total return | Rating |
|---|---|
| Above +15% | BUY |
| −15% to +15% | HOLD |
| Below −15% | SELL |

Map the number onto the band and take the answer. There is no fourth tier, no
paired label, and no rating that means "HOLD but I like it." Where the answer is
uncomfortable, `marginal` and `flip_assumption` are where that goes.

## The decision prose sections

After the front-matter, in this order.

1. The call. Rating, target, expected return, conviction, in three sentences.
   Someone reading only this should be able to act.
2. What decided it. The analyst finding or the side of the debate that carried the
   decision, named.
3. The scenarios. The table, with a paragraph on each defending its probability.
4. Where the debate landed. Both attacks, including the one rejected and the
   reason. A rejected argument that turns out right in twelve months is the most
   valuable thing in the archive, and it only exists if it was written down.
5. How marginal. The distance to the band edge and the flipping assumption, with
   the sensitivity numbers.
6. Entry discipline. Price table. Actions, separate from the rating.
7. Ownership and conflicts. The position as fact from the snapshot: company, share
   count, share of portfolio, snapshot date, nothing else.
8. Disclaimer. Educational and research only, not investment advice.

## The model.py contract

Written by the valuation agent in stage 2 and imported by both export builders, so
it is the only copy of these figures that exists. Plain literals only: no imports,
no I/O, no computation beyond arithmetic on literals already stated. A missing
optional key is fine and the builder skips that exhibit; a misspelled key is a
failed build.

The complete, working example is
[example/Acme/runs/2026-01-15/model.py](../example/Acme/runs/2026-01-15/model.py),
and an empty one to copy is [templates/model.py](../templates/model.py). The
structure:

```python
META = {
    "ticker": "ACME", "company": "Acme Materials Corporation", "exchange": "NYSE",
    "currency": "USD", "price": 100.00, "price_date": "2026-01-09",
    "run_date": "2026-01-15", "fiscal_year_end": "Dec 31",
    "shares_diluted": 250.0,      # millions
    "dividend_12m": 2.20,         # per share, over the target horizon
}

DCF = {
    "wacc": 0.085, "terminal_growth": 0.025,
    "discounting": "mid-year",            # "mid-year" | "year-end"
    # the part-year between the run date and the next fiscal year end, or None
    "stub": None,
    "years": ["FY2026E", ..., "FY2035E"],          # ten labels
    "fcf": [1_440.0, ..., 2_115.0],                # ten figures, USD millions
    "t": [0.5, 1.5, ..., 9.5],                     # discount period per year
    "terminal_method": "perpetuity growth",        # exit multiple is a cross-check
    "terminal_roic": 0.14,
    "terminal_reinvestment_rate": 0.179,           # terminal_growth / terminal_roic
    "pv_forecast": 12_092.1, "terminal_value": 36_131.2, "pv_terminal": 15_980.3,
    "tv_share_of_ev": 0.569,
    "enterprise_value": 28_072.4, "net_debt": 1_800.0,
    "net_debt_basis": "Funded debt less cash; operating leases charged to opex",
    "equity_value": 26_272.4, "value_per_share": 105.09,
    "reverse_dcf": {"implied_growth": 0.021, "implied_margin": 0.193,
                    "implied_wacc": 0.0884, "implied_terminal_growth": 0.0205,
                    "verdict": "..."},
    # (label, value as text, basis and source) — rendered as the assumptions sheet
    "assumptions": [("WACC", "8.50%", "CAPM, DGS10 4.20% + 5.0% ERP, beta 1.02")],
}

SCENARIOS = {   # probabilities must sum to 1.0
    "bull": {"probability": 0.25, "target": 138.00, "exit_multiple": 24.0,
             "eps": 5.75, "note": "..."},
    "base": {...}, "bear": {...},
}

WEIGHTED = {"target": 108.50, "expected_total_return": 0.107,
            "horizon_months": 12}

ESTIMATES = {   # three actual years then two estimated
    "years": ["FY2023A", "FY2024A", "FY2025A", "FY2026E", "FY2027E"],
    "rows": [("Revenue (USD m)", [7_620.0, 7_980.0, 8_400.0, 8_820.0, 9_260.0])],
}

SENSITIVITY = {
    "row_label": "Exit multiple", "row_values": [17.0, 18.5, 20.5, 21.5, 23.0],
    "col_label": "FY2027E EPS", "col_values": [5.15, 5.45, 5.75],
    "grid": [[87.6, 92.7, 97.8], ...],             # targets, rows × cols
}

COMPS = {
    "columns": ["P/E fwd", "EV/EBITDA", "EV/Sales", "FCF yield"],
    "subject": ("Acme Materials", "ACME", [19.7, 14.1, 3.3, 0.054]),
    "rows": [("Northbridge Chemical", "NBC", [17.2, 11.8, 2.4, 0.061])],
}

FOOTBALL = [   # (label, low, high)
    ("DCF", 94.70, 118.16),
    ("Comparables", 98.00, 126.00),
    ("52-week range", 84.20, 121.60),
    ("Street targets", 95.00, 130.00),
    ("Scenario range", 72.00, 138.00),
]

SOURCES = [   # numbered in the appendix in this order
    (1, "Form 10-K for fiscal 2025, filed 2026-02-18", "sec.gov/Archives/..."),
]
```

Rules on the module:

| Key | Rule |
|---|---|
| `META` | `price` and `price_date` must equal the preflight reference price. An agent that fetched its own price shows up here first |
| `DCF` | Ten explicit forecast years, then the terminal value. `t` is the discount period of each year and must match `years` in length; the workbook discounts on those figures rather than assuming a convention, so a mid-year run and a year-end run both come out right. `terminal_reinvestment_rate` must equal `terminal_growth / terminal_roic`. `stub` is `None` where the run date sits on a fiscal year end. `tv_share_of_ev` above 0.70 gets a line on the DCF sheet saying the valuation is mostly a claim about the year after the forecast |
| `SCENARIOS` | Probabilities sum to 1.0. The three targets must reconcile to `WEIGHTED["target"]` on those weights |
| `WEIGHTED` | After stage 4 this must equal `decision.md` front-matter. Where the judge overrode the valuation agent, the orchestrator patches this and rebuilds |
| `SENSITIVITY` | `grid` is rows × cols and its dimensions must match the two value lists |
| `FOOTBALL` | Every row is a genuine range. Where a range has one value, give it as a range of zero width rather than omitting the row |
| `SOURCES` | Numbered from 1, in the order they appear in the appendix |

## statements.csv

Written by the fundamentals agent in stage 1 and read by the workbook builder
directly. One header row, then one row per line item:

```
statement,line_item,unit,FY2016,FY2017,...,FY2025
income,Revenue,USD millions,5200,5480,...,8400
```

`statement` is one of `income`, `balance`, `cashflow`, `segment`, `ratio`. `unit` is
one of `USD millions`, `USD`, `shares millions`, `percent`, `ratio`, `days`. Year
columns run oldest to newest in the company's own fiscal labels. An empty cell for
a year with no figure, never a zero and never "n/a". The first data row is revenue.
A final `meta,fiscal_year_end,text,<month and day>` row closes the file.

The example is
[example/Acme/runs/2026-01-15/statements.csv](../example/Acme/runs/2026-01-15/statements.csv).

## Which file wins

`decision.md` front-matter is authoritative for the rating, the target, the expected
return and the scenario probabilities. `model.py` is authoritative for everything
else.

When the judge sets a target different from the valuation agent's, the orchestrator
patches `WEIGHTED` in `model.py` and rebuilds both artefacts. Editing `decision.md`
to match the model is the wrong direction and inverts the process: the judge rules,
the model records.

## Why typed at all

The framework this borrows from parses its rating out of prose with a regular
expression, and when the pattern misses it defaults to Hold. A parsing failure then
quietly manufactures a call no agent made. Typed fields with a fixed set of allowed
values mean the failure surfaces as a failure.

There is a second payoff. Because `decision.md` front-matter is the only place the
rating and target live, any query over `<research_root>/*/runs/` gives a coverage
table for free, and it cannot drift from the underlying records the way a
hand-maintained table does.
