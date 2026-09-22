# Qpump

**A fair launchpad for meme coins on Qubic.** Anyone can create a token for 25,000,000 QU instead of
the 1,000,000,000 QU it normally costs, and the smart contract handles everything else by itself.

It powers **[The Yard](https://theyard.meme)**, part of the QDoge Protocol. Submitted to Qubic core
as [PR 1010](https://github.com/qubic/core/pull/1010).

## The problem

Creating an asset on Qubic costs 1,000,000,000 QU. That's fine for a serious project and absurd for
a meme coin, where most attempts are worth nothing and the fun is in trying.

## How Qpump solves it

While a token is finding its feet, balances live **inside the contract**. Nothing is issued, so a
launch costs 25,000,000 QU, 40 times less. Only when a token sells out does the contract pay the full
issuance fee and create the real asset, out of the money that token raised.

## A token's life

| Stage | What happens |
|---|---|
| **Create** | Pick a ticker, name and image. Pay the launch fee |
| **Entry batch** | For ~5 minutes, every buyer pays the same price. Being fast wins nothing, so bots have no edge |
| **Trading** | The price rises along a fixed line from 1 QU to 10 QU per token as people buy |
| **Graduation** | All 710M tokens sold. The contract takes over |
| **Free market** | The token trades on Qswap and QX with no ceiling |

## What graduation does, with no help from anyone

A full curve raises 3,905,000,000 QU. The contract spends it, in this order:

1. **1,000,000,000 QU to QX**, which creates the real token, 1 billion supply
2. **~200,000,000 QU to Qswap**, which opens the trading pool
3. **~2,644,000,000 QU and ~264M tokens into that pool**, locked **forever** — there is no function
   to take it out
4. **200 QU per holder** to deliver everyone their tokens automatically. Nobody claims, nobody pays
5. **50,000,000 QU to the creator**, and **10,000,000 QU burned**

## Why it's fair

- **No creator allocation.** Creators buy at the same price as everyone else, or not at all
- **No admin.** No pause button, no fee changes, no withdrawals, no upgrades. Nobody can touch it
- **Liquidity can't be pulled.** The pool belongs to the contract, which cannot move it
- **Dead tokens refund.** If nobody trades for about two months, holders get their QU back and the
  ticker is freed
- **No minimums.** Buy, sell or transfer any amount
- **Nowhere for money to leak.** Fees only ever reach shareholders, the QDOGE buyback, or the
  contract's own fuel. There is no team wallet and no withdrawal function

## Fees

| When | How much | Where it goes |
|---|---|---|
| Creating a token | 25,000,000 QU | 20M to shareholders, 5M burned |
| Every buy and sell | 1%, at least 1,000 QU | 70% shareholders, 20% buys QDOGE, 10% burned |
| Sending tokens to someone | 100 QU | Burned |

**Shareholders** are whoever holds Qpump contract shares; the contract pays them every epoch.
**Burned** means the QU goes into the contract's own execution reserve, which pays Qubic for running
it — not to any person. The **QDOGE** is bought on Qswap once per epoch and stays in the contract,
which has no way to move it.

Fees are charged on top of the price, never skimmed out of the curve, and the 1,000 QU minimum is a
floor on the fee rather than a minimum trade. No platform wallet takes a cut of anything.

## Does it work?

Tested on a live Qubic devnet, driving the real contract with real transactions:

- **45 of 45** lifecycle tests passed, including a real graduation into a real Qswap pool
- **32 of 32** stress tests passed, with 30 wallets trading 5 tokens at once
- Passes Qubic's official `contract-verify` tool
- Every number was checked against [an independent model](sim/qpump_model.py), not against the
  contract's own maths

Details: [test-results/SUMMARY.md](test-results/SUMMARY.md)

## What's in here

| File | What it is |
|---|---|
| [`contract/Qpump.h`](contract/Qpump.h) | The contract |
| [`contract/contract_qpump.cpp`](contract/contract_qpump.cpp) | Its test suite |
| [`qpump-core-v1.304.0.patch`](qpump-core-v1.304.0.patch) | Adds both to a Qubic core checkout |
| [`sim/qpump_model.py`](sim/qpump_model.py) | Independent model of the economics |
| [`test-results/`](test-results) | Devnet logs and results |

## Build and test it yourself

```bash
git clone https://github.com/qubic/core.git && cd core && git checkout v1.304.0
```

```bash
git apply ../qpump-core-v1.304.0.patch
```

Open `Qubic.sln`, build the `test` project in Release x64, then:

```bash
test.exe --gtest_filter=ContractQpump.*
```

## Good to know

- **Every token graduates at the same price**, 10 QU. A popular token gets there faster, not higher.
  Its price can go anywhere afterwards
- **New pools start small**, so early trades move the price a lot
- **A graduated ticker is taken forever.** A refunded one can be used again
- **Rounding leftovers stay in the contract**, never taken from anyone

The site and backend are closed source; available on request.

Licence: [MIT](LICENSE).
