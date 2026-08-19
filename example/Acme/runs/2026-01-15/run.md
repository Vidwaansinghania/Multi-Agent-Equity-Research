---
title: ACME — Method 2 run, 2026-01-15
ticker: ACME
run_date: 2026-01-15
stage: closed
---

# Run file — ACME, 2026-01-15

Acme Materials Corporation is invented, and so is every figure in this run
folder. The folder exists to show the shape of a run and to give the export
scripts something to build from. Nothing here is a view on a real security.

## What this run is

A scheduled first pass on a name with no prior coverage. No position is held.

| Field | Value |
|---|---|
| Ticker | ACME (NYSE) |
| Company | Acme Materials Corporation |
| Reference price | $100.00 as of 2026-01-09 (close) |
| Fiscal year end | December 31 |
| CIK | 0000000000 (fictional) |
| Position held | none — snapshot 2026-01-12 shows no ACME |
| Benchmark for scoring | SPY |

## Models

| Stage | Model |
|---|---|
| Analysts (1) | claude-sonnet-5 |
| Valuation, debate, judgment, risk, report (2–6) | claude-opus-5 |

## Filings resolved in preflight

| What | Where |
|---|---|
| Most recent 10-K | fiscal 2025, filed 2026-02-18 |
| Last four 8-Ks | 2025-10-29, 2025-07-30, 2025-04-24, 2025-02-18 |
| Company facts | `companyfacts.json` in this folder (omitted from the example) |

## Market data budget

Six calls made against a daily cap of 75, all by the market analyst: one quote,
one daily series, three multiple histories and one Treasury yield. Connector
identifiers come from `config.toml` and are not recorded here.

## Prior lessons read

None. ACME has no scored rows in the calls log.

## Brand palette

`#1F5C8B`, taken from the header colour published in the investor-relations
stylesheet. Contrast checks in the build log.

## Close

All eight stages ran. Three artefacts built, in `exports/`. Row added to the
calls log with review due 2027-01-15.
