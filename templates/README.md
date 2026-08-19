# Templates

Copy these into a new run folder and fill them in. Year columns and fiscal labels
change with the company; the ones here are placeholders.

| File | Written in | Contract |
|---|---|---|
| `run.md` | stage 0, by the orchestrator | — |
| `statements.csv` | stage 1, by the fundamentals agent | [docs/05-output-schema.md](../docs/05-output-schema.md) |
| `model.py` | stage 2, by the valuation agent | [docs/05-output-schema.md](../docs/05-output-schema.md) |
| `decision.md` | stage 4, by the judge | [docs/05-output-schema.md](../docs/05-output-schema.md) |
| `company-index.md` | stage 7, by the orchestrator | — |
| `calls-log.md` | once, then appended per run | [docs/08-calls-log.md](../docs/08-calls-log.md) |

The other run files — the four analyst memos, `valuation.md`, `bull.md`, `bear.md`,
`risk.md`, `report.md` and `comparison.md` — have no template. Their prompts specify
what they contain, and a template would only encourage filling in headings rather
than answering the brief. Worked versions of all of them are in
[example/Acme](../example/Acme/runs/2026-01-15).
