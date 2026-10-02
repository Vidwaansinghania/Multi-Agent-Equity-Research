# Calls log

Every call either gets scored or it never happened. Append-only: rows move from the
open table to the scored table and are not rewritten. How to score one is in
[docs/08-calls-log.md](../docs/08-calls-log.md).

Scoring is against alpha rather than raw return, because raw return mostly measures
the market.

## Open calls

| Ticker | Method | Call date | Call | Price at call | Target | Implied price return | Benchmark | Review due | Status |
|---|---|---|---|---|---|---|---|---|---|
| | | | | | | | | | pending |

Status here is `pending` or `withdrawn`; a scored row moves to the scored table. A refresh that moves the call or the
target is a new row; the old row is never edited. A withdrawn call keeps its row,
marked `withdrawn` with the reason, and is not scored.

Implied return here is price to target only. Where dividends matter the decision
record's total-return figure differs slightly, and the record governs.

## Scored calls

| Ticker | Method | Call date | Call | Raw return | Benchmark return | Alpha | Direction right | Scored |
|---|---|---|---|---|---|---|---|---|

## Reflections

Two to four sentences per scored call, plain prose, no headings. Whether the
directional call was right and the alpha figure; which part of the thesis held and
which failed; one concrete lesson for the next name like it. These get re-read at the
start of every future run on the ticker, so they compete with the filings for
context — write them to be useful in fifteen seconds.
