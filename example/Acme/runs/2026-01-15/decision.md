---
method: 2
ticker: ACME
exchange: NYSE
company: Acme Materials Corporation
run_date: 2026-01-15
reference_price: 100.00
price_date: 2026-01-09
rating: HOLD
target: 108.50
target_horizon_months: 12
expected_total_return: 0.107
conviction: moderate
marginal: true
flip_assumption: >
  The 25% bear probability, which rests on two named coatings customers
  evaluating insourcing. At 15% bear and 35% base the weighted target is
  $117.15 and the expected total return is +19.4%, which is BUY. A multi-year
  renewal from either customer is the event that moves it.
decided_by: industry
scenarios:
  bull:  { probability: 0.25, target: 138.00 }
  base:  { probability: 0.50, target: 112.00 }
  bear:  { probability: 0.25, target: 72.00 }
position: null
models:
  analysts: claude-sonnet-5
  decision: claude-opus-5
  report: claude-opus-5
alpha_vantage_calls: 6
---

# Decision — ACME, 2026-01-15

Acme Materials Corporation is invented and so is every figure here. This file
exists to show the shape of a decision record.

## The call

HOLD, twelve-month target $108.50, expected total return of +10.7% including
$2.20 of dividends against a $100.00 reference price on 2026-01-09. Conviction
moderate. The business is better than its multiple suggests and the customer
concentration is worse than its history suggests, and those two cancel inside the
HOLD band.

## What decided it

The industry analyst's Porter table, specifically the buyer-power row: three
coatings customers at 21% of segment revenue, up from 17% two years ago, with two
of them publicly evaluating insourcing. That finding is what holds the bear
probability at 25%, and the bear probability is the only input that moves this
call across a band edge. The bull's argument on margin trend is the stronger piece
of analysis in the debate and it does not change the rating, because a 140bp
margin improvement is worth $8 a share and the concentration risk is worth $36.

## The scenarios

| Case | Probability | Target | Basis |
|---|---|---|---|
| Bull | 25% | $138.00 | Margin reaches 21.0% by FY2029 and Dalton ramps on plan |
| Base | 50% | $112.00 | Revenue 5.0% fading to 3.0%, margin flat at 19.6% |
| Bear | 25% | $72.00 | Two coatings customers insource, taking 7.1% of revenue |

The bull weight stays at 25% rather than rising. The bull's margin case is
credible but it is an extrapolation of a decade-long trend into a decade of
forecast, and the same fundamentals file shows the trend flattening in the last
three years: 38bp, 28bp, 33bp of annual margin gain against 53bp early in the
series.

The bear weight stays at 25% rather than falling to the bull's 15%. The bull is
right that evaluating is not building. The bear is right that the disclosure
changed, and a risk factor added to a 10-K in the year two named customers start
evaluating is the company telling you the probability is no longer negligible.

## Where the debate landed

The bull won on the quality of the business and lost on what that is worth here.
Its strongest specific point, that incremental return on capital of 20.5% exceeds
the 15.1% historical average, is the best single fact in the run and it belongs in
the report's thesis. It moves the base case target by about $8.

The bear's central claim survives. Its arithmetic check on the valuation memo
found no error, which is worth recording: the terminal reinvestment rate and the
sensitivity grid both reconcile.

The bear's weakest point is the reading of the reverse discounted cash flow. A
45bp gap on terminal growth is not evidence that the market has priced a specific
customer loss; it is inside the noise on a beta estimate.

## How marginal

+10.7% against a +15.0% BUY edge, so 4.3 points inside the band and marginal by
the contract's own test. One input flips it: the bear probability. At 15% bear and
35% base the weighted target is $117.15 and the expected return is +19.4%.

Nothing else comes close. A 100bp change in WACC moves the target $9. A full point
of terminal operating margin moves it $6.

## Entry discipline

| Price | Action |
|---|---|
| Above $112 | No purchase. Above the base case. |
| $100 to $112 | Hold. No new capital at an expected return inside the band. |
| $92 to $100 | Start a position if the Q1 print on 2026-04-23 shows coatings volume flat or better. |
| Below $92 | Buy without waiting for the print, which is the discounted cash flow low end of $94.70 less a margin. |

## Ownership and conflicts

No position is held in ACME. The holdings snapshot is dated 2026-01-12 and shows
no line in this security.

## Disclaimer

Produced for educational and research purposes only. Not investment advice, not
an offer, and not a solicitation to buy or sell any security.
