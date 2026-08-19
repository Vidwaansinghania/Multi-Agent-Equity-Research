---
method: 2
ticker: <TICKER>
exchange: <EXCHANGE>
company: <legal name>
run_date: <YYYY-MM-DD>
reference_price: <price>
price_date: <YYYY-MM-DD>
rating: <BUY | HOLD | SELL>
target: <price>
target_horizon_months: 12
expected_total_return: <decimal, dividends included>
conviction: <low | moderate | high>
marginal: <true | false>
flip_assumption: >
  <The one assumption that moves the call to the neighbouring band, at its value in
  the memo, with the target and expected return it produces at the changed value.>
decided_by: <fundamentals | market | news | industry | valuation | bull | bear>
scenarios:
  bull:  { probability: <p>, target: <price> }
  base:  { probability: <p>, target: <price> }
  bear:  { probability: <p>, target: <price> }
position: null
models:
  analysts: <model>
  decision: <model>
  report: <model>
alpha_vantage_calls: <total across every connector>
---

# Decision — <TICKER>, <YYYY-MM-DD>

## The call

<Rating, target, expected total return, conviction, in three sentences. Someone
reading only this should be able to act.>

## What decided it

<The analyst finding or the side of the debate that carried the decision, named.>

## The scenarios

| Case | Probability | Target | Basis |
|---|---|---|---|
| Bull | <p> | <price> | <one line> |
| Base | <p> | <price> | <one line> |
| Bear | <p> | <price> | <one line> |

<A paragraph on each weight, defending it.>

## Where the debate landed

<Both attacks, including the one rejected and the reason. Name the strongest specific
point on each side.>

## How marginal

<Distance to the band edge, the flipping assumption, and the sensitivity numbers. What
else was checked and did not come close.>

## Entry discipline

| Price | Action |
|---|---|
| Above <price> | <action> |
| <range> | <action> |
| Below <price> | <action> |

## Ownership and conflicts

<The position as fact from the snapshot: company, share count, share of portfolio,
snapshot date. Nothing about bias. Where there is no position, say so and give the
snapshot date.>

## Disclaimer

Produced for educational and research purposes only. Not investment advice, not an
offer, and not a solicitation to buy or sell any security.
