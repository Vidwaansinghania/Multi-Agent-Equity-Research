---
agent: valuation
model: claude-opus-5
stage: 2
---

# Valuation — ACME

Every figure below is invented. See `run.md`. The numbers are also in `model.py`,
which is what the workbook and the report read.

## Method

Discounted free cash flow to the firm as primary, comparable multiples as
secondary. Ten explicit forecast years, mid-year discounting, no stub because
fiscal 2025 closed on 2025-12-31. Terminal value by perpetuity growth at 2.5%
with terminal reinvestment at growth over return on new capital, 2.5% / 14.0% =
17.9%. Reverse discounted cash flow as a check.

## Cost of capital

WACC of 8.50%. Cost of equity 9.30% from a 4.20% ten-year Treasury, a 5.0%
equity risk premium and a five-year monthly beta of 1.02. After-tax cost of debt
3.6% at 24% of total capital, on the existing coupon schedule rather than a
marginal rate.

## Forecast

Revenue grows 5.0% for three years, fading to 3.0% by FY2032, which is below the
5.5% ten-year history and consistent with the guidance cut in October. Operating
margin holds at 19.6%, up 30bp from FY2025 on the water-based mix and no better.
Capital expenditure runs 5.0% of revenue, against 5.1% over the past five years.
Free cash flow grows from $1,440m to $2,115m, a 4.4% compound rate.

## Result

| Item | Value |
|---|---|
| PV of forecast cash flow | $12,092m |
| Terminal value | $36,131m |
| PV of terminal value | $15,980m |
| Terminal value share of enterprise value | 56.9% |
| Enterprise value | $28,072m |
| Net debt | $1,800m |
| Equity value | $26,272m |
| Value per share | $105.09 |

At a WACC of 9.0% with 2.3% terminal growth the value is $94.70; at 8.0% with
2.7% it is $118.16. That range, $95 to $118, is the discounted cash flow row of
the football field.

Comparables give $98 to $126 on a 17.2x to 22.4x forward earnings range against
FY2027E EPS of $5.45, with Acme's own ten-year median of 18.2x inside it.

## Reverse discounted cash flow

Holding everything else, the current $100.00 implies terminal growth of 2.05%
against 2.50% assumed here, or a WACC of 8.84% against 8.50%. The market is
paying for slightly less than this forecast rather than for a different business.

## Scenarios

| Case | Probability | Exit multiple | FY2027E EPS | Target |
|---|---|---|---|---|
| Bull | 25% | 24.0x | $5.75 | $138.00 |
| Base | 50% | 20.5x | $5.45 | $112.00 |
| Bear | 25% | 14.0x | $5.15 | $72.00 |

Probability-weighted target $108.50. The bear probability is set at 25% rather
than lower because the insourcing risk the industry analyst found is specific,
dated and named by the customers themselves.

## Where the analysts disagreed

The market analyst has consensus FY2026 EPS at $5.08 and the fundamentals file
supports $5.12 on the same revenue. The lower figure is used, because the
difference is inside the rounding on segment margin and taking consensus keeps
the comparison honest.

No rating is stated here. That is stage 4's job.
