# Export scripts

Shared, parameterised, and written once. Every run calls these; no run writes its own
exporter. The full account is [docs/07-exports.md](../docs/07-exports.md); this file is
the short version.

```bash
python build/build_workpapers.py "<run folder>"
python build/build_workbook.py "<run folder>"
python build/build_report.py "<run folder>" --brand "#RRGGBB" --brand-source "where the hex came from"
```

Each writes into `<run folder>/exports/` and prints the path. `-o` overrides it. On
Windows set `PYTHONIOENCODING=utf-8` first.

| File | What it does |
|---|---|
| `m2md.py` | Markdown to typed blocks, shared by both document builders. Holds `drop_plumbing` and the pattern it matches |
| `m2brand.py` | Brand palette with contrast checks applied: which colour may carry text, which may carry a chart mark, which is for large fills only |
| `m2config.py` | Configuration from `config.toml` and the environment |
| `build_workpapers.py` | Every agent's output in one Word file, in stage order, unedited |
| `build_workbook.py` | Fourteen sheets from `statements.csv` and `model.py` |
| `build_report.py` | The report PDF, with exhibits drawn from the model rather than retyped |

The report builder takes the rating, target and expected return from `decision.md`
front-matter, never from `report.md`, and keys its exhibits off the two-digit section
numbers in the report's headings.

Read two things after every PDF build: the sentences the plumbing strip removed, and
the contrast report. Both are printed for that purpose.
