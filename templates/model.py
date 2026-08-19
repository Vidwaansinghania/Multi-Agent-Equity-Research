"""Method 2 valuation numbers -- <TICKER>, run <YYYY-MM-DD>. Written by the
valuation agent. Every figure traces to an analyst file; see valuation.md.

Plain literals only: no imports, no I/O, no computation beyond arithmetic on
literals already stated. Both export builders import this module, so it is the only
copy of these figures that exists. The contract is docs/05-output-schema.md; a
missing optional key skips an exhibit, a misspelled key fails the build.
"""

META = {
    "ticker": "<TICKER>", "company": "<legal name>", "exchange": "<EXCHANGE>",
    "currency": "USD", "price": 0.0, "price_date": "<YYYY-MM-DD>",
    "run_date": "<YYYY-MM-DD>", "fiscal_year_end": "<Mon DD>",
    "shares_diluted": 0.0,        # millions
    "dividend_12m": 0.0,          # per share, over the target horizon
}

DCF = {
    "wacc": 0.0, "terminal_growth": 0.0,
    "discounting": "mid-year",            # "mid-year" | "year-end"
    # the part-year between the run date and the next fiscal year end, or None
    "stub": {"label": "<H2 FY20XXE>", "fraction": 0.0, "t": 0.0,
             "fcf": 0.0, "pv": 0.0},
    "years": ["FY20XXE"] * 10,
    "fcf": [0.0] * 10,                    # USD millions
    "t": [0.5, 1.5, 2.5, 3.5, 4.5, 5.5, 6.5, 7.5, 8.5, 9.5],
    "terminal_method": "perpetuity growth",   # exit multiple is a cross-check
    "terminal_roic": 0.0,                     # return on new capital, terminal year
    "terminal_reinvestment_rate": 0.0,        # terminal_growth / terminal_roic
    "pv_forecast": 0.0, "terminal_value": 0.0, "pv_terminal": 0.0,
    "tv_share_of_ev": 0.0,                    # above 0.70 gets a warning line
    "enterprise_value": 0.0, "net_debt": 0.0,
    "net_debt_basis": "<how net debt was computed and how leases were treated>",
    "equity_value": 0.0, "value_per_share": 0.0,
    "reverse_dcf": {"implied_growth": 0.0, "implied_margin": None,
                    "implied_wacc": 0.0, "implied_terminal_growth": 0.0,
                    "verdict": "<what the current price already assumes, and whether "
                               "anything in the analyst files supports it>"},
    # (label, value as text, basis and source) -- rendered as the assumptions sheet
    "assumptions": [("WACC", "0.00%", "<CAPM inputs with their sources>"),
                    ("Terminal growth", "0.00%", "<basis>")],
}

SCENARIOS = {   # probabilities must sum to 1.0
    "bull": {"probability": 0.0, "target": 0.0, "exit_multiple": 0.0,
             "eps": 0.0, "note": "<what has to be true>"},
    "base": {"probability": 0.0, "target": 0.0, "exit_multiple": 0.0,
             "eps": 0.0, "note": "<what has to be true>"},
    "bear": {"probability": 0.0, "target": 0.0, "exit_multiple": 0.0,
             "eps": 0.0, "note": "<what has to be true>"},
}

WEIGHTED = {"target": 0.0, "expected_total_return": 0.0, "horizon_months": 12}

ESTIMATES = {   # three actual years then two estimated
    "years": ["FY20XXA", "FY20XXA", "FY20XXA", "FY20XXE", "FY20XXE"],
    "rows": [("Revenue (USD m)", [0.0] * 5),
             ("Revenue growth", [0.0] * 5),
             ("Gross margin", [0.0] * 5),
             ("Operating margin", [0.0] * 5),
             ("EBITDA (USD m)", [0.0] * 5),
             ("Net income (USD m)", [0.0] * 5),
             ("Diluted EPS (USD)", [0.0] * 5),
             ("Free cash flow (USD m)", [0.0] * 5)],
}

SENSITIVITY = {
    "row_label": "<assumption that moves the target most>", "row_values": [0.0] * 5,
    "col_label": "<second assumption>", "col_values": [0.0] * 3,
    "grid": [[0.0] * 3 for _ in range(5)],    # targets, rows x cols
}

COMPS = {
    "columns": ["P/E fwd", "EV/EBITDA", "EV/Sales", "FCF yield"],
    "subject": ("<company>", "<TICKER>", [0.0, 0.0, 0.0, 0.0]),
    "rows": [("<peer>", "<TICKER>", [0.0, 0.0, 0.0, 0.0])],
}

FOOTBALL = [   # (label, low, high) -- every row a genuine range
    ("DCF", 0.0, 0.0),
    ("Comparables", 0.0, 0.0),
    ("52-week range", 0.0, 0.0),
    ("Street targets", 0.0, 0.0),
    ("Scenario range", 0.0, 0.0),
]

SOURCES = [   # numbered in the appendix in this order
    (1, "<filing, date>", "<url>"),
]
