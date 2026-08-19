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

## Divergence from prior coverage

<What the other process called and when, the gap in rating and target, and where the
two diverged. "No prior coverage" where there is none.>

## Open questions carried forward

<What the next run on this ticker should check first, and the date that settles it.>
