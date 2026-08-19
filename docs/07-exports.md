# 07 · Exports

Three builders, shared and parameterised. Every run calls these; no run writes its
own exporter, so a fix reaches every future run instead of one folder.

Each takes the run folder as its one positional argument. On Windows set
`PYTHONIOENCODING=utf-8` first, or a minus sign in the console output raises a
`UnicodeEncodeError` on the default code page.

```bash
python build/build_workpapers.py "research/<Company>/runs/<DATE>"
```

```bash
python build/build_workbook.py "research/<Company>/runs/<DATE>"
```

```bash
python build/build_report.py "research/<Company>/runs/<DATE>" --brand "#1F5C8B" --brand-source "investor relations stylesheet"
```

Each writes into `<run folder>/exports/` and prints the path. `-o` overrides the
output path.

## The files

| File | What it does |
|---|---|
| `m2md.py` | Markdown to typed blocks, shared by both document builders. Also holds `drop_plumbing`, which removes sentences naming local plumbing and records every one it removed |
| `m2brand.py` | Brand palette with the contrast checks already applied: which colour may carry text, which may carry a chart mark, which is for large fills only |
| `m2config.py` | Configuration from `config.toml` and the environment |
| `build_workpapers.py` | Every agent's output in one Word file, in stage order, unedited |
| `build_workbook.py` | The numbers, from `statements.csv` and `model.py`, one sheet per thing worth checking |
| `build_report.py` | The report PDF, in the company's colours, with the exhibits drawn from the model rather than retyped |

## What each builder needs

| Builder | Requires | Degrades to |
|---|---|---|
| Workpapers | nothing beyond the markdown files that exist | a document with a line naming the absent stages |
| Workbook | `statements.csv`, `model.py` | skips the sheets whose input is missing and says so on the README sheet |
| Report | `report.md`, `decision.md` | exits with a message when `report.md` is absent; drops individual exhibits when `model.py` or `statements.csv` are |

The workbook builds fourteen sheets: README, income statement, balance sheet, cash
flow, common size, ratios, segments, estimates, DCF, scenarios, sensitivity, comps,
football field, sources.

The report builder reads the rating, target and expected return from `decision.md`
front-matter, never from `report.md`. That is deliberate: the judge rules and the
writer writes, so where the two disagree the record wins. It also keys its four
exhibits off the two-digit section numbers in `report.md` — the ten-year history
chart onto section 04, the football field and sensitivity table onto 05, the
scenario table onto 08 — so a report whose headings drop those numbers builds
without exhibits.

## Two things to read after every build

**The dropped sentences.** `build_report.py` prints every sentence `drop_plumbing`
removed. Read all of them. The strip works by sentence rather than by paragraph
because a plumbing clause often sits at the end of a paragraph worth keeping, and an
over-broad pattern can take a paragraph you wanted. The pattern is at the top of
`m2md.py`.

**The palette report.** It prints the contrast ratio behind every decision it made.
White on a saturated brand colour does not behave predictably: it fails on some
blues at 3.56:1 and passes on a saturated red. Where a colour cannot carry text
without losing its identity, it stays on the chrome and the charts run on the
validated series.

## No tritanopia check

The Viénot 1999 inverse this family of scripts uses is validated for protanopia and
deuteranopia only. Pushed through the tritan cone it saturates every input and
reports a distance of zero between colours that are plainly different.
`m2brand.simulate` raises on `kind='trit'` rather than returning a misleading
figure, so any tritanopia figure quoted anywhere is unverified.

## The display font

Reportlab's `TTFont` reads TrueType `glyf` outlines only. An OpenType file with CFF
outlines, which is how most licensed display faces ship, cannot be parsed and the
build falls back to Helvetica. The fallback is acceptable; the silence was not, so
`build_report.py` prints which font it actually used.

Getting a CFF-outline face into a PDF needs either a TrueType build of the font or
an HTML-and-headless-Chrome route where CSS loads the OTF directly.

## Verification status

All three builders were last checked against the worked example in `example/Acme/`,
which exercises fourteen workbook sheets, four report exhibits, the disclosure
blocks and the plumbing strip. The DCF sheet discounts on the `t` list the valuation
agent supplies rather than assuming end-of-year, and warns when the terminal
reinvestment rate fails to reconcile to growth over return on capital or when
terminal value passes 70% of enterprise value.
