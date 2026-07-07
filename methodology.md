# Methodology

## Hypotheses

H1: wallets that share the same collateral asset across 2+ lending protocols
(Aave v3, Morpho Blue, Euler v2, Fluid) show a measurably higher CPSE right
before confirmed shadow-contagion events, compared to that asset's baseline
over the preceding 30-60 days.

H0: CPSE does not differ meaningfully between the pre-incident window and the
baseline period.

### CPSE definition

For a wallet w:

```
CPSE(w) = sum over each collateral asset a held by w:
          value(w, a) * (n_protocols(a, w) - 1)
```

where n_protocols(a, w) is the number of distinct **protocols** where w uses
asset a as collateral.

**Correction (v2).** My first Resolv analysis counted Morpho Blue sub-markets
toward n_protocols. That's wrong by my own definition: Morpho Blue markets are
deliberately isolated from each other, so three positions inside Morpho is one
protocol, not three. All numbers in this repo use the corrected definition.
The mistake and how I caught it are documented in [findings/resolv.md](findings/resolv.md),
on purpose, because silently fixing it felt worse than admitting it.

### What I am NOT claiming

- Causality. Even if CPSE were elevated before an incident, that wouldn't mean
  shared collateral causes contagion.
- Generalization. Two quantitative case studies don't say anything about
  "DeFi in general". This is hypothesis-generating work.
- Statistical significance. With n=2 there are no meaningful p-values and I
  don't report any.

## Snapshot design

- T-0 is the exploit block of each incident.
- T-7 is T-0 minus 50,813 blocks (about 7 days at ~7,259 blocks/day, sanity
  checked in scratch.ipynb). The same offset is used for all three cases.
- All position reads go against an archive node at the exact snapshot block.

## Pipeline

Python + web3.py against an Ankr archive RPC. Etherscan for holder exports,
Dune for market discovery.

- **src/snapshot.py** (Aave v3): getReserveData() for the aToken address,
  getUserConfiguration() bitmap to enumerate all collateral positions per
  wallet without guessing assets, dust threshold, is_contract() filter.
- **src/morpho_snapshot.py** (Morpho Blue): position(marketId, wallet) on the
  singleton, with a market() activity check first, so a zero result isn't
  trusted before confirming the market wasn't just empty.
- **src/euler_snapshot.py** (Euler v2): ERC-4626 pattern, balanceOf +
  convertToAssets.
- **is_contract()**: eth_getCode on every holder-export candidate before it
  enters the EOA sample. See [findings/contamination.md](findings/contamination.md).

### Known code issue, fixed

The first version of the Aave script hardcoded 18 decimals when converting
balances. I originally believed this didn't affect any published numbers,
since rsETH and WETH are both 18 decimals. That was wrong: re-running the
fixed script surfaced a $646,170 USDC position (`0x084caf1b...`) that the old
code had silently crushed to dust (`6.46e-07`) and dropped. So the fix DID
change a published number, from 4 rows/3 wallets to 5 rows/4 wallets in
[findings/kelp.md](findings/kelp.md). It did not change the CPSE result,
since USDC isn't the asset under test. I'm leaving both the original mistaken
claim and this correction in, rather than quietly editing the first version
away, for the same reason everything else in this section is disclosed.

### Pipeline validation

Before trusting any of my own numbers I checked the pipeline against
independent forensics: the KelpDAO attacker wallet returned
53,000.000000003 rsETH, which matches the Innora.ai incident report to nine
decimal places.

## Sampling, and its built-in bias

Candidates come from public holder exports ranked by size. That has a
consequence I only fully appreciated after the null results: the largest
holders have every reason to concentrate on a single venue (better rates, less
gas, simpler monitoring), so rank-by-size sampling selects exactly the
population least likely to diversify across protocols. If a CPSE signal
exists, it's more likely among mid-size holders. I didn't test that; it's
future work, not a claim.

## Case treatment tiers

| Case | Treatment | What that means |
|---|---|---|
| KelpDAO (Apr 2026) | quantitative | my own on-chain backtest with this pipeline |
| Resolv (Mar 2026) | quantitative | my own on-chain backtest with this pipeline |
| Stream/xUSD (Nov 2025) | qualitative | I could not verify the venue addresses, so exposure figures are cited from external research and clearly labeled as such |

Numbers from the qualitative tier are never mixed with numbers from the
quantitative tier.

## Response mechanism taxonomy

When a collateral asset gets compromised, protocols respond in structurally
different ways, and the response is where I actually saw cross-protocol
coupling, not in shared wallet collateral:

- **Market freeze** (KelpDAO): on-chain emergency pause 46.2 minutes after the
  exploit, executed by a bare EOA despite the uniform press description of a
  multisig. Aave, SparkLend and Fluid froze their rsETH markets within hours.
- **Issuer/team response** (Resolv): an off-chain key compromise handled at
  the issuer level. A detail I like: Resolv's pause needed a 4/4 multisig
  while the mint depended on a single key, so the protocol had stronger
  protection for stopping itself than for printing money.
- **Oracle hardcoding** (Stream/xUSD): Morpho, Euler and Elixir pinned the
  xUSD price to $1.00 after the depeg, deliberately, to stop cascading
  liquidations.

One twist worth flagging: the same mechanism appears twice with opposite
roles. At Stream, hardcoding the oracle was a post-incident defense. At
Resolv, Morpho vaults had the USR price hardcoded to $1 before the incident
as a design choice, which is part of why the damage propagated (borrowing
against a token the market had already repriced). Same lever, defense in one
case, amplifier in the other.

## Verify before use

More than once during this project, addresses and citations produced by AI
tools were wrong: fake arXiv IDs, a testnet address presented as mainnet, a
wrong chain address for USR. My rule became: no address, tx hash or citation
goes into this repo without being checked against a primary source (block
explorer, verified contract, or the paper itself). The contamination finding
is really the same rule applied to holder data.

## Limitations

- n = 2 quantitative case studies.
- Fluid never checked, for any case. This matters: Fluid reportedly took over
  $10M of bad debt in the Resolv incident, so it's a real blind spot in my
  coverage, not a technicality.
- KelpDAO x Euler check skipped (vault delisted after the incident).
- Stream/xUSD block heights are manual estimates, and the whole case is
  qualitative.
- The KelpDAO pause signer is unresolved: LRTConfig doesn't expose enumerable
  roles and a historical RoleGranted log sweep wasn't feasible on my RPC tier
  (block-range limits). Documented as an open finding in [findings/kelp.md](findings/kelp.md).
- Aave's Guardian details changed after my analysis window: the documented
  5/9 setup was rotated to 4/7 with unattributed signers in May 2026.
