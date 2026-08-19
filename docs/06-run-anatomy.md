# 06 · Run anatomy

Every company gets its own node. A node holds one folder per run, and a run is never
edited after it closes.

## The tree

```
research/<Company>/
├── _index.md                          # snapshot, run history, links to newest exports
└── runs/<YYYY-MM-DD>/
    ├── run.md                         # stage 0 — preflight
    ├── companyfacts.json              # stage 0 — cached XBRL company facts
    ├── analyst-fundamentals.md        # stage 1
    ├── analyst-market.md
    ├── analyst-news.md
    ├── analyst-industry.md
    ├── statements.csv                 # stage 1 — ten fiscal years, machine-readable
    ├── valuation.md                   # stage 2
    ├── model.py                       # stage 2 — the typed numbers
    ├── bull.md                        # stage 3
    ├── bear.md                        # stage 3
    ├── decision.md                    # stage 4 — the typed record
    ├── risk.md                        # stage 5
    ├── report.md                      # stage 6 — the institutional report
    ├── comparison.md                  # stage 7 — against prior coverage
    └── exports/
        ├── <TICKER>_Method2_Report_<YYYY-MM-DD>.pdf
        ├── <TICKER>_Method2_Workpapers_<YYYY-MM-DD>.docx
        └── <TICKER>_Method2_Model_<YYYY-MM-DD>.xlsx
```

`research/` is the default and comes from `paths.research_root`. It is gitignored,
so real research stays out of the repository unless you decide otherwise.

The folder name is the company's common name, `Home Depot` rather than `HD`, so a
node sorts next to any prior coverage of the same company. The run folder is the
date alone, because the ticker is already the node.

A second run on the same day gets a `-b` suffix rather than overwriting the first.
Two runs that disagree measure the stability of the process, and both are worth
keeping.

## What each file is for

| File | Written by | Why it exists |
|---|---|---|
| `run.md` | orchestrator | Ticker, models, holdings snapshot, reference price, market-data budget, the CIK and the resolved filing URLs. The one place a later reader learns what the run knew at the time |
| `companyfacts.json` | orchestrator | Fetched once in preflight so no analyst has to call the endpoint or rediscover it. Read directly by the fundamentals agent |
| `analyst-*.md` | four analysts | The evidence. Cannot be reconstructed once prices and consensus have moved |
| `statements.csv` | fundamentals agent | Ten fiscal years of income statement, balance sheet and cash flow, one row per line item. Feeds the workbook and the ten-year exhibits without anyone retyping a figure |
| `valuation.md` | valuation agent | The base case as prose, with every assumption defended |
| `model.py` | valuation agent | The same numbers as Python literals. The workbook and the PDF both import this, so a corrected assumption propagates to both artefacts on rebuild |
| `bull.md`, `bear.md` | debate agents | Both attacks, including the one the judge rejects. A rejected argument that turns out right is the most valuable thing in the archive |
| `decision.md` | judge | The typed record. The only place the rating and target live |
| `risk.md` | risk gate | Position, concentration, correlation, currency drag, entry discipline |
| `report.md` | report writer | The institutional report. Source for the PDF |
| `comparison.md` | orchestrator | This run against prior coverage of the same ticker. Written last, and the only point in a run where prior coverage may be opened |
| `exports/` | orchestrator | The three deliverables. Built by the shared scripts in `build/`; nothing here is written by hand |

A folder missing `decision.md` is an abandoned run. Leave it in place with a line in
`run.md` saying where it stopped, because a stage that fails repeatedly is a finding
about the pipeline.

## The company index

One page per company, carrying the snapshot fields in its own front-matter:
`ticker`, `company`, `latest_call`, `latest_target`, `latest_run`. The body holds a
run-history table, the divergence from any prior coverage, and links to the newest
three exports. [templates/company-index.md](../templates/company-index.md) is the
shape.

The snapshot fields are copied from the newest run's `decision.md` front-matter and
never computed independently.

## Retention

Keep everything. Nothing in a closed run gets deleted or revised, and a corrected
view is a new run rather than an edit to an old one. That includes exports: a
superseded PDF stays where it is, because the calls log points at the version that
was live when the call was struck.
