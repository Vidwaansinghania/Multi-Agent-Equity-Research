# 02 · Setup

## What you need

Python 3.11 or newer, because the build scripts read `config.toml` with the
standard-library `tomllib`. On 3.10 and older they fall back to environment
variables and print a line saying so.

```bash
pip install -r requirements.txt
```

Three packages: reportlab for the PDF, openpyxl for the workbook, python-docx for
the workpapers document. Each builder exits with a readable message rather than a
traceback when its package is missing, so you can build two artefacts out of three
on a partial install.

Claude Code, to run the pipeline itself. The build scripts are ordinary Python and
run without it.

## Configure

```bash
cp config.example.toml config.toml
```

Set at least `analyst.name`, which is printed on the report cover and in the
analyst certification, and `analyst.email`, which goes into the SEC EDGAR
User-Agent header. Everything else has a working default.
[config.example.toml](../config.example.toml) documents each key inline.

`config.toml` is gitignored. So is `research/`, so real research stays out of the
repository unless you decide otherwise.

Environment variables override the file. The mapping is at the top of
[build/m2config.py](../build/m2config.py); `M2_ANALYST`, `M2_ANALYST_EMAIL` and
`M2_CONFIG` are the ones worth knowing.

## Install the skill

The trigger phrase lives in a Claude Code skill:

```bash
mkdir -p .claude/skills && cp -r skills/method-2 .claude/skills/
```

Claude Code then starts a run when you type `run a multi agent equity research
report on <TICKER>`, and only then. The skill is written to refuse adjacent
requests, because a full run spawns ten agents and spends a daily market-data
quota, so an accidental trigger has a real cost.

## SEC EDGAR

EDGAR returns 403 to any request without a User-Agent naming a person and a
contact address. Most HTTP fetch tools send none, so they fail on every `sec.gov`
path. Fetch with Python and set the header:

```python
import json, urllib.request

def edgar(url, email, name):
    req = urllib.request.Request(url, headers={"User-Agent": "%s %s" % (name, email)})
    return json.load(urllib.request.urlopen(req))

facts = edgar("https://data.sec.gov/api/xbrl/companyfacts/CIK0000789019.json",
              "you@example.com", "Your Name")
```

Two entry points carry almost everything a run needs:

| Endpoint | What it gives |
|---|---|
| `data.sec.gov/submissions/CIK##########.json` | The filing index: accession numbers and primary documents, newest first |
| `data.sec.gov/api/xbrl/companyfacts/CIK##########.json` | Every tagged XBRL figure the company has filed, which is where ten years of statements comes from in one request |

Company facts does not carry segment detail or guidance. Those come from the 10-K
and the 8-K exhibits, whose URLs preflight resolves out of the filing index.

Preflight fetches both once and saves company facts into the run folder, so no
agent calls either endpoint. See [docs/03-pipeline.md](03-pipeline.md).

## Market data

The market analyst is the only agent allowed to spend market-data calls. Set
`market_data.connectors` to the MCP connector identifiers serving your data, in
the order they should be used, and `market_data.daily_call_cap` to the total
across all of them.

Two things about connector identifiers. MCP tools are namespaced
`mcp__<connector-id>__FUNCTION` and carry no display name, so the run has to be
handed the mapping explicitly rather than inferring it — the order connectors
appear in a session is not meaningful. And if your connectors are shared with
another task, say which are off limits in the same place, because a run that
spends someone else's quota breaks their morning.

The cap is a ceiling, not an allowance. Free sources cover most of what the market
analyst needs: stockanalysis.com carries price, market capitalisation, multiples
and consensus, and FRED serves the ten-year Treasury as CSV at
`fred.stlouisfed.org/graph/fredgraph.csv?id=DGS10`. The worked example in
`example/Acme/` answers its market questions in six calls.

Tickers outside the primary US exchanges usually need a suffix to quote at all,
`.TO` and `.V` for Toronto and the Venture exchange among them. Resolve the suffix
in preflight rather than halfway through a run.

## Fonts

Reportlab's `TTFont` reads TrueType `glyf` outlines only. An OpenType file with
CFF outlines, which is how most licensed display faces ship, cannot be parsed, and
the build falls back to Helvetica. That fallback is fine; silence about it is not,
so `build_report.py` prints which font it actually used.

Leave the `[fonts]` section empty to run on Helvetica deliberately. To use a
display face, point `fonts.dir` at a directory holding TrueType builds and name
the two files. Getting a CFF-outline face into a PDF needs either a TrueType
build of it or an HTML-and-headless-Chrome route where CSS loads the OTF
directly.

## Check the install

Build all three artefacts from the worked example, which uses an invented company:

```bash
python build/build_workpapers.py example/Acme/runs/2026-01-15
```

```bash
python build/build_workbook.py example/Acme/runs/2026-01-15
```

```bash
python build/build_report.py example/Acme/runs/2026-01-15 --brand "#1F5C8B" --brand-source "investor relations stylesheet"
```

Expect a fourteen-sheet workbook, a twelve-section Word file and a six-page PDF in
`example/Acme/runs/2026-01-15/exports/`. The PDF build also prints its contrast
checks and every sentence it stripped; both exist to be read. See
[docs/07-exports.md](07-exports.md).

On Windows set `PYTHONIOENCODING=utf-8` before running the builders, or a minus
sign in the console output raises a `UnicodeEncodeError` on the default code page.
