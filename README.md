# Qpump

A bonding-curve token launchpad as a Qubic smart contract. Anyone pays a flat launch fee, a token
trades on a linear curve inside the contract, and when the curve sells out the contract issues the
real Qubic asset, opens and funds a Qswap pool, locks the liquidity and delivers every holder
automatically. No admin, no pause, no creator allocation.

It powers [The Yard](https://theyard.meme), part of the QDoge Protocol.

| File | What it is |
|---|---|
| [`contract/Qpump.h`](contract/Qpump.h) | The contract, written for [qubic/core](https://github.com/qubic/core) v1.304.0 |
| [`contract/contract_qpump.cpp`](contract/contract_qpump.cpp) | GoogleTest suite for the core test harness |
| [`qpump-core-v1.304.0.patch`](qpump-core-v1.304.0.patch) | Adds both to a core checkout, wired in at contract index 30 |
| [`sim/qpump_model.py`](sim/qpump_model.py) | Independent integer model of the economics, used to fuzz invariants and compute expected test values |
| [`test-results/`](test-results) | Logs and results from live devnet runs |

## Status

| Check | Result |
|---|---|
| Live devnet, full lifecycle | **45 / 45 passed** |
| Live devnet, concurrent stress run | **32 / 32 passed** |
| Official `qubic/contract-verify` | PASSED |
| Banned-token scan (brackets, quotes, `%`, `/`, `#`, `__`, native types) | Clean, comments included |
| Full `contract_def.h` build with Qpump at index 30 | No Qpump errors |
| Python fuzz of the money invariants, 3,000 randomized runs | Passes |

See [test-results/SUMMARY.md](test-results/SUMMARY.md) for what the devnet runs actually proved.

## How a token works

| Stage | Behavior |
|---|---|
| Opening batch | 1,200 ticks (about 5 minutes) where every order is pooled and settled at one average price, capped at a quarter of the curve. Being first gains nothing, so snipers and bots have no edge. |
| Curve | Linear, 1 QU to 10 QU per token over 710M tokens. A full curve raises 3,905,000,000 QU. |
| Graduation | The contract pays QX 1B QU to issue the 1B supply, pays Qswap 200M QU to create a pool, seeds ~2.64B QU and ~264M tokens at exactly 10 QU, then delivers every holder their tokens as QX-managed shares. The creator is paid a 50M QU reward and 10M QU is burned. |
| After graduation | The coin keeps a permanent read-only record, its ticker can never be launched again, and the asset trades on Qswap and QX. |
| Idle | A coin with no buys or sells for 9 epochs (about two months) refunds its holders pro-rata and frees its ticker. There is no age limit. |

## Fees

| Source | Split |
|---|---|
| Launch, 25M QU | 20M to Qpump shareholders, 5M burned into the execution reserve |
| Trade, 1% (minimum 1,000 QU) | 70% shareholders, 20% burned, 10% buys QDOGE on Qswap and locks it in the contract |
| Transfer, 100 QU flat | Burned |
| Graduation | 50M QU creator reward, 10M QU burned, from the raise |

There are no minimum buys, no minimum balances and no per-holder fees: any amount can be bought,
sold or transferred.

## Interface

| Type | Id | Name | Notes |
|---|---|---|---|
| Procedure | 1 | CreateCoin | Launch fee 25M QU; anything above it becomes the creator's opening order |
| Procedure | 2 | Buy | Exact token count, attached QU is the most you pay |
| Procedure | 3 | Sell | Only while the coin is on the curve |
| Procedure | 4 | Process | Permissionless: settles a batch, expires a coin, retries graduation or pushes payouts |
| Procedure | 5 | Claim | Collect your own delivery or refund |
| Procedure | 6 | Transfer | Move curve tokens for a flat 100 QU |
| Procedure | 7 | BuyWithQu | Spend an exact QU amount, with a minimum token count for slippage |
| Function | 1-9 | GetCoin, GetHolder, QuoteBuy, QuoteSell, QuoteBudget, GetFees, ListCoins, GetStats, ListGraduated | Read-only |

Every state change emits an event carrying the contract index, coin name and id, actor, QU, tokens,
the coin's raised QU and tokens sold, the holder count, the trade fee and a counterparty id.

## Build and test

```bash
git clone https://github.com/qubic/core.git && cd core && git checkout v1.304.0
```

```bash
git apply ../qpump-core-v1.304.0.patch
```

Then open `Qubic.sln`, build the `test` project in Release x64 and run:

```bash
test.exe --gtest_filter=ContractQpump.*
```

The `contractDescriptions` entry uses construction epoch 234 as a placeholder. On a testnet, set it
to an epoch at or below the current one so the contract is active.

## Limits and storage

32,768 live coins, 65,536 permanent graduated records, 10 live coins per creator at a time (a slot
frees when a coin graduates or refunds, so there is no lifetime limit), 3,355,443 holder positions
and 838,860 wallets. Contract state is 238,502,104 bytes, well under Qubic's 1 GB limit, sized up
front so no migration is needed as usage grows.

## Known limitations

- **Rounding dust stays with the contract.** Splitting the opening batch and refunds pro-rata leaves
  a few units behind; they are never lost to any party.
- **Unused delivery budget is burned.** If QX's transfer fee rises before every holder is delivered,
  holders can still collect with `Claim` by attaching the fee.
- **One graduated ticker per name**, since every graduated asset is issued by the contract.
- **Pool liquidity is locked for good.** The Qswap position belongs to the contract, which has no
  withdraw path, so its fee share compounds into the pool.

## Licence

[MIT](LICENSE).
