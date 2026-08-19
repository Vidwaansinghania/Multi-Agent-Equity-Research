# 08 · Calls log

Every call either gets scored or it never happened. This is the only file in the
process that gets more valuable with time, and it is the part most worth keeping
even if the fan-out turns out to add nothing.

The log lives at `paths.calls_log`, defaulting to `research/calls-log.md`. Start it
from [templates/calls-log.md](../templates/calls-log.md).

## Score against alpha, not raw return

A HOLD on a name that fell 20% while the index fell 2% was a bad call. A HOLD on a
name that fell 20% while the index fell 25% was a good one. Raw return mostly
measures the market, and the point of the log is to measure the process.

## Open calls

One row per call, appended when the run closes.

| Ticker | Method | Call date | Call | Price at call | Target | Implied price return | Benchmark | Review due | Status |
|---|---|---|---|---|---|---|---|---|---|
| ACME | 2 | 2026-01-15 | HOLD | $100.00 | $108.50 | +8.5% | SPY | 2027-01-15 | pending |

Implied return in this table is price to target only. Where dividends matter the
decision record's total-return figure differs slightly, and the record governs.

Seed the table with any prior calls from another process on the same tickers. Rows
from two processes on one ticker are what makes a head-to-head comparison possible,
and they only work if both were logged at the time rather than reconstructed later.

## Scored calls

| Ticker | Method | Call date | Call | Raw return | Benchmark return | Alpha | Direction right | Scored |
|---|---|---|---|---|---|---|---|---|

## How to score a call

Run this when a review date comes up, or earlier if the thesis has visibly settled.
A name that hit its target in four months, or a bear case that arrived on one
earnings call, can be scored early and marked as such.

1. Get the price on the review date and the benchmark's price on both the call date
   and the review date. Same source for both, and record which.
2. Raw return is price change plus dividends received over the period. Alpha is raw
   return minus the benchmark's total return over the same window.
3. Decide whether the direction was right. A BUY is right if the name beat its
   benchmark; a SELL is right if it lagged; a HOLD is right if the name landed
   inside roughly the band the call implied, which is the hardest of the three to
   judge and should be judged strictly.
4. Move the row to the scored table and write the reflection.

## Reflections

Two to four sentences of plain prose per scored call, no headings and no bullets.
Cover, in order: whether the directional call was right, citing the alpha figure;
which part of the thesis held and which failed; and one concrete lesson for the next
analysis of a similar name.

The length cap is the point. These get re-read at the start of every future run on
the ticker, so they compete for context with the filings, and a page of reflection
per call would crowd out the evidence. Write them so a future run learns something
in fifteen seconds.

## How a run uses this file

At preflight, before any agent is spawned, the orchestrator reads every scored entry
for the ticker being run, up to the five most recent, plus the three most recent
scored entries for any other ticker, for cross-name lessons.

Those go into the judge's context in stage 4, labelled as prior lessons. They do not
go to the analysts, whose job is to read the evidence in front of them rather than
to inherit a conclusion.

Pending entries are never fed forward. An unscored call is an opinion, and feeding a
run its own past opinions is how a process talks itself into consistency it has not
earned.

## Known gap

Nothing scores automatically. Someone has to run the review on the due date, and if
nobody does, the log quietly becomes a list of unfalsified opinions, which is the
exact failure it exists to prevent. Set a recurring reminder for the month the first
call comes due.
