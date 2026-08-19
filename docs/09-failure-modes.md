# 09 · Failure modes

## During a run

| Symptom | Cause | Fix |
|---|---|---|
| An analyst returns thin output | The ticker has little SEC presence, or the agent burned its budget on one source | Re-run that agent alone with a narrower brief. Do not let the judge rule on a gap |
| Fewer than ten years of statements available | The company listed recently, changed its fiscal year, or restated | Take what exists, label the span in `statements.csv` and in the report, and say plainly it is short. A padded series is worse than a short one |
| A market-data connector returns nothing | That connector has hit its daily limit | Move to the next one in order. Once all are spent, fall back to stockanalysis.com for price and consensus and FRED for rates, and note the fallback in `run.md`. Never substitute a connector belonging to another task |
| Bull and bear reach the same conclusion | The base case is uncontroversial, or the prompts drifted | A legitimate outcome. Say so in the decision record; a call nobody can argue against is information |
| The judge lands exactly on a band edge | Genuinely marginal | Take the band, then state the marginality and the flipping assumption. Never invent a fourth rating |
| `model.py` and `decision.md` disagree | The judge overrode the valuation agent's target | Patch `model.py` from `decision.md`, rebuild both artefacts, and note the override in the decision record. Never edit `decision.md` to match the model |
| An agent quotes a price nobody else used | It fetched its own instead of using the preflight price | Re-run that agent with the price restated. The scenario table will not add up otherwise |
| Two runs on the same ticker disagree | Non-determinism, or new evidence | Keep both run folders. Divergence between two runs a week apart measures the process's own stability and is worth more than either answer |

## During a build

| Symptom | Cause | Fix |
|---|---|---|
| `No report.md in <path>` | Stage 6 has not run | Run stage 6. The workpapers and workbook builders do not need it |
| `model.py failed to import` | A syntax error, or computation at module level | The contract is plain literals only. Fix the module, do not work around it in the builder |
| The PDF has no exhibits | The report's headings lost their two-digit section numbers | The builder keys exhibits off `## 04`, `## 05` and `## 08`. Restore the numbers |
| The PDF names a build script | The strip pass missed a sentence | Fix the pattern in `m2md.py`, not in `report.md`, then rebuild and diff the text against the previous version |
| A whole paragraph vanished from the PDF | The strip pattern is over-broad | Read the dropped-sentence list the build prints, narrow the pattern, rebuild |
| The report is set in Helvetica | No display font configured, or the file has CFF outlines reportlab cannot parse | Expected. Configure a TrueType build of the face, or accept the fallback; the build says which font it used |
| The cover reads `[ANALYST NAME]` | `analyst.name` is unset | Set it in `config.toml` or in `M2_ANALYST` |
| Workbook sheets are missing | `statements.csv` or `model.py` is absent or partial | The README sheet names what it skipped and why |
| `UnicodeEncodeError` on a minus sign | Windows console code page | Set `PYTHONIOENCODING=utf-8` before running the builder |
| SEC EDGAR returns 403 | No User-Agent, or one without a contact address | Fetch with Python and set a header naming a person and an email. Most generic fetch tools cannot do this |

## Design failures worth watching for

**The judge agreeing with prior coverage.** If any agent reads an existing call
before the judge rules, the run collapses into agreement with it and produces a
confirmation dressed as an independent process. This is why the anchoring rule is
absolute and why `comparison.md` is stage 7.

**Attribution always landing on one stage.** If `decided_by` reads `valuation` across
a dozen runs, the debate is decoration. That is a finding about the pipeline, and the
answer is to cut stages rather than to keep paying for them.

**A log full of pending rows.** Unscored calls are opinions. A year of pending rows
means the process has produced no evidence about itself.
