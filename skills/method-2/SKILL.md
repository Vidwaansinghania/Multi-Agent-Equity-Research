---
name: method-2
description: >
  Runs the Method 2 multi-agent equity research pipeline — ten specialist agents
  (four analysts, valuation, bull, bear, judge, risk gate, report writer) producing
  a typed BUY / HOLD / SELL decision record plus three deliverables: a workpapers
  Word file, a model workbook and an institutional report PDF, all under
  research/<Company>/runs/.
  OPT-IN ONLY, EXACT PHRASE ONLY: use this skill only when the user writes
  "run a multi agent equity research report on <TICKER>" (or invokes /method-2).
  Never trigger it on any other equity-research request, however similar. A request
  to research a company, value a business, write a thesis, check a rating, or give a
  view on a stock is NOT this skill. A full run spawns ten agents and consumes a
  shared daily market-data quota, so a wrong trigger has real cost. When in doubt,
  do the work normally and mention that the phrase exists.
---

# Method 2 — multi-agent equity research

## Check the trigger before anything else

Proceed only if the user's message contains the phrase `run a multi agent equity
research report on` followed by a ticker or company name, or they invoked
`/method-2` directly. Small variations in wording are fine: capitalisation,
"multi-agent" hyphenated, a company name instead of a ticker.

If the request is merely adjacent — "research Costco", "what do you think of NVDA",
"value this company", "run the equity process on X" — do not start a run. Do the work
the normal way and, in one sentence, tell them the trigger phrase exists if they
wanted the fan-out.

If they name several tickers, run them one at a time and say so. Ten agents per
ticker, and the market-data cap is a daily ceiling shared across every run rather
than an allowance to spend.

## Then read the process

Everything about the run lives in the docs, not in this file. Read in this order:

1. `docs/03-pipeline.md` — the eight stages, what each agent receives, the failure modes
2. `docs/04-role-prompts.md` — the seven prompts and the shared preamble
3. `docs/05-output-schema.md` — the typed contracts for `decision.md` and `model.py`
4. `docs/06-run-anatomy.md` — where the files go
5. `docs/07-exports.md` — how the three artefacts get built
6. `docs/10-quality-standards.md` — the bar every stage is held to
7. `config.toml` — paths, connectors, currency, benchmark, models

Then execute the stages in order. This file adds only the mechanics of spawning.

## Spawning mechanics

Pass the role prompt from `docs/04-role-prompts.md` as the agent's prompt, with the
shared preamble prepended and the bracketed values substituted from preflight and
from `config.toml`.

| Stage | Calls | Model | Concurrency |
|---|---|---|---|
| 1 · Evidence | 4 | `models.analysts` | all four agent calls in one message |
| 2 · Base case | 1 | `models.valuation` | — |
| 3 · Debate | 2 | `models.debate` for both | both agent calls in one message |
| 4 · Judgment | 1 | `models.judge` | — |
| 5 · Risk gate | 1 | `models.risk` | — |
| 6 · Report | 1 | `models.report` | — |

Bull and bear take the same model. If one changes, both change: an asymmetric debate
is biased in a way the transcript never shows.

Run the agents in the foreground so the stages stay ordered; each stage depends on the
files the previous one wrote. Within a stage, put every agent call in a single message
so they genuinely run at once.

Tell each agent to write its own file into the run folder and return only a short
summary. Do not transcribe an agent's output yourself.

## Deliverables

Stage 7 is the orchestrator's. Build all three with the shared scripts, from the run
folder:

```bash
python build/build_workpapers.py "<run folder>"
```

Then `build_workbook.py` and `build_report.py` the same way, the last one taking
`--brand "#RRGGBB"` and `--brand-source`. On Windows set `PYTHONIOENCODING=utf-8`
first. Read the dropped-sentence list and the palette report the PDF build prints;
both exist to be read, not skipped.

## Hard constraints

- **Every output lands in `<research_root>/<Company>/runs/<YYYY-MM-DD>/`.** Never
  write into a folder holding prior coverage from another process.
- **Every company gets a node**, named by common name, holding one folder per run. A
  closed run is never edited; a corrected view is a new run.
- **No agent reads prior coverage of the ticker before the judge rules.** The
  comparison is stage 7, after the rating is committed.
- **Only the market agent touches the market-data connectors**, capped at the
  configured total, a ceiling and not a target, used in the configured order,
  sequentially, at least 1.1 seconds apart, with a failed call still counting. The
  tools carry an identifier and no name, so hand the market agent the mapping from
  `config.toml` verbatim and tell it not to infer one. Any connector not in that list
  is off limits, including ones that appear in the session.
- **Three ratings only.** BUY, HOLD, SELL, mapped from the probability-weighted
  twelve-month total return onto the bands in `docs/05-output-schema.md`. Any other
  value is a failed run.
- **The quality bar is `docs/10-quality-standards.md`**: ten years of statements, a
  Porter's five forces table with an evidence column, a football field, five
  structured risks, a dated catalyst calendar and the four disclosure blocks are all
  required rather than optional.
- **Read the holdings file in preflight** and pass the position to the judge and the
  risk gate. The ownership block states the position as fact.
- **A run isn't done until** the three artefacts are built and open, copied from the
  run's `exports/` into `<research_root>/reports/` under the filenames the builder
  wrote, the company index is updated, and the row is in the calls log with a review
  date twelve months out.

## Reporting back

Nobody watches a run, so the final message carries everything: the rating, the target,
the expected return, how marginal it is and which assumption flips it, which stage
carried the decision, how it differs from any prior coverage, and what the risk gate
said about position size and currency drag. Link the run folder and the decision
record, and give the paths to all three deliverables.
