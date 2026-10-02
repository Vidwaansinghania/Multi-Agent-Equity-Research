---
ticker: <TICKER>
company: <legal name>
latest_call: <BUY | HOLD | SELL>
latest_target: <price>
latest_run: <YYYY-MM-DD>
---

# <Company>

<One line: what the business is and what the current call rests on.>

## Snapshot

| Field | Value |
|---|---|
| Rating | <BUY / HOLD / SELL> |
| Twelve-month target | $<price> |
| Reference price | $<price> as of <YYYY-MM-DD> |
| Expected total return | <+X.X%> |
| Conviction | <low / moderate / high> |
| Marginal | <yes, and the flipping assumption / no> |
| Decided by | <stage> |

Every field above is copied from the newest run's `decision.md` front-matter and
never computed here.

## Runs

| Run | Rating | Target | Reference price | Decided by | Exports |
|---|---|---|---|---|---|
| <YYYY-MM-DD> | <call> | $<price> | $<price> | <stage> | [report](runs/<DATE>/exports/<TICKER>_Method2_Report_<DATE>.pdf) · [model](runs/<DATE>/exports/<TICKER>_Method2_Model_<DATE>.xlsx) · [workpapers](runs/<DATE>/exports/<TICKER>_Method2_Workpapers_<DATE>.docx) |

## Run files

One table per run, newest first, linking every stage file in the order it was
produced. A closed run is never edited, so these links live here rather than in
`run.md`.

| Stage | File |
|---|---|
| 0 · Preflight | [run.md](runs/<DATE>/run.md) |
| 1 · Evidence | [fundamentals](runs/<DATE>/analyst-fundamentals.md) · [market](runs/<DATE>/analyst-market.md) · [news](runs/<DATE>/analyst-news.md) · [industry](runs/<DATE>/analyst-industry.md) · [statements.csv](runs/<DATE>/statements.csv) |
| 2 · Base case | [valuation.md](runs/<DATE>/valuation.md) · [model.py](runs/<DATE>/model.py) |
| 3 · Debate | [bull.md](runs/<DATE>/bull.md) · [bear.md](runs/<DATE>/bear.md) |
| 4 · Judgment | [decision.md](runs/<DATE>/decision.md) |
| 5 · Risk gate | [risk.md](runs/<DATE>/risk.md) |
| 6 · Report | [report.md](runs/<DATE>/report.md) |
| 7 · Close | [comparison.md](runs/<DATE>/comparison.md) |

## Divergence from prior coverage

<What the other process called and when, the gap in rating and target, and where the
two diverged. "No prior coverage" where there is none.>

## Open questions carried forward

<What the next run on this ticker should check first, and the date that settles it.>
