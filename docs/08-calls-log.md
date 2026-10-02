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

`build/score_calls.py` does steps 1 to 4 except the reflection:

```bash
python build/score_calls.py                  # list what is due and score it, change nothing
python build/score_calls.py --write          # move the scored rows into the scored table
python build/score_calls.py --early ACME     # score a pending call before its review date
```

Each row is scored on its own terms, so a ticker refreshed into a second row has
each row scored from its own call date; `--early ACME:2026-01-15` picks one of them.
A row whose status reads `withdrawn` is not scored, stays where it is, and its run is
left out of the tally below.

It takes the benchmark from the row's Benchmark column, falling back to
`scoring.benchmark_home` for a listing in the home currency and `scoring.benchmark`
otherwise. Both legs come from one source, Yahoo's daily adjusted close by default,
which carries dividends, so a ratio of two adjusted closes is a total return. The
source is written into the Scored cell. `--prices` reads a CSV of
`symbol,date,adjclose` instead. The fetch is the script's own, not a market-data
connector, so it spends none of the market agent's quota.

A HOLD counts as right when alpha lands within the HOLD band's half-width, ±15
points, because a HOLD claims the name will track its benchmark rather than that it
will return between −15% and +15% in absolute terms. `--hold-band` narrows it for a
stricter reading. The script also warns when the close it found on the call date is
more than 2% from the logged price at call, which usually means the wrong symbol.

## Is the debate earning its cost

Every run of the script ends with a tally of `decided_by` across every closed run
under the research root, scored or not, grouped into analysts, valuation and debate.
For the scored ones it shows how many were directionally right and the mean alpha as
called: alpha on BUYs, minus alpha on SELLs. `--tally-only` prints the tally without
fetching a price. Below a dozen runs and a dozen scored calls it says the sample is
too small, and it is.

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

The script scores what is due, but only when someone runs it. Run it in the month the
first call comes due and on a monthly reminder after that, or the log quietly becomes
a list of unfalsified opinions, which is the exact failure it exists to prevent.
