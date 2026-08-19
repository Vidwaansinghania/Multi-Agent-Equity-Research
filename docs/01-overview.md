# 01 · Overview

Method 2 is a second, independent way of producing an equity call. A single
analyst working alone is the first way, and the two are meant to cover the same
tickers so they can be compared on the same names. That comparison is the reason
the process exists in this form.

Ten agent calls in eight stages, driven by a human running Claude Code as the
orchestrator. The orchestrator sequences the stages, does the preflight, builds
the deliverables, and performs no analysis.

## What each stage is for

Stage 1 is evidence. Four analysts work at the same time and none of them sees
another's output, which is deliberate: four correlated summaries of one filing add
nothing. Fundamentals reads ten fiscal years out of the filings. Market
establishes what the price already implies. News finds what changed since the last
10-K. Industry compares the economics to the companies trying to take them.

Stage 2 is the only stage that produces numbers a judge can rule on. The valuation
agent builds a discounted cash flow, a comparables cross-check, three scenarios
with explicit probabilities, and a sensitivity grid, and it is forbidden from
stating a rating. Its output is the object the next two agents attack.

Stage 3 is the debate. A bull and a bear each attack the stated base case, by
naming assumptions at their value in the memo and computing what a different value
does to the weighted target. They run at the same time on the same model, so
neither can answer the other and neither has a model advantage.

Stage 4 is judgment. The judge reads the four analyst files and the valuation memo
alongside both attacks, maps the probability-weighted twelve-month total return
onto three bands, and takes the answer. It also records which stage carried the
decision and how close the call sits to a band edge.

Stage 5 is a portfolio check rather than a fourth opinion: concentration,
correlation with what is already held, the currency round trip against the
expected return, and entry discipline as a price table. It cannot change the
rating, and a disagreement stands in the record.

Stage 6 writes the report. It inherits the rating, target and probabilities from
the decision record and reproduces them exactly. Its own work is the three
sections nobody else produced: the company overview, the investment thesis with
its variant perception, and five structured risks.

Stage 7 builds the three artefacts, writes the comparison against any prior
coverage, and logs the call with a review date twelve months out.

## The design decisions that matter

**The judge reads the evidence, not only the argument.** This is the single
biggest departure from the framework the roles come from, where the judge sees
only the debate transcript and therefore rules on whoever argued better.

**Bull and bear run on the same model.** An asymmetric debate is biased in a way
that never appears in the transcript. If the model changes for one, it changes for
both.

**One agent owns market data.** Four parallel agents each reaching for quotes
would exhaust a daily quota in a single stage. Everyone else works from filings
and free sources.

**Everything typed that anything downstream reads.** The rating and target live in
`decision.md` front-matter and nowhere else. The valuation lives in `model.py` and
nowhere else. The workbook, the PDF, the company index and the calls-log row all
read from those two files and keep no copy.

**The exporters are shared.** No run writes its own builder. A fix to
`build/build_report.py` reaches every future run instead of one folder.

**Front-loaded discovery.** Preflight resolves the CIK, the filing index and the
XBRL company facts file once, before any agent is spawned. A tool call inside an
agent's conversation re-sends everything before it, so an agent left to rediscover
a URL pays for that search again on every later turn. A token audit of the first
full ten-agent run found this the largest single driver of cost: two analysts made
sixty and ninety tool calls, most of them finding URLs rather than reading
filings, and evidence gathering alone ran to more than a third of the run.

## How this differs from TradingAgents

Built after reading [TradingAgents](https://github.com/TauricResearch/TradingAgents)
(Tauric Research, Apache-2.0). The role decomposition is theirs. Five things are
deliberately different.

| Their design | Method 2 | Why |
|---|---|---|
| Five-tier rating parsed from prose with a regex that defaults to Hold on failure | Three tiers in a typed field; an invalid value fails the run | A parsing failure should surface rather than manufacture a call no agent made |
| The judge reads only the debate transcript | The judge reads the analyst files and the valuation memo alongside both attacks | Otherwise the more persuasive agent wins regardless of the evidence |
| Bull and bear argue in the abstract | Both attack a stated base case with explicit numbers | An argument against a number is checkable; an argument for optimism is not |
| Social-media sentiment as a co-equal analyst | Absent; one section of the news file at most | Noise on a twelve-month probability-weighted call |
| Three risk personas argue about temperament | One risk gate that computes concentration, correlation and currency drag | Temperament is not risk management |

Their strongest idea is the one most worth keeping: an append-only decision log
with post-hoc reflections scored against alpha. That is
[docs/08-calls-log.md](08-calls-log.md), and it stays valuable even if the fan-out
turns out to add nothing.

## What would make this worth continuing

Three things, in order, and none of them is available in the first month.

Runs on tickers already covered by a single-analyst process, to see whether the
ratings differ at all. Then the `decided_by` field across a dozen runs, to see
which stage is doing the work: if it is always the valuation agent, the debate is
decoration and can be cut. Then scored rows in the calls log, which is the only
evidence either method is any good.

Until the third one exists, treat every output as an interesting second opinion.
