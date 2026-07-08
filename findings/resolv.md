# Case study 2: Resolv / USR (March 22, 2026)

Treatment: **quantitative**. This is my own on-chain backtest against an
archive node.

## The incident

- Token: USR, `0x66a1E37c9b0eAddca17d3662D6c05F4DECf3e110` (Ethereum mainnet,
  verified contract)
- The attacker compromised Resolv's AWS KMS environment and got the
  SERVICE_ROLE signing key. With it they minted 80M unbacked USR in two
  transactions (50M, then 30M) against roughly $100-200K of USDC, because the
  contract had no on-chain check between deposited and minted amounts. USR
  depegged 80-97% within about 17 minutes.
- Exploit block: 24,710,031
- T-7 snapshot block: 24,659,218 (T-0 minus 50,813 blocks)

## The CPSE backtest

**Aave v3**: top 34 EOA USR holders checked, **0 USR positions**. This also
matches Aave's founder publicly confirming Aave had no USR exposure, which is
a nice independent cross-check on my scan.

**Morpho Blue**: over 70 USR/wstUSR markets found via Dune. I identified the
top ~100 wallets with positions (the biggest one around 114M USR on a single
market). Raw candidate list: `data/resolv/morpho_usr_raw.csv`. Note the word
raw: that file intentionally still contains contracts (including the Euler
vault address and the curator vault described below), because filtering
happens in the scripts, not in the export. See `data/README.md`.

**Euler v2**: USR vault `0x3A8992754E2EF51D8F90620d2766278af5C59b90`
(confirmed on app.euler.finance, the "Resolv cluster"). I cross-checked the
Morpho wallets against this vault: 34 of them had positions, but all of them
dust, between 1.09 and 217.78 USR, against multi-million USR positions on
Morpho. Value-wise that's a ratio around 0.005%, so I don't count it as a
CPSE signal. File: `data/resolv/euler_t7.csv`.

**Fluid**: not checked (time). And I have to be honest about how much that
matters here: Fluid/Instadapp reportedly absorbed over $10M of bad debt from
this incident and saw around $300M of outflows in a day. So the one venue I
skipped is one that was genuinely hit. It doesn't change my wallet-level
finding, but it's a real hole in coverage, not a footnote.

**CPSE result: effectively null** (dust only), after the corrections below.

## Two mistakes I made and caught

I'm documenting these on purpose.

**Mistake 1: wrong metric level.** My first pass computed "CPSE" over the
number of Morpho sub-markets per wallet. Three markets inside Morpho Blue is
not three protocols; Morpho markets are isolated by design, so intra-Morpho
concentration isn't cross-protocol risk at all. I corrected the metric to
count protocols. All numbers here use the corrected definition.

**Mistake 2: a contract disguised as the star finding.** Under the wrong
definition, wallet `0x14faa112a14b70328d2ca17102aafe398f0c369c` looked like
the largest CPSE finding of the whole project (65.7M). The is_contract()
check showed it's a contract, most likely a MetaMorpho-style curator vault,
not a person. Removed from the sample.

What bothers me in hindsight is that both mistakes pushed in the same
direction: toward the biggest, most publishable possible number. Both were
caught by boring mechanical checks. That's why those checks stay in the
pipeline permanently.

## The oracle detail that reframes the taxonomy

While verifying press coverage of this incident I ran into something
important: several Morpho vaults holding USR/wstUSR had the USR price
hardcoded to $1, before the incident, as a design choice, with no external
oracle and no circuit breaker. When USR crashed on secondary markets, those
vaults kept valuing it at $1, which meant collateral that the market had
already repriced could still back borrowing at face value. Around 15 Morpho
vaults were impacted.

Compare that with Stream/xUSD (see [stream.md](stream.md)), where protocols
hardcoded the price to $1 AFTER the depeg, deliberately, as a defense against
liquidation cascades. Same mechanism, opposite role: post-incident defense in
one case, pre-incident amplifier in the other. That contrast is now part of
the response taxonomy in [methodology.md](../methodology.md).

One more control-layer detail worth recording: Resolv's pause function
required a 4/4 multisig while minting depended on one key in AWS KMS. The
protocol had stronger safeguards for stopping itself than for creating money.

## What I take from this case

1. Shared-collateral exposure among top holders: effectively null. Large
   holders picked one venue (Morpho) and stayed there.
2. The contagion that did happen ran through venue design (hardcoded $1
   pricing) and curator vaults, not through wallet-level shared collateral.
3. The response was issuer-level (off-chain key compromise handled by the
   team), a structurally different mechanism from KelpDAO's on-chain freeze.
