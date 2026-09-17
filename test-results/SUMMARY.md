# Devnet test results

Two runs against a live Qubic devnet with Qpump deployed at contract index 30, driving the contract
through real transactions and reading state back with `querySmartContract`. Every number the contract
produced was cross-checked against an independent model of the curve
([`sim/qpump_model.py`](../sim/qpump_model.py)), not against the contract's own arithmetic.

| Run | Result | Log | Raw |
|---|---|---|---|
| Full lifecycle | **45 / 45 passed** | [qpump_comprehensive_test.log](qpump_comprehensive_test.log) | [json](qpump_comprehensive_results.json) |
| Concurrency stress | **32 / 32 passed** | [qpump_stress_test.log](qpump_stress_test.log) | [json](qpump_stress_results.json) |

## Full lifecycle run

Phases: launch, opening batch, curve trading, a real QU/QDOGE Qswap pool, a buyout to graduation, an
epoch transition, the idle refund path, and the QDOGE buyback.

What it proved:

- **The opening batch is uniform-price.** Three orders settled at one price, and each holder received
  exactly the share the independent model predicted (69,889,341 / 46,592,894 / 61,017,764 tokens).
- **The batch cap trims and refunds.** An over-cap order filled the batch to exactly 377,187,500 QU
  and the excess 69,040,623 QU was refunded.
- **Trading matches the formula exactly**, for `QuoteBuy`, an exact-token `Buy`, `QuoteBudget`,
  `BuyWithQu`, `QuoteSell`, `Sell` and `Transfer`. Contract and model agreed to the QU.
- **Graduation ran by itself, end to end:** the asset was issued, a Qswap pool opened with
  2,644,898,805 QU and 264,489,880 tokens at exactly 10 QU, holders received real QX-managed shares,
  and the permanent record was written with `poolFallback = 0` (no fallback needed).
- **A graduated ticker is blocked forever**, while a refunded one is freed: MOON expired after its
  9-epoch idle timeout, holders received pro-rata refunds, and the ticker was relaunched afterwards.
- **The QDOGE buyback fired for real:** the contract bought 932,111 QDOGE on Qswap, and that QDOGE is
  held by Qpump's own contract identity, locked as designed.
- **Rejected calls change nothing:** a zero-token buy and an underfunded buy were fully refunded with
  no state change.

## Concurrency stress run

5 coins, 30 wallets, with 10 wallets per coin landing trades in the same tick each round.

What it proved:

- **Concurrent trades in one tick settle correctly** across all five coins.
- **Three coins graduated in the same run**, and every one of the 10 concurrent traders on FLOKI
  received real QX-managed shares (10/10 delivered).
- **One coin refunded** after its idle timeout, with holders receiving nonzero pro-rata QU.
- **One coin stayed open** under continuous small trades, nowhere near completing its curve.
- **Final aggregates matched exactly:** 5 launched, 3 graduated, 1 refunded, 1 still live.

## Notes

- Identities in the logs are devnet test wallets. Transaction links point at the tester's local
  explorer.
- One test tolerance was widened during this work: refund dust is bounded by two chained
  floor-divisions (opening-batch tokens, then the pro-rata refund), not one. The dust stays in the
  contract's own balance and is never taken from any party.
