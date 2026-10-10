---
ticker: ACME
company: Acme Materials Corporation
latest_call: HOLD
latest_target: 108.50
latest_run: 2026-01-15
---

# Acme Materials Corporation

Invented company, invented figures. See [example/README.md](../README.md).

Industrial coatings and specialty adhesives, sold to manufacturers in North America.
The call rests on whether two named coatings customers, 21% of segment revenue between
three, move from evaluating insourcing to building it.

## Snapshot

| Field | Value |
|---|---|
| Rating | HOLD |
| Twelve-month target | $108.50 |
| Reference price | $100.00 as of 2026-01-09 |
| Expected total return | +10.7% |
| Conviction | moderate |
| Marginal | yes — the 25% bear probability; at 15% the call is BUY |
| Decided by | industry |

Every field above is copied from the newest run's `decision.md` front-matter.

## Runs

| Run | Rating | Target | Reference price | Decided by | Exports |
|---|---|---|---|---|---|
| 2026-01-15 | HOLD | $108.50 | $100.00 | industry | [report](runs/2026-01-15/exports/ACME_Method2_Report_2026-01-15.pdf) · [model](runs/2026-01-15/exports/ACME_Method2_Model_2026-01-15.xlsx) · [workpapers](runs/2026-01-15/exports/ACME_Method2_Workpapers_2026-01-15.docx) |

## Run files, 2026-01-15

Every file the run wrote, in stage order.

| Stage | Files |
|---|---|
| 0 · Preflight | [run](runs/2026-01-15/run.md) |
| 1 · Evidence | [fundamentals](runs/2026-01-15/analyst-fundamentals.md) · [market](runs/2026-01-15/analyst-market.md) · [news](runs/2026-01-15/analyst-news.md) · [industry](runs/2026-01-15/analyst-industry.md) · [statements.csv](runs/2026-01-15/statements.csv) |
| 2 · Valuation | [valuation](runs/2026-01-15/valuation.md) · [model.py](runs/2026-01-15/model.py) |
| 3 · Debate | [bull](runs/2026-01-15/bull.md) · [bear](runs/2026-01-15/bear.md) |
| 4 · Judgment | [decision](runs/2026-01-15/decision.md) |
| 5 · Risk gate | [risk](runs/2026-01-15/risk.md) |
| 6 · Report | [report](runs/2026-01-15/report.md) |
| 7 · Comparison | [comparison](runs/2026-01-15/comparison.md) |

## Divergence from prior coverage

None. ACME has no prior single-analyst node, so this run cannot test whether
adversarial pressure changes a call. See
[comparison.md](runs/2026-01-15/comparison.md).

## Open questions carried forward

Coatings volume in the Q1 print on 2026-04-23, which is the one number that moves the
bear probability and therefore the rating. Then the Dalton ramp at the Q2 print on
2026-07-29, which the bull case needs.
