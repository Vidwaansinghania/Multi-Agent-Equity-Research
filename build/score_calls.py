"""Score calls that have reached their review date, and tally who decided them.

    python build/score_calls.py                    # show what is due and score it
    python build/score_calls.py --write            # also move scored rows in the log
    python build/score_calls.py --early ACME       # score a call before its date
    python build/score_calls.py --tally-only       # attribution table, no prices
    python build/score_calls.py --prices p.csv     # prices from a file, no network

Reads the calls log (``paths.calls_log``) and every ``decision.md`` under
``paths.research_root``. Follows docs/08-calls-log.md: raw return is total return
over the window, alpha is raw return minus the benchmark's total return over the
same window, and the direction test is against alpha.

Prices come from one source for both legs and the source is recorded in the
scored row. The default is Yahoo Finance's daily adjusted close, which folds
dividends in, so the ratio of two adjusted closes is a total return. It is a
free fetch from this script, not a market-data connector, so it spends none of
the market agent's quota. ``--prices`` reads a CSV of ``symbol,date,adjclose``
(``close`` optional) instead, for a source of your own or a machine with no
network. The close on or before each date is used, and a close more than six
days stale is an error rather than a guess.

Without ``--write`` nothing is changed. With it, scored rows leave the open
table and are appended to the scored table. Reflections are not written here:
they are judgment, and the script lists which calls still need one.

The attribution tally reads ``decided_by`` from every closed run, scored or not,
and joins scored rows on ticker and call date. It groups the seven stages into
analysts, valuation and debate, because the question it exists to answer is
whether the debate earns its cost.
"""

import argparse
import csv
import datetime as dt
import glob
import json
import os
import sys
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import m2md
from m2config import CONFIG, REPO_ROOT

OPEN_HEADING = "## Open calls"
SCORED_HEADING = "## Scored calls"
SCORED_COLUMNS = ["Ticker", "Method", "Call date", "Call", "Raw return",
                  "Benchmark return", "Alpha", "Direction right", "Scored"]

STAGES = {
    "fundamentals": "analysts", "market": "analysts", "news": "analysts",
    "industry": "analysts", "valuation": "valuation", "bull": "debate",
    "bear": "debate",
}

# Exchanges whose listings trade in Canadian dollars, and the suffix the price
# source uses for them.
HOME_EXCHANGES = {"TSX": ".TO", "TSXV": ".V", "TSX-V": ".V", "NEO": ".NE",
                  "CBOE CANADA": ".NE", "CSE": ".CN"}

STALE_DAYS = 6


def resolve(path):
    return path if os.path.isabs(path) else os.path.join(REPO_ROOT, path)


def pct(x):
    return "%+.1f%%" % (100 * x)


def parse_pct(text):
    try:
        return float(text.replace("%", "").replace("+", "").strip()) / 100
    except (ValueError, AttributeError):
        return None


def parse_date(text):
    return dt.date.fromisoformat(text.strip())


# ---------------------------------------------------------------- the log --

def cells(line):
    return [c.strip() for c in line.strip().strip("|").split("|")]


def find_table(lines, heading):
    """Return (header, first_row_index, end_index) of the first table under a heading."""
    try:
        start = next(i for i, l in enumerate(lines) if l.strip() == heading)
    except StopIteration:
        sys.exit("the calls log has no '%s' section" % heading)
    i = start + 1
    while i < len(lines) and not lines[i].lstrip().startswith("|"):
        if lines[i].startswith("## "):
            sys.exit("no table under '%s' in the calls log" % heading)
        i += 1
    if i + 1 >= len(lines):
        sys.exit("no table under '%s' in the calls log" % heading)
    header = cells(lines[i])
    first = i + 2                               # skip the |---| separator
    end = first
    while end < len(lines) and lines[end].lstrip().startswith("|"):
        end += 1
    return header, first, end


def read_rows(lines, heading):
    header, first, end = find_table(lines, heading)
    rows = []
    for idx in range(first, end):
        row = dict(zip(header, cells(lines[idx])))
        if row.get("Ticker"):                   # the template's blank row
            row["_line"] = idx
            rows.append(row)
    return rows


def due_rows(open_rows, asof, early):
    out = []
    for row in open_rows:
        if not row.get("Status", "").lower().startswith("pending"):
            continue
        try:
            review = parse_date(row["Review due"])
        except (KeyError, ValueError):
            print("skipping %s %s: review date '%s' is not YYYY-MM-DD"
                  % (row["Ticker"], row.get("Call date"), row.get("Review due")))
            continue
        if review <= asof:
            out.append((row, review, False))
        elif row["Ticker"].upper() in early:
            out.append((row, asof, True))
    return out


def write_log(path, lines, scored):
    """Drop scored rows from the open table and append them to the scored table."""
    drop = {s["row"]["_line"] for s in scored}
    _, _, scored_end = find_table(lines, SCORED_HEADING)
    new_rows = ["| " + " | ".join(s["cells"]) + " |" for s in scored]
    lines = lines[:scored_end] + new_rows + lines[scored_end:]
    lines = [l for i, l in enumerate(lines) if i not in drop]
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(lines) + "\n")


# ------------------------------------------------------------------- runs --

def load_runs(root):
    runs = []
    for path in sorted(glob.glob(os.path.join(root, "*", "runs", "*", "decision.md"))):
        with open(path, encoding="utf-8") as fh:
            fm, _ = m2md.split_frontmatter(fh.read())
        data = m2md.parse_frontmatter(fm)
        data["_path"] = path
        runs.append(data)
    return runs


def find_run(runs, ticker, call_date):
    for run in runs:
        if (run.get("ticker", "").upper() == ticker.upper()
                and run.get("run_date") == call_date):
            return run
    return None


def symbol_for(ticker, run):
    if "." in ticker or run is None:
        return ticker
    return ticker + HOME_EXCHANGES.get(run.get("exchange", "").upper(), "")


def benchmark_for(row, run):
    if row.get("Benchmark"):
        return row["Benchmark"]
    if run and run.get("exchange", "").upper() in HOME_EXCHANGES:
        return CONFIG["scoring"]["benchmark_home"]
    return CONFIG["scoring"]["benchmark"]


# ----------------------------------------------------------------- prices --

class PriceFile:
    def __init__(self, path):
        self.label = os.path.basename(path)
        self.series = {}
        with open(path, newline="", encoding="utf-8") as fh:
            for rec in csv.DictReader(fh):
                close = rec.get("close") or None
                self.series.setdefault(rec["symbol"].upper(), []).append(
                    (parse_date(rec["date"]), float(rec["adjclose"]),
                     float(close) if close else None))
        for bars in self.series.values():
            bars.sort()

    def bars(self, symbol, start, end):
        return self.series.get(symbol.upper(), [])


class Yahoo:
    label = "Yahoo adjusted close"
    URL = ("https://query1.finance.yahoo.com/v8/finance/chart/%s"
           "?period1=%d&period2=%d&interval=1d&events=div%%2Csplit")

    def __init__(self):
        self.cache = {}

    def bars(self, symbol, start, end):
        key = (symbol, start, end)
        if key in self.cache:
            return self.cache[key]
        epoch = lambda d: int(dt.datetime(d.year, d.month, d.day,
                                          tzinfo=dt.timezone.utc).timestamp())
        url = self.URL % (symbol, epoch(start - dt.timedelta(days=14)),
                          epoch(end + dt.timedelta(days=2)))
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                result = json.load(resp)["chart"]["result"][0]
            offset = result["meta"].get("gmtoffset", 0)
            closes = result["indicators"]["quote"][0]["close"]
            adj = result["indicators"]["adjclose"][0]["adjclose"]
        except (OSError, ValueError, KeyError, IndexError, TypeError) as exc:
            raise LookupError("could not fetch %s: %s" % (symbol, exc))
        out = []
        for ts, c, a in zip(result.get("timestamp", []), closes, adj):
            if a is not None:
                day = dt.datetime.fromtimestamp(ts + offset, dt.timezone.utc).date()
                out.append((day, a, c))
        self.cache[key] = out
        return out


def close_on(source, symbol, day, start, end):
    """The bar on or before day, refusing one more than STALE_DAYS old."""
    bars = [b for b in source.bars(symbol, start, end) if b[0] <= day]
    if not bars:
        raise LookupError("no %s price on or before %s" % (symbol, day))
    bar = bars[-1]
    if (day - bar[0]).days > STALE_DAYS:
        raise LookupError("the last %s price before %s is from %s"
                          % (symbol, day, bar[0]))
    return bar


# ---------------------------------------------------------------- scoring --

def direction_right(call, alpha, hold_band):
    """docs/08: BUY beats its benchmark, SELL lags it, HOLD lands inside the band."""
    if call == "BUY":
        return alpha > 0
    if call == "SELL":
        return alpha < 0
    if call == "HOLD":
        return abs(alpha) <= hold_band
    raise ValueError("'%s' is not BUY, HOLD or SELL" % call)


def score(row, end, early, run, source, hold_band, asof):
    ticker, call = row["Ticker"], row["Call"].upper()
    start = parse_date(row["Call date"])
    sym, bench = symbol_for(ticker, run), benchmark_for(row, run)

    s0 = close_on(source, sym, start, start, end)
    s1 = close_on(source, sym, end, start, end)
    b0 = close_on(source, bench, start, start, end)
    b1 = close_on(source, bench, end, start, end)
    raw = s1[1] / s0[1] - 1
    bench_ret = b1[1] / b0[1] - 1
    alpha = raw - bench_ret
    right = direction_right(call, alpha, hold_band)

    warnings = []
    logged = m2md.num({"p": row.get("Price at call", "").lstrip("$")}, "p")
    if logged and s0[2]:
        gap = s0[2] / logged - 1
        if abs(gap) > 0.02:
            warnings.append("%s closed at %.2f on %s against %.2f logged at call "
                            "(%s); check the symbol is the security called"
                            % (sym, s0[2], s0[0], logged, pct(gap)))
    if run is None:
        warnings.append("no run folder found for %s %s, so decided_by is unknown "
                        "and the symbol was taken as written" % (ticker, row["Call date"]))

    stamp = "%s, %s" % (asof.isoformat(), source.label)
    if early:
        stamp = "%s, early at %s" % (stamp, end.isoformat())
    return {
        "row": row, "ticker": ticker, "call": call, "call_date": row["Call date"],
        "raw": raw, "bench": bench, "bench_ret": bench_ret, "alpha": alpha,
        "right": right, "warnings": warnings,
        "window": (s0[0], s1[0]),
        "cells": [ticker, row.get("Method", ""), row["Call date"], call, pct(raw),
                  "%s (%s)" % (pct(bench_ret), bench), pct(alpha),
                  "yes" if right else "no", stamp],
    }


# ------------------------------------------------------------------ tally --

def tally(runs, scored_rows):
    outcomes = {}
    for row in scored_rows:
        alpha = parse_pct(row.get("Alpha", ""))
        right = row.get("Direction right", "").lower().startswith("y")
        if alpha is not None:
            sign = {"BUY": 1, "SELL": -1}.get(row.get("Call", "").upper())
            outcomes[(row["Ticker"].upper(), row["Call date"])] = (
                alpha * sign if sign else None, right)

    by_stage, unknown = {}, []
    for run in runs:
        stage = run.get("decided_by", "").strip().lower()
        if stage not in STAGES:
            unknown.append("%s %s: decided_by '%s'"
                           % (run.get("ticker"), run.get("run_date"), stage or "missing"))
            continue
        rec = by_stage.setdefault(stage, {"runs": 0, "scored": 0, "right": 0, "alphas": []})
        rec["runs"] += 1
        hit = outcomes.get((run.get("ticker", "").upper(), run.get("run_date")))
        if hit:
            rec["scored"] += 1
            rec["right"] += hit[1]
            if hit[0] is not None:
                rec["alphas"].append(hit[0])

    total = sum(r["runs"] for r in by_stage.values())
    print("\nWho decided the call, across %d closed run%s"
          % (total, "" if total == 1 else "s"))
    if not total:
        print("  no decision.md with a valid decided_by under the research root")
    else:
        print("  %-13s %-10s %5s %6s %7s %10s %15s"
              % ("Stage", "Group", "Runs", "Share", "Scored", "Direction",
                 "Alpha as called"))
        groups = {}
        for stage in sorted(by_stage, key=lambda s: (-by_stage[s]["runs"], s)):
            rec = by_stage[stage]
            g = groups.setdefault(STAGES[stage],
                                  {"runs": 0, "scored": 0, "right": 0, "alphas": []})
            for k in g:
                g[k] += rec[k]
            print("  " + row_text(stage, STAGES[stage], rec, total))
        print()
        for group in ("analysts", "valuation", "debate"):
            if group in groups:
                print("  " + row_text(group, "", groups[group], total))
        print("\n  Alpha as called is the mean of alpha on BUYs and minus alpha on "
              "SELLs, so\n  positive means the calls paid. HOLDs count toward "
              "direction only.")
        n_scored = sum(r["scored"] for r in by_stage.values())
        if total < 12 or n_scored < 12:
            print("\n  %d run%s and %d scored. docs/09 asks for a dozen of each before "
                  "this says anything about a stage." % (total, "" if total == 1 else "s",
                                                         n_scored))
        else:
            top = max(groups, key=lambda g: groups[g]["runs"])
            if groups[top]["runs"] / total >= 0.75:
                print("\n  %s carried %d of %d calls. If that group is valuation, "
                      "docs/09 says the debate is decoration." % (top, groups[top]["runs"], total))
    for line in unknown:
        print("  not counted, %s" % line)


def row_text(name, group, rec, total):
    n, a = rec["scored"], rec["alphas"]
    hit = "%d of %d" % (rec["right"], n) if n else "-"
    mean = "%s (%d)" % (pct(sum(a) / len(a)), len(a)) if a else "-"
    return ("%-13s %-10s %5d %5.0f%% %7d %10s %15s"
            % (name, group, rec["runs"], 100 * rec["runs"] / total, n, hit, mean))


# ------------------------------------------------------------------- main --

def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--log", default=resolve(CONFIG["paths"]["calls_log"]),
                    help="calls log (default: paths.calls_log)")
    ap.add_argument("--root", default=resolve(CONFIG["paths"]["research_root"]),
                    help="research root holding the run folders (default: paths.research_root)")
    ap.add_argument("--asof", type=parse_date, default=dt.date.today(),
                    help="score as of this date, YYYY-MM-DD (default: today)")
    ap.add_argument("--early", nargs="+", default=[], metavar="TICKER",
                    help="score these pending calls now, before their review date")
    ap.add_argument("--prices", help="CSV of symbol,date,adjclose[,close] to use "
                                     "instead of fetching")
    ap.add_argument("--hold-band", type=float, default=0.15,
                    help="a HOLD is right when |alpha| is at most this (default 0.15, "
                         "the HOLD band's half-width)")
    ap.add_argument("--write", action="store_true",
                    help="move scored rows from the open table to the scored table")
    ap.add_argument("--tally-only", action="store_true",
                    help="skip scoring and print the decided_by tally")
    args = ap.parse_args()

    if not os.path.exists(args.log):
        sys.exit("no calls log at %s; start one from templates/calls-log.md" % args.log)
    with open(args.log, encoding="utf-8") as fh:
        lines = fh.read().splitlines()
    if find_table(lines, SCORED_HEADING)[0] != SCORED_COLUMNS:
        sys.exit("the scored table's columns differ from docs/08-calls-log.md; "
                 "fix the header before scoring into it")
    runs = load_runs(args.root)
    scored_before = read_rows(lines, SCORED_HEADING)
    failed = False

    if not args.tally_only:
        early = {t.upper() for t in args.early}
        due = due_rows(read_rows(lines, OPEN_HEADING), args.asof, early)
        print("%d call%s due for scoring as of %s, from %s"
              % (len(due), "" if len(due) == 1 else "s", args.asof, args.log))
        source = PriceFile(args.prices) if args.prices else Yahoo()
        scored = []
        for row, end, is_early in due:
            run = find_run(runs, row["Ticker"], row["Call date"])
            try:
                result = score(row, end, is_early, run, source, args.hold_band, args.asof)
            except (LookupError, ValueError, OSError, KeyError) as exc:
                print("  %s %s: not scored, %s" % (row["Ticker"], row["Call date"], exc))
                failed = True
                continue
            scored.append(result)
            print("  %-8s %s %-4s  %s to %s  raw %s, %s %s, alpha %s, direction %s"
                  % (result["ticker"], result["call_date"], result["call"],
                     result["window"][0], result["window"][1], pct(result["raw"]),
                     result["bench"], pct(result["bench_ret"]), pct(result["alpha"]),
                     "right" if result["right"] else "wrong"))
            for w in result["warnings"]:
                print("      warning: %s" % w)

        if scored and args.write:
            write_log(args.log, lines, scored)
            print("\nmoved %d row%s to the scored table in %s"
                  % (len(scored), "" if len(scored) == 1 else "s", args.log))
            print("each needs a reflection under '## Reflections', per docs/08: "
                  + ", ".join("%s %s" % (s["ticker"], s["call_date"]) for s in scored))
        elif scored:
            print("\nnothing written; rerun with --write to move these rows")
        scored_before += [dict(zip(SCORED_COLUMNS, s["cells"])) for s in scored]

    tally(runs, scored_before)
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
