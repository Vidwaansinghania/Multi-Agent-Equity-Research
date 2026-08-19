---
title: <TICKER> — Method 2 run, <YYYY-MM-DD>
ticker: <TICKER>
run_date: <YYYY-MM-DD>
stage: preflight
---

# Run file — <TICKER>, <YYYY-MM-DD>

## What this run is

<Why it is being run: new coverage, a re-run after an earnings print, a divergence
test against prior coverage.>

| Field | Value |
|---|---|
| Ticker | <TICKER> (<EXCHANGE>) |
| Company | <legal name> |
| Reference price | $<price> as of <YYYY-MM-DD> (<close or intraday>) |
| Fiscal year end | <month and day> |
| CIK | <0000000000> |
| Position held | <shares, value, share of portfolio, snapshot date, or "none"> |
| Benchmark for scoring | <SPY> |

## Models

| Stage | Model |
|---|---|
| Analysts (1) | <model> |
| Valuation, debate, judgment, risk, report (2–6) | <model> |

## Filings resolved in preflight

| What | Where |
|---|---|
| Most recent 10-K | <accession, filing date, primary document URL> |
| 8-K 1 | <date, URL> |
| 8-K 2 | <date, URL> |
| 8-K 3 | <date, URL> |
| 8-K 4 | <date, URL> |
| Company facts | `companyfacts.json` in this folder |

## Market data budget

<Connectors in use, in order, and the cap. What an earlier run today already spent.
Fill in the calls actually made once stage 1 closes.>

## Prior lessons read

<Scored calls-log rows for this ticker, up to five, plus the three most recent scored
rows on any ticker. These go to the judge in stage 4 and to nobody else. Write "none"
where the log has no scored rows.>

## Brand palette

<Hex values and where they came from: published CSS tokens, a brand book, or the logo
sampled. Contrast results from the build log.>

## Close

<Which stages ran, which artefacts built, where the run stopped if it did. A run
missing decision.md is abandoned and this is where that gets recorded.>
