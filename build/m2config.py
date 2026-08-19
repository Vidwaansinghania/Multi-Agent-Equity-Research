"""Configuration for the export scripts.

Values come from three places, later ones winning: the defaults below, a
``config.toml`` at the repository root, and environment variables. Nothing here
is a secret and nothing here belongs in a run folder — a run records what it
used in ``run.md``, and this file records how the machine is set up.

    from m2config import CONFIG
    CONFIG["analyst"]["name"]

Environment overrides:

    M2_CONFIG            path to a config file other than <repo>/config.toml
    M2_ANALYST           analyst name printed on the cover and the certification
    M2_ANALYST_EMAIL     contact address for the SEC EDGAR User-Agent header
    M2_FONT_DIR          directory holding the display font files
    M2_DISPLAY_REGULAR   TrueType file for the display face, regular weight
    M2_DISPLAY_BOLD      TrueType file for the display face, bold weight
"""

import os
import sys

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

DEFAULTS = {
    "analyst": {"name": "", "email": ""},
    "fonts": {"dir": "", "display_regular": "", "display_bold": ""},
    "paths": {"python": sys.executable, "research_root": "research"},
    "scoring": {"benchmark": "SPY"},
    "market_data": {"connectors": [], "daily_call_cap": 75},
}

ENV = {
    ("analyst", "name"): "M2_ANALYST",
    ("analyst", "email"): "M2_ANALYST_EMAIL",
    ("fonts", "dir"): "M2_FONT_DIR",
    ("fonts", "display_regular"): "M2_DISPLAY_REGULAR",
    ("fonts", "display_bold"): "M2_DISPLAY_BOLD",
    ("paths", "python"): "M2_PYTHON",
    ("paths", "research_root"): "M2_RESEARCH_ROOT",
    ("scoring", "benchmark"): "M2_BENCHMARK",
}

MISSING = []


def _read_file(path):
    if not path or not os.path.exists(path):
        return {}
    try:
        import tomllib
    except ImportError:                     # Python 3.10 and older
        MISSING.append("tomllib is unavailable, so %s was not read; set the "
                       "M2_* environment variables instead" % path)
        return {}
    with open(path, "rb") as fh:
        return tomllib.load(fh)


def load():
    cfg = {k: dict(v) for k, v in DEFAULTS.items()}
    path = os.environ.get("M2_CONFIG") or os.path.join(REPO_ROOT, "config.toml")
    for section, values in _read_file(path).items():
        if isinstance(values, dict):
            cfg.setdefault(section, {}).update(values)
        else:
            cfg[section] = values
    for (section, key), var in ENV.items():
        val = os.environ.get(var)
        if val:
            cfg.setdefault(section, {})[key] = val
    if not cfg["analyst"]["name"]:
        MISSING.append("no analyst name is set, so the cover and the analyst "
                       "certification will read [ANALYST NAME]; set it in "
                       "config.toml or in M2_ANALYST")
        cfg["analyst"]["name"] = "[ANALYST NAME]"
    return cfg


CONFIG = load()
ANALYST = CONFIG["analyst"]["name"]
