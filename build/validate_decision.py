"""Check a run's decision record against the contract in docs/05-output-schema.md.

The workbook and report builders call enforce() before they write anything, so a
run whose rating, band, scenarios or model disagree fails loudly instead of
shipping an artefact. The workpapers builder calls warn(): it documents failed and
partial runs too, and lists the problems instead of refusing.
Every problem is collected and printed together, so one pass shows the whole fix.

    python build/validate_decision.py "<run folder>"

Exits 0 when the record holds, 1 with one line per problem when it does not.

What it checks
    - rating is BUY, HOLD or SELL
    - expected_total_return is a decimal inside the rating's band
    - expected_total_return reconciles to target, reference price and dividend
    - marginal matches the distance to a band edge, with a flip_assumption when true
    - decided_by and conviction take an allowed value
    - scenario probabilities sum to 1 and the weighted target reconciles to target
    - model.py agrees: META price and date, SCENARIOS, WEIGHTED
"""

import argparse
import importlib.util
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import m2md

RATINGS = ("BUY", "HOLD", "SELL")
BAND_EDGE = 0.15          # above +15% BUY, below -15% SELL, HOLD between, edges inclusive
MARGINAL_WIDTH = 0.05     # within 5 points of either edge
DECIDED_BY = ("fundamentals", "market", "news", "industry", "valuation", "bull", "bear")
CONVICTION = ("low", "moderate", "high")
SCENARIO_KEYS = ("bull", "base", "bear")
REQUIRED = ("ticker", "run_date", "reference_price", "price_date", "rating", "target",
            "expected_total_return", "conviction", "marginal", "decided_by", "scenarios")

# Tolerances. Targets are stated to the cent and returns to a tenth of a point, so
# these absorb rounding and nothing larger.
PROB_TOL = 1e-6
PRICE_TOL = 0.01
RETURN_TOL = 0.0006

_SCENARIO = re.compile(
    r"^(\w+):\s*\{\s*probability:\s*([-+0-9.eE]+)\s*,\s*target:\s*([-+0-9.eE,]+)\s*\}\s*$")


def band(ret):
    if ret > BAND_EDGE:
        return "BUY"
    if ret < -BAND_EDGE:
        return "SELL"
    return "HOLD"


def is_marginal(ret):
    return min(abs(ret - BAND_EDGE), abs(ret + BAND_EDGE)) <= MARGINAL_WIDTH + 1e-9


def parse_scenarios(raw):
    """The scenarios block, raw from m2md, to {name: (probability, target)}."""
    out, bad = {}, []
    for line in (raw or "").splitlines():
        m = _SCENARIO.match(line.strip())
        if not m:
            bad.append(line.strip())
            continue
        try:
            out[m.group(1)] = (float(m.group(2)), float(m.group(3).replace(",", "")))
        except ValueError:
            bad.append(line.strip())
    return out, bad


def load_model(path):
    spec = importlib.util.spec_from_file_location("m2model_validate", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def check(run_dir):
    """Return a list of problems with the run's decision record. Empty means it holds."""
    errors = []
    dec_path = os.path.join(run_dir, "decision.md")
    if not os.path.exists(dec_path):
        return ["no decision.md: stage 4 has not run"]
    fm, _ = m2md.read_note(dec_path)

    for key in REQUIRED:
        if str(fm.get(key, "")).strip() == "":
            errors.append("%s is missing" % key)

    rating = fm.get("rating", "")
    if rating and rating not in RATINGS:
        errors.append("rating %r is not one of BUY, HOLD, SELL" % rating)

    ret = None
    raw_ret = str(fm.get("expected_total_return", "")).strip()
    if raw_ret:
        try:
            ret = float(raw_ret)
        except ValueError:
            errors.append("expected_total_return %r is not a decimal" % raw_ret)
        else:
            if abs(ret) > 5:
                errors.append("expected_total_return %s reads as a percentage; "
                              "write it as a decimal" % raw_ret)
                ret = None
    if ret is not None and rating in RATINGS and band(ret) != rating:
        errors.append("expected_total_return %+.1f%% falls in the %s band, not %s"
                      % (ret * 100, band(ret), rating))

    marginal = str(fm.get("marginal", "")).strip().lower()
    if marginal and marginal not in ("true", "false"):
        errors.append("marginal %r is not true or false" % fm.get("marginal"))
    elif marginal and ret is not None:
        if (marginal == "true") != is_marginal(ret):
            errors.append("marginal is %s but %+.1f%% is %s 5 points of a band edge"
                          % (marginal, ret * 100,
                             "within" if is_marginal(ret) else "more than"))
    if marginal == "true" and not str(fm.get("flip_assumption", "")).strip():
        errors.append("marginal is true but flip_assumption is empty")

    decided_by = fm.get("decided_by", "")
    if decided_by and decided_by not in DECIDED_BY:
        errors.append("decided_by %r is not one of %s" % (decided_by, ", ".join(DECIDED_BY)))
    conviction = fm.get("conviction", "")
    if conviction and conviction not in CONVICTION:
        errors.append("conviction %r is not one of %s" % (conviction, ", ".join(CONVICTION)))

    target = m2md.num(fm, "target")
    price = m2md.num(fm, "reference_price")
    scenarios, bad = parse_scenarios(fm.get("scenarios"))
    for line in bad:
        errors.append("scenarios line not understood: %r" % line)
    if fm.get("scenarios"):
        if sorted(scenarios) != sorted(SCENARIO_KEYS):
            errors.append("scenarios are %s; expected bull, base, bear"
                          % (", ".join(sorted(scenarios)) or "none"))
        elif scenarios:
            psum = sum(p for p, _ in scenarios.values())
            if abs(psum - 1) > PROB_TOL:
                errors.append("scenario probabilities sum to %.4f, not 1" % psum)
            weighted = sum(p * t for p, t in scenarios.values())
            if target is not None and abs(weighted - target) > PRICE_TOL:
                errors.append("scenarios weight to %.2f but target is %.2f"
                              % (weighted, target))

    model_path = os.path.join(run_dir, "model.py")
    if not os.path.exists(model_path):
        errors.append("no model.py: stage 2 has not run")
        return errors
    try:
        model = load_model(model_path)
    except Exception as exc:                       # noqa: BLE001
        errors.append("model.py failed to import: %s" % exc)
        return errors

    meta = getattr(model, "META", None) or {}
    if price is not None and meta.get("price") is not None \
            and abs(float(meta["price"]) - price) > PRICE_TOL:
        errors.append("model.py META price %.2f differs from reference_price %.2f"
                      % (meta["price"], price))
    if fm.get("price_date") and meta.get("price_date") \
            and str(meta["price_date"]) != fm["price_date"]:
        errors.append("model.py META price_date %s differs from %s"
                      % (meta["price_date"], fm["price_date"]))
    if fm.get("ticker") and meta.get("ticker") and meta["ticker"] != fm["ticker"]:
        errors.append("model.py META ticker %s differs from %s" % (meta["ticker"], fm["ticker"]))

    if ret is not None and target is not None and price:
        dividend = float(meta.get("dividend_12m") or 0)
        implied = (target + dividend) / price - 1
        if abs(implied - ret) > RETURN_TOL:
            errors.append("target %.2f plus dividend %.2f on price %.2f is %+.1f%%, "
                          "but expected_total_return is %+.1f%%"
                          % (target, dividend, price, implied * 100, ret * 100))

    weighted = getattr(model, "WEIGHTED", None)
    if not weighted:
        errors.append("model.py has no WEIGHTED")
    else:
        if target is not None and abs(float(weighted.get("target", 0)) - target) > PRICE_TOL:
            errors.append("model.py WEIGHTED target %s differs from decision.md %.2f; "
                          "patch WEIGHTED and rebuild" % (weighted.get("target"), target))
        if ret is not None and abs(float(weighted.get("expected_total_return", 0)) - ret) \
                > RETURN_TOL:
            errors.append("model.py WEIGHTED expected_total_return %s differs from "
                          "decision.md %s; patch WEIGHTED and rebuild"
                          % (weighted.get("expected_total_return"), raw_ret))

    m_scen = getattr(model, "SCENARIOS", None)
    if not m_scen:
        errors.append("model.py has no SCENARIOS")
    elif scenarios:
        for name, (p, t) in sorted(scenarios.items()):
            row = m_scen.get(name)
            if not row:
                errors.append("model.py SCENARIOS has no %s" % name)
                continue
            if abs(float(row.get("probability", -1)) - p) > PROB_TOL:
                errors.append("model.py %s probability %s differs from decision.md %s"
                              % (name, row.get("probability"), p))
            if abs(float(row.get("target", -1)) - t) > PRICE_TOL:
                errors.append("model.py %s target %s differs from decision.md %.2f"
                              % (name, row.get("target"), t))
    return errors


def enforce(run_dir):
    """Exit with every problem listed if the decision record breaks the contract."""
    errors = check(run_dir)
    if errors:
        sys.exit("decision.md fails the contract in %s:\n  - %s\n"
                 "Where model.py disagrees, patch it to match decision.md. Never edit "
                 "decision.md to match the model; see docs/05-output-schema.md."
                 % (run_dir, "\n  - ".join(errors)))


def warn(run_dir):
    """Print every problem without stopping. For the workpapers, which document a
    failed or partial run as faithfully as a good one."""
    errors = check(run_dir)
    if errors:
        print("warning: decision.md fails the contract:\n  - %s"
              % "\n  - ".join(errors), file=sys.stderr)
    return errors


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("run_dir")
    args = ap.parse_args()
    run_dir = os.path.abspath(args.run_dir)
    errors = check(run_dir)
    if errors:
        print("FAIL %s" % run_dir)
        for e in errors:
            print("  - %s" % e)
        sys.exit(1)
    print("ok %s" % run_dir)


if __name__ == "__main__":
    main()
