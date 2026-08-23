# CLAUDE.md

Instructions for Claude Code working in this repository.

## What this is

An eight-stage, ten-agent equity research pipeline plus three export scripts. The
process is documented in `docs/`, start to end. Read
[docs/03-pipeline.md](docs/03-pipeline.md) before touching anything that runs a stage.

## Running the pipeline

Only on the trigger phrase `run a multi agent equity research report on <TICKER>`.
The skill in [skills/method-2/SKILL.md](skills/method-2/SKILL.md) carries it and
explains the spawning mechanics. A full run spawns ten agents and spends a daily
market-data quota, so do not start one because a request sounds like equity research.

## Rules that hold regardless of the task

**Three ratings only.** BUY, HOLD, SELL, on the bands in
[docs/05-output-schema.md](docs/05-output-schema.md). No fourth tier, no paired
labels. An invalid `rating` value is a failed run rather than a new rating.

**Nothing retypes a figure.** The rating and target live in `decision.md`
front-matter. The valuation lives in `model.py`. The workbook, the PDF, the company
index and the calls-log row read from those two. If you find yourself copying a number
between files, stop and read the schema.

**`decision.md` wins over `model.py` on the rating, target, expected return and
scenario probabilities.** Where the judge overrode the valuation agent, patch
`WEIGHTED` in `model.py` and rebuild. Never edit `decision.md` to match the model.

**No agent reads prior coverage of the ticker before the judge rules.** The comparison
is stage 7. Reading an existing call earlier turns the run into a confirmation of it.

**Only the market agent spends market-data calls**, from the connectors in
`config.toml`, in that order, sequentially. Connectors not in that list belong to
another task.

**A closed run is never edited.** A corrected view is a new run folder.

## Working on the export scripts

They live in `build/` and are shared: every run calls the same ones, so a fix reaches
every future run. Do not copy a builder into a run folder.

Check any change against the worked example, which is the only fixture in the
repository:

```bash
python build/build_workpapers.py example/Acme/runs/2026-01-15
```

```bash
python build/build_workbook.py example/Acme/runs/2026-01-15
```

```bash
python build/build_report.py example/Acme/runs/2026-01-15 --brand "#1F5C8B" --brand-source "investor relations stylesheet"
```

Expect twelve DOCX sections, fourteen workbook sheets and a six-page PDF. On Windows
set `PYTHONIOENCODING=utf-8` first.

Two outputs of the PDF build exist to be read rather than skipped: the list of
sentences the plumbing strip removed, and the contrast report behind every colour
decision. Narrow the pattern in `m2md.py` if the strip took a paragraph worth keeping.

## Keeping the run cheap

Cost inside an agent is roughly its context multiplied by its turn count, so the
lever is turns rather than sources. Two audited runs put re-read instructions and
briefs above half the total bill and everything reaching outside the machine below
half a percent.

- Shared work belongs in preflight, not in an agent. The filing index, the company
  facts file and the statement series are all resolved once, before stage 1.
- Agents append each section as they finish it. A stage killed mid-way then costs
  the remainder rather than the whole file.
- Before adding an instruction to a role prompt, remember it is re-read on every
  turn that agent takes. Length in a brief is charged dozens of times over.
- Reaching for a source is cheap. Rediscovering something preflight already found
  is not.

## Things that will waste a run

Fetching a second price. Every agent uses the one price resolved in preflight, or the
scenario table stops adding up.

Letting an agent rediscover a filing URL. Preflight resolves the CIK, the filing index
and the company facts file once and hands them over. A tool call inside an agent's
conversation re-sends everything before it, so a rediscovered URL is paid for again on
every later turn.

Calling SEC EDGAR without a User-Agent naming a person and an email. It returns 403 to
every such request. Fetch with Python and set the header.

Quoting a tritanopia figure from `m2brand`. The simulation is validated for protanopia
and deuteranopia only and raises on `kind='trit'` for that reason.

## Writing

Sentence-case headings. Plain verbs. Tables where a table helps and prose where it
does not. No filler about what something represents or underscores; state the fact and
stop.

Nothing in this repository is investment advice, and every report it builds says so.
