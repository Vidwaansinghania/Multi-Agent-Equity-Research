"""Method 2 valuation numbers -- ACME, run 2026-01-15. Written by the valuation
agent. Every figure traces to an analyst file; see valuation.md.

Acme Materials Corporation is invented. The figures are a fixture that exercises
every workbook sheet and every report exhibit, and they are not a view on any
real company.
"""

META = {
    "ticker": "ACME", "company": "Acme Materials Corporation", "exchange": "NYSE",
    "currency": "USD", "price": 100.00, "price_date": "2026-01-09",
    "run_date": "2026-01-15", "fiscal_year_end": "Dec 31",
    "shares_diluted": 250.0,      # millions
    "dividend_12m": 2.20,         # per share, over the target horizon
}

DCF = {
    "wacc": 0.085, "terminal_growth": 0.025,
    "discounting": "mid-year",
    # FY2025 closed on 2025-12-31, three weeks before the run, so there is no stub
    "stub": None,
    "years": ["FY2026E", "FY2027E", "FY2028E", "FY2029E", "FY2030E",
              "FY2031E", "FY2032E", "FY2033E", "FY2034E", "FY2035E"],
    "fcf": [1_440.0, 1_535.0, 1_630.0, 1_720.0, 1_810.0,
            1_890.0, 1_965.0, 2_030.0, 2_075.0, 2_115.0],   # USD millions
    "t": [0.5, 1.5, 2.5, 3.5, 4.5, 5.5, 6.5, 7.5, 8.5, 9.5],
    "terminal_method": "perpetuity growth",
    "terminal_roic": 0.14,
    "terminal_reinvestment_rate": 0.179,      # 0.025 / 0.14
    "pv_forecast": 12_092.1, "terminal_value": 36_131.2, "pv_terminal": 15_980.3,
    "tv_share_of_ev": 0.569,
    "enterprise_value": 28_072.4, "net_debt": 1_800.0,
    "net_debt_basis": "Funded debt of $2,480m less cash of $680m; operating "
                      "leases charged to operating expense",
    "equity_value": 26_272.4, "value_per_share": 105.09,
    "reverse_dcf": {"implied_growth": 0.021, "implied_margin": 0.193,
                    "implied_wacc": 0.0884, "implied_terminal_growth": 0.0205,
                    "verdict": "The current price implies 2.1% terminal growth "
                               "against 2.5% in the base case. The market is "
                               "paying for slightly less than this run assumes, "
                               "which is a narrow disagreement rather than a "
                               "mispricing."},
    "assumptions": [
        ("WACC", "8.50%", "CAPM: DGS10 4.20% + 5.0% ERP, beta 1.02, "
                          "after-tax cost of debt 3.6% at 24% of capital"),
        ("Terminal growth", "2.50%", "Long-run US nominal GDP"),
        ("Terminal ROIC", "14.0%", "Ten-year average of 15.1%, faded for "
                                   "competitive entry in adhesives"),
        ("Forecast FCF CAGR", "4.4%", "Revenue at 5.0% fading to 3.0%, "
                                      "operating margin flat at 19.6%"),
    ],
}

SCENARIOS = {   # probabilities must sum to 1.0
    "bull": {"probability": 0.25, "target": 138.00, "exit_multiple": 24.0,
             "eps": 5.75, "note": "Adhesives price increases hold and the "
                                  "Dalton plant reaches full utilisation in "
                                  "FY2027"},
    "base": {"probability": 0.50, "target": 112.00, "exit_multiple": 20.5,
             "eps": 5.45, "note": "Volume grows with industrial production, "
                                  "margin flat"},
    "bear": {"probability": 0.25, "target": 72.00, "exit_multiple": 14.0,
             "eps": 5.15, "note": "Two of the three largest coatings customers "
                                  "insource, taking 9% of segment revenue"},
}

WEIGHTED = {"target": 108.50, "expected_total_return": 0.107,
            "horizon_months": 12}

ESTIMATES = {
    "years": ["FY2023A", "FY2024A", "FY2025A", "FY2026E", "FY2027E"],
    "rows": [("Revenue (USD m)", [7_620.0, 7_980.0, 8_400.0, 8_820.0, 9_260.0]),
             ("Revenue growth", [0.061, 0.047, 0.053, 0.050, 0.050]),
             ("Gross margin", [0.386, 0.388, 0.390, 0.391, 0.392]),
             ("Operating margin", [0.1872, 0.1900, 0.1933, 0.1950, 0.1965]),
             ("EBITDA (USD m)", [1_754.0, 1_859.3, 1_985.2, 2_075.0, 2_175.0]),
             ("Net income (USD m)", [1_027.4, 1_098.2, 1_182.7, 1_245.0, 1_310.0]),
             ("Diluted EPS (USD)", [4.01, 4.34, 4.73, 5.08, 5.45]),
             ("Free cash flow (USD m)", [1_120.0, 1_235.0, 1_340.0, 1_440.0, 1_535.0])],
}

SENSITIVITY = {
    "row_label": "Exit multiple", "row_values": [17.0, 18.5, 20.5, 21.5, 23.0],
    "col_label": "FY2027E EPS", "col_values": [5.15, 5.45, 5.75],
    "grid": [[87.6, 92.7, 97.8],
             [95.3, 100.8, 106.4],
             [105.6, 111.7, 117.9],
             [110.7, 117.2, 123.6],
             [118.5, 125.4, 132.3]],
}

COMPS = {
    "columns": ["P/E fwd", "EV/EBITDA", "EV/Sales", "FCF yield"],
    "subject": ("Acme Materials", "ACME", [19.7, 14.1, 3.3, 0.054]),
    "rows": [("Northbridge Chemical", "NBC", [17.2, 11.8, 2.4, 0.061]),
             ("Calder Specialty", "CSP", [22.4, 15.6, 3.8, 0.044]),
             ("Ferro-Lane Industries", "FLI", [15.8, 10.4, 1.9, 0.068])],
}

FOOTBALL = [
    ("DCF", 94.70, 118.16),
    ("Comparables", 98.00, 126.00),
    ("52-week range", 84.20, 121.60),
    ("Street targets", 95.00, 130.00),
    ("Scenario range", 72.00, 138.00),
]

SOURCES = [
    (1, "Acme Materials Corporation, Form 10-K for fiscal 2025, filed 2026-02-18",
     "example.invalid/acme/10-K-2025"),
    (2, "Acme Materials Corporation, Form 8-K, Q3 fiscal 2025 results, 2025-10-29",
     "example.invalid/acme/8-K-2025-10-29"),
    (3, "Acme Materials Corporation, Q3 fiscal 2025 earnings call transcript, 2025-10-29",
     "example.invalid/acme/transcript-2025-10-29"),
    (4, "US Treasury ten-year constant maturity (DGS10), 2026-01-09, FRED",
     "fred.stlouisfed.org/series/DGS10"),
]
