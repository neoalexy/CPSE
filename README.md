# [CPSE] - Cross-Protocol Shared Exposure

I set out to measure whether "shadow contagion" in DeFi lending spreads through
wallets that hold the same collateral on multiple protocols. Short answer: at
least among the biggest holders, it doesn't. The longer answer turned out to be
more interesting than the hypothesis, and it's about visibility.

## The main idea I ended up with

Before anyone can measure systemic risk in DeFi, they need to be able to
reliably see who holds what and who controls what. Right now you often can't:

- Public "top holder" lists are contaminated with infrastructure pretending to
  be individuals. In my samples, **20.1%** of candidate addresses were smart
  contracts (aTokens, bridge escrows, curator vaults), not people.
- Methods that look for shared risk sample the largest holders, which is
  exactly the population least likely to show it (big holders concentrate on
  one venue for better rates and simpler monitoring).
- The press narrative about who controls emergency powers doesn't match the
  chain. KelpDAO's pause, described everywhere as an "emergency pauser
  multisig", was executed by a bare EOA.
- And the industry is moving toward less transparency here, not more. One
  month after KelpDAO, Aave rotated its Emergency Guardian to a 4/7 setup and
  stopped publicly naming the signers, citing attack surface against
  individuals ([governance post](https://governance.aave.com/t/aave-emergency-guardian-protocol-signer-rotation/24944)).

So: DeFi has a risk **visibility** problem before it has a proven risk
**existence** problem.

## What I actually tested

H1: wallets sharing the same collateral asset across 2+ lending protocols
(Aave v3, Morpho Blue, Euler v2, Fluid) show elevated CPSE right before
confirmed contagion events, compared to a 30-60 day baseline.

CPSE(w) = sum over assets a of: value(w, a) * (n_protocols(a, w) - 1)

I tested this with block-level T-7 snapshots on an archive node, on two
incidents, plus a third incident treated qualitatively:

| Case | What happened | Treatment | CPSE result |
|---|---|---|---|
| [KelpDAO / rsETH](findings/kelp.md) (Apr 2026) | 116,500 rsETH forge-minted through a 1-of-1 DVN bridge config, ~$292M | quantitative | **0** - none of the top 50 EOA holders had rsETH on both Aave and Morpho at T-7 |
| [Resolv / USR](findings/resolv.md) (Mar 2026) | 80M USR minted with a compromised AWS KMS key, depeg within 17 min | quantitative | **effectively null** - only dust-level Euler overlap (~0.005% of the Morpho positions) |
| [Stream / xUSD](findings/stream.md) (Nov 2025) | collapse with ~$285M cross-protocol exposure (cited from external research, not my backtest) | qualitative | not independently tested. Exposure existed, but it lived in curator vaults, not wallets |

## The three findings

**1. Holder data is contaminated (20.1%).** 35 of 174 candidate addresses from
Etherscan holder exports were contracts, not individuals. One of them briefly
looked like the biggest finding of the whole project until an is_contract()
check caught it. Details in [findings/contamination.md](findings/contamination.md).

**2. The null result, and why the method couldn't have seen the real contagion
anyway.** Both quantitative cases came back null at the wallet level. Partly
that's sampling: rank-by-size selects holders who rationally concentrate. But
KelpDAO also showed a channel that no T-7 snapshot can see by definition: the
attacker deposited the freshly minted rsETH on Aave and borrowed roughly $195M
of WETH against it, leaving Aave with ~$177M of bad debt. That collateral
didn't exist at T-7, so no pre-incident wallet scan could have caught it. See
[findings/kelp.md](findings/kelp.md).

**3. Guardian transparency is degrading.** The KelpDAO pause came from an
unattributable EOA, the pause authority on LRTConfig can't be enumerated with
standard tooling, and Aave then stopped naming its Guardian signers entirely.
Who holds the pause keys is getting harder to verify on purpose. See
[findings/kelp.md](findings/kelp.md).

Across the three cases I also ended up with a small taxonomy of how protocols
respond to a compromised collateral asset (market freeze, issuer response,
oracle hardcoding), including the odd detail that oracle hardcoding shows up
once as a defense (Stream) and once as a damage amplifier (Resolv). That's in
[methodology.md](methodology.md).

## Repo map

```
README.md            this file
methodology.md       hypotheses, CPSE definition and its correction, pipeline, limitations
process.md           how the project actually went, including the mistakes
notes.md             my raw working notes, kept as-is
findings/
  contamination.md   the 20.1% finding
  kelp.md            KelpDAO case study (quantitative)
  resolv.md          Resolv case study (quantitative)
  stream.md          Stream/xUSD case study (qualitative, clearly marked)
src/
  snapshot.py        Aave v3 checker (bitmap position enumeration)
  morpho_snapshot.py Morpho Blue checker
  euler_snapshot.py  Euler v2 checker (ERC-4626)
  find_pause.py      attempt to enumerate LRTConfig role holders (it can't, which is the point)
data/                inputs and outputs, see data/README.md
```

## Limitations, honestly

Two case studies isn't enough for statistical significance, and I don't
claim it is. Full list of gaps and estimates is in
[methodology.md](methodology.md).

One more thing: several addresses and citations suggested by AI tools during
this project turned out to be wrong or made up. Every address, tx hash and
citation in this repo was checked against a primary source before use.
