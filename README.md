# Multi-Agent-Equity-Research

A repeatable equity research process run by ten AI agents in eight stages, ending
in a typed BUY / HOLD / SELL record, three built artefacts, and a row in a log
that gets scored against the benchmark twelve months later.

Four analysts gather evidence independently. A valuation agent builds a base case
and is forbidden from stating a call. A bull and a bear attack that base case on
the same model, at the same time, neither seeing the other. A judge reads the
evidence alongside both attacks and issues the rating. A risk gate checks what the
call does to an actual portfolio. A report writer publishes. The orchestrator, a
human running Claude Code, sequences the stages and builds the deliverables, and
does no analysis of its own.

The point of the design is not that ten agents beat one. That is an open question
this repository is set up to answer rather than assume. The point is that every
call it produces is dated, typed, attributed to the stage that carried it, and
scored later against what the market actually did.

## What a run produces

| Artefact | What it is |
|---|---|
| Report PDF | The institutional report, in the company's brand colours, twelve to eighteen pages |
| Model XLSX | Fourteen sheets: ten-year statements, common-size, ratios, DCF, scenarios, sensitivity, comps, football field, sources |
| Workpapers DOCX | Every agent's output in stage order, unedited. The audit trail |

No figure is retyped between the three. The workbook and the PDF both import the
run's `model.py`, and the rating and target come from `decision.md` front-matter
and nowhere else.

## Quickstart

```bash
git clone <this repo> && cd multi-agent-equity-research
pip install -r requirements.txt
cp config.example.toml config.toml   # then set your name, email and paths
```

Build the three artefacts from the worked example, which uses an invented company
so nothing in it is a view on a real security:

```bash
python build/build_workpapers.py example/Acme/runs/2026-01-15
```

```bash
python build/build_workbook.py example/Acme/runs/2026-01-15
```

```bash
python build/build_report.py example/Acme/runs/2026-01-15 --brand "#1F5C8B" --brand-source "investor relations stylesheet"
```

To run the pipeline on a real ticker, open the repository in Claude Code and say:

```
run a multi agent equity research report on MSFT
```

The skill in [skills/method-2/SKILL.md](skills/method-2/SKILL.md) carries the
trigger. Copy that folder into `.claude/skills/` to have Claude Code pick it up.

## Tuned for token cost

Ten agents reading a decade of filings is expensive, and the expense is not where
it looks. Two full runs were audited line by line. Both found the same thing: what
an agent carries on every turn costs far more than what it reaches out for once.

On the more recent audit, re-read instructions and role briefs came to 55% of the
whole bill and reading files and running scripts to 23%, while every web search,
every page fetch and every market-data call together came to under half a percent.
Cost inside an agent scales with its context multiplied by its turn count, so the
lever is turns, not sources.

Three things follow, and all three are in the process rather than in advice:

- **Shared work happens once, in preflight.** The CIK, the filing index and the
  company facts file are resolved before any agent starts, and `build/m2facts.py`
  turns that file into the run's ten-year statement series. The fundamentals agent
  checks and extends those rows instead of rebuilding them, which on the audited
  run was a tenth of the entire budget spent across 126 turns picking through one
  JSON file.
- **Agents append as they go.** Every brief tells its agent to write each section
  as it finishes rather than composing the whole file and saving at the end. When
  three stages of the audited run hit a rate limit, the two holding their work in
  memory were re-run from zero and the one that had been appending resumed.
- **Beta is measured in preflight, not argued in the debate.** One regression up
  front is cheaper than four agents and a judge reasoning about a number none of
  them measured, and it produces a better call as well as a shorter run.

None of this trades away coverage. The four analysts still work independently, the
debate still runs both sides on the same model, and the judge still reads the
evidence rather than the transcript.

## The eight stages

| Stage | Agents | Model | Parallel | Writes |
|---|---|---|---|---|
| 0 · Preflight | orchestrator | — | — | `run.md`, `companyfacts.json` |
| 1 · Evidence | 4 analysts | Sonnet | all four at once | `analyst-*.md`, `statements.csv` |
| 2 · Base case | valuation | Opus | — | `valuation.md`, `model.py` |
| 3 · Debate | bull, bear | Opus, same both | both at once | `bull.md`, `bear.md` |
| 4 · Judgment | judge | Opus | — | `decision.md` |
| 5 · Risk gate | risk | Opus | — | `risk.md` |
| 6 · Report | writer | Opus | — | `report.md` |
| 7 · Close | orchestrator | — | — | `exports/` ×3, `comparison.md`, calls-log row |

## Documentation

| Read | For |
|---|---|
| [docs/01-overview.md](docs/01-overview.md) | What the process is, the design decisions, and how it differs from TradingAgents |
| [docs/02-setup.md](docs/02-setup.md) | Install, configuration, market data, SEC EDGAR access |
| [docs/03-pipeline.md](docs/03-pipeline.md) | The eight stages in full, with what each agent receives |
| [docs/04-role-prompts.md](docs/04-role-prompts.md) | The seven prompts and the shared preamble, ready to paste |
| [docs/05-output-schema.md](docs/05-output-schema.md) | The typed contracts for `decision.md` and `model.py`, and the rating bands |
| [docs/06-run-anatomy.md](docs/06-run-anatomy.md) | Where every file goes and what it is for |
| [docs/07-exports.md](docs/07-exports.md) | The three builders, what they need, how they degrade |
| [docs/08-calls-log.md](docs/08-calls-log.md) | Scoring calls against alpha, and how a run reads its own history |
| [docs/09-failure-modes.md](docs/09-failure-modes.md) | Symptoms, causes, fixes |
| [docs/10-quality-standards.md](docs/10-quality-standards.md) | The checklist every stage is held to |

## Repository layout

```
build/          the three export scripts and their two shared modules
docs/           the process, start to end
skills/         the Claude Code skill that carries the trigger phrase
templates/      empty run.md, decision.md, model.py, statements.csv, calls log
example/Acme/   a complete worked run on an invented company, with built exports
config.toml     yours, gitignored; copy config.example.toml
```

Run folders live under `research/<Company>/runs/<YYYY-MM-DD>/` by default, which
is gitignored so real research stays out of the repository unless you choose
otherwise. Each closed run's three artefacts are also copied to `research/reports/`,
so finished reports sit in one place.

## Three ratings, and what that costs

BUY above +15%, HOLD between −15% and +15%, SELL below −15%, on the
probability-weighted twelve-month total return. Any other value in the `rating`
field fails the run rather than becoming a fourth tier. Where a call sits within
five points of a band edge it is marked marginal and has to name the single
assumption that would move it.

The framework this borrows its role decomposition from parses its rating out of
prose with a regular expression and defaults to Hold when the pattern misses,
which manufactures a call no agent made. Typed fields with a fixed set of allowed
values turn that into a visible failure.

## Educational and research use only

Nothing this process produces is investment advice. Every report it builds carries
that statement, and so does every decision record.

## Credit

The role decomposition comes from
[TradingAgents](https://github.com/TauricResearch/TradingAgents) (Tauric
Research, Apache-2.0). Five things here are deliberately different, and
[docs/01-overview.md](docs/01-overview.md) sets out each one and why.

MIT licensed. See [LICENSE](LICENSE).
