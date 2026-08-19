# 03 · Pipeline

Ten agent calls in eight stages. The orchestrator is whoever is running Claude
Code. It sequences the stages, writes the preflight and the close, and runs the
export scripts. It does no analysis of its own.

## Shape of a run

| Stage | Agents | Model | Parallel | Writes |
|---|---|---|---|---|
| 0 · Preflight | orchestrator only | — | — | `run.md`, `companyfacts.json` |
| 1 · Evidence | 4 analysts | Sonnet | yes, all four at once | `analyst-fundamentals.md`, `analyst-market.md`, `analyst-news.md`, `analyst-industry.md`, `statements.csv` |
| 2 · Base case | 1 valuation agent | Opus | — | `valuation.md`, `model.py` |
| 3 · Debate | bull + bear | Opus, same model both | yes, both at once | `bull.md`, `bear.md` |
| 4 · Judgment | 1 judge | Opus | — | `decision.md` |
| 5 · Risk gate | 1 risk agent | Opus | — | `risk.md` |
| 6 · Report | 1 report writer | Opus | — | `report.md` |
| 7 · Deliverables and close | orchestrator only | — | — | `exports/` ×3, `comparison.md`, company index, calls-log row |

Four agents run concurrently in stage 1 and two more in stage 3. Stage 1 takes the
longest. Nothing here runs against a clock.

Splitting the judge from the report writer keeps the ruling short and auditable
and lets the writing be long. The judge rules; the writer writes.

## What the run has to produce

| Artefact | Built from |
|---|---|
| `<TICKER>_Method2_Workpapers_<DATE>.docx` | the ten markdown files, verbatim, in stage order |
| `<TICKER>_Method2_Model_<DATE>.xlsx` | `statements.csv` and `model.py` |
| `<TICKER>_Method2_Report_<DATE>.pdf` | `report.md` and `model.py`, with the rating from `decision.md` |

Nothing retypes a figure. The workbook and the PDF both import `model.py`, so a
corrected assumption propagates to both on rebuild, and the rating and target come
from `decision.md` front-matter and nowhere else.

## Section ownership

The report covers nine numbered sections and every one has an owner.

| Section | Producer | Stage |
|---|---|---|
| 01 Company overview — business, segments, revenue mix | fundamentals analyst, written up by the report writer | 1, 6 |
| 02 Investment thesis and variant perception | report writer, from the analyst files and the debate | 6 |
| 03 Industry and competitive positioning, Porter's five forces | industry analyst | 1 |
| 04 Financial analysis, ten fiscal years, common-size, ratio history | fundamentals analyst | 1 |
| 05 Valuation, DCF, comps, sensitivity, football field | valuation analyst, chart data from the market analyst | 1, 2 |
| 06 Risks — five specific risks with impact, probability, trigger, mitigation | report writer, from `bear.md`, `analyst-news.md`, `analyst-industry.md` | 6 |
| 07 Catalysts and ESG, dated | news analyst | 1 |
| 08 Bull, base, bear and recommendation | valuation, debate, judge | 2–4 |
| 09 Appendices, four disclosure blocks | judge for ownership, report writer for the rest | 4, 6 |

The football field carries five rows: the DCF range, the comps range, the
fifty-two-week range, the street target range and the scenario range, all against
the reference price, with the probability-weighted target as a vertical marker. The
extra rows cost nothing because the market analyst already gathers the range and
the street targets.

## Stage 0 — preflight

Do all of this before spawning anything. Every item is a failure that costs a whole
run if it surfaces in stage 3 instead.

- [ ] Resolve the ticker and exchange, including any suffix the quote needs.
- [ ] Find or create the node at `<research_root>/<Company>/`, using the company's
      common name, and create `runs/<YYYY-MM-DD>/` inside it. A second run the same
      day takes a `-b` suffix.
- [ ] Write `run.md` with the ticker, the date, the models, the reference price and
      the reason for the run. [templates/run.md](../templates/run.md) is the shape.
- [ ] Read the holdings file and record the position verbatim into `run.md`:
      company, share count, share of portfolio, snapshot date. If there is no
      position, write that.
- [ ] Get one price and its as-of date. Every downstream agent uses this price.
      Agents fetching their own produces a scenario table that does not add up.
- [ ] Resolve the CIK and fetch the filing index once, at
      `data.sec.gov/submissions/CIK##########.json`. Record the CIK and, from the
      index, the accession number and primary document URL for the most recent
      10-K and the last four 8-Ks. Hand these straight to the fundamentals and news
      agents in their prompts.
- [ ] Fetch `data.sec.gov/api/xbrl/companyfacts/CIK##########.json` once and save
      it into the run folder as `companyfacts.json`. The fundamentals agent reads
      the file rather than calling the endpoint.
- [ ] Confirm the market-data headroom. Record the connector table in `run.md` and
      pass it to the market agent verbatim, because the tools carry an identifier
      and no name. If an earlier run today already spent some of the cap, say what
      is left.
- [ ] Read the scored rows in the calls log for this ticker, up to five, plus the
      three most recent scored rows on any ticker. These go to the judge in stage 4
      labelled as prior lessons, and to nobody else.
- [ ] Confirm no agent has been handed prior coverage of this ticker. The anchoring
      rule is not optional: reading an existing call first collapses the exercise
      into agreement with it.

## Stage 1 — evidence, four agents in parallel

Spawn all four in one message so they run concurrently. Each gets the prompt from
[docs/04-role-prompts.md](04-role-prompts.md), the ticker, the price and as-of date
from preflight, and its own tool budget. None sees another's output.

| Agent | Owns | Tools | Hard limits |
|---|---|---|---|
| Fundamentals | Ten fiscal years of statements, common-size, ratio history, quality of earnings, incremental returns on capital, segments | `companyfacts.json` from preflight; Python against EDGAR for the 10-K and 8-Ks at the resolved URLs | No market-data connectors. Cite by filing and section. Writes `statements.csv` as well as its memo |
| Market | Price history, multiples against their own history, consensus, fifty-two-week range, street targets | The configured connectors, in order; stockanalysis.com; FRED CSV | The only agent allowed on the connectors. The cap is a ceiling. Sequential, at least 1.1 seconds apart, a failed call still counting |
| News | Filings-adjacent events, 8-K exhibits, guidance changes, litigation, dated catalyst calendar, ESG | The resolved 10-K and 8-K URLs; Python against EDGAR beyond those; web fetch and search | No social-media sentiment. No price moves; the market agent owns price |
| Industry | Competitive position, Porter's five forces, unit economics against named peers, structural change | Web fetch and search, EDGAR for peer filings | Name peers explicitly. No vague claims about "the sector" |

Ten years of statements comes out of `companyfacts.json`. Segment detail and
guidance are not in it and come from the 10-K and the 8-K exhibits, whose URLs
preflight already resolved.

Sentiment is deliberately absent. Treating social-media sentiment as a first-class
input is defensible for a swing trade and noise on a probability-weighted
twelve-month call. If a sentiment read is ever wanted it goes to the news agent as
one section, never as a fifth vote.

## Stage 2 — base case

One agent. Receives all four analyst files and `statements.csv`. Builds the
valuation and the three scenarios, and this is the only stage that produces numbers
the judge can rule on.

Requirements:

- Discounted cash flow as primary, comparables as secondary, both built off the
  ten-year history rather than three years. How the DCF is built is fixed rather
  than left to the agent: free cash flow to the firm, ten explicit years, mid-year
  discounting with a stub for the part-year, terminal value by perpetuity growth
  with reinvestment at growth over return on new capital, terminal value reported
  as a share of enterprise value, and a reverse DCF as a check. Two runs that
  discount differently are not comparable, and comparing runs is the point.
- Bull, base and bear scenarios with explicit probabilities summing to 1, and a
  probability-weighted twelve-month target.
- Real costs charged, including share-based compensation.
- A financial estimates table: three years actual, two estimated, on revenue,
  growth, gross margin, operating margin, EBITDA, net income, EPS and free cash
  flow.
- A sensitivity grid on the two assumptions that move the target most.
- The football-field inputs: the DCF range, the comps-implied range, the scenario
  range.
- Every input traceable to a stage 1 file. Where two analysts conflict, say so and
  say which was used.

It writes twice: `valuation.md` for the reasoning and `model.py` for the numbers,
in the format [docs/05-output-schema.md](05-output-schema.md) fixes. The output is
a memo, not a rating. Stating a call here would anchor the two agents who attack it
next.

## Stage 3 — debate, two agents in parallel

Both receive the four analyst files and the valuation memo. Neither sees the other,
because they run at the same time. Neither states a rating.

The bull attacks the base case for being too conservative, the bear for being too
generous. Both name specific assumptions by their value in the memo, cite evidence
from the analyst files, compute what their version does to the weighted target, and
say what evidence would change their mind. A rhetorical performance with no
falsifiable claim in it is a failed stage and gets re-run.

Both run on the same model. Asymmetric models produce an asymmetric debate and the
asymmetry never shows up in the transcript.

## Stage 4 — judgment

One agent. Receives the four analyst files, the valuation memo, both attacks, and
the prior lessons pulled in preflight. Reading the evidence rather than only the
debate is the fix for the flaw in the original design.

Its output is `decision.md`, conforming to the schema exactly: typed front-matter,
then the prose sections. The rating comes from mapping the probability-weighted
twelve-month total return onto the bands and taking the answer even when it is
uncomfortable.

The judge also does two things the framework's judge never does. It attributes,
naming which analyst finding or which side of the debate carried the decision,
which is what makes per-stage attribution possible later. And it states
marginality: how close the call is to a band edge, and which single assumption
flips it.

If the judge sets a target that differs from the valuation agent's weighted target,
it says so and says why. The orchestrator then patches `model.py` to match
`decision.md`, never the other way round.

## Stage 5 — risk gate

One agent. A portfolio check, not a fourth opinion. It receives the decision record
and the holdings snapshot, and answers concretely:

- The existing position, as a share of the portfolio and of the equity sleeve.
- What the recommended action does to single-name concentration.
- What this name correlates with in the existing book, named holding by holding.
- The round-trip currency cost. Where the security trades in a currency the account
  does not hold, conversion is charged in both directions at the configured spread.
  On a call with an expected return inside the HOLD band that cost can exceed the
  entire edge, and the risk agent has to say so when it does.
- Entry discipline as a price table.

The risk agent may not change the rating. If it thinks the rating is wrong it says
so in `risk.md` and the disagreement stands in the record.

## Stage 6 — report

One agent. Receives everything: four analyst files, `statements.csv`, the valuation
memo, both attacks, the decision record and the risk file. It writes `report.md` in
the nine-section order above.

It writes, it does not decide. The rating, target, expected return and scenario
probabilities are inherited from `decision.md` front-matter and reproduced exactly.
A report writer that recomputes a number has broken the one rule that keeps the
three artefacts consistent. One that finds an arithmetic error names it at the end
of its file and leaves the published figures alone, because the decision record is
what gets scored in twelve months.

## Stage 7 — deliverables and close

Orchestrator only, no agents.

- [ ] Resolve the company's brand palette and record the hex values and their
      source in `run.md`. Sourcing order: published CSS design tokens, then a brand
      book or investor-relations template, then the logo sampled for dominant hues.
- [ ] Build the three artefacts with the scripts in `build/`. Verify each one opens
      and that the rating and target in the PDF match `decision.md`.
- [ ] Check that no line naming a script, a `.py` file or a rebuild instruction
      reached the PDF or the DOCX. The exporter strips by sentence rather than by
      paragraph and prints every sentence it removed; read all of them, because an
      over-broad pattern can take a paragraph worth keeping.
- [ ] Write `comparison.md`: this rating and target against any prior coverage of
      the same ticker, and where the two processes diverged. This is the first point
      in the run where prior coverage may be opened.
- [ ] Update the company index, with snapshot fields copied from `decision.md`
      front-matter, a row in the run table, and the export links.
- [ ] Add the row to the calls log with status `pending` and the review date twelve
      months out.
- [ ] Report back with everything: the rating, the target, how marginal, the
      flipping assumption, the divergence from prior coverage, what the risk gate
      said, and the paths to the three artefacts. Everything in one message, because
      nobody watches a run.

## Costs to respect

A full run is ten agent calls and the analyst stage is the long one.

Ten years of statements comes from the XBRL company facts endpoint in one request
and costs no market-data quota. Preflight resolving the CIK, the filing index and
the company facts file once is the single largest saving available: a tool call
inside an agent's conversation re-sends everything before it, so an agent left to
rediscover a URL pays for that search again on every later turn.

Market-data calls are a daily ceiling shared across every run, not an allowance to
spend. A run that answers its market questions in eight calls has done it right.

Failure modes and their fixes are in
[docs/09-failure-modes.md](09-failure-modes.md).
