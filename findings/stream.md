# Case study 3: Stream Finance / xUSD (November 3-6, 2025)

Treatment: **QUALITATIVE**. Unlike the KelpDAO and Resolv cases, I did NOT
run my own on-chain CPSE backtest here. The exposure figures below are cited
from external research, not reproduced by my pipeline. Please don't read the
numbers in this file with the same confidence as the other two case studies.
The reason for the downgrade is explained below, because the reason matters.

## The incident

- Token: xUSD, `0xe2fc85bfb48c4cf147921fbe110cf92ef9f26f94` (StreamVault
  contract, verified). Not a plain ERC-20: it's a LayerZero OFT token with
  round-based share accounting. balanceOf on lending protocols still behaves
  normally, which is what my checks would rely on.
- Timeline: depeg and collapse across November 3-6, 2025.
- Block estimates: T-0 around 23,713,289 and T-7 around 23,662,476 (my
  standard 50,813-block offset). Both are MANUAL estimates, I never resolved
  them with a proper block-by-timestamp lookup.

## What I did complete

- Verified the xUSD contract address and its non-standard architecture.
- Downloaded the holder export: 394 addresses.
- Tried to find the venue addresses I'd need for a real backtest:
  - Euler xUSD vault: not found, two search rounds.
  - Morpho xUSD market IDs: not found.

## Why I downgraded this case instead of pushing through

Without verified vault and market addresses, any CPSE number I computed would
sit on unverified infrastructure addresses. That is exactly the class of
error the rest of this project is about (see
[contamination.md](contamination.md)). Computing on guessed addresses to get
a third quantitative case would have been the same mistake I caught myself
making at Resolv, just one layer up. So this case is qualitative, and labeled
loudly.

## What the public record shows (cited, not mine)

The "Yields and More" research group documented roughly $285M of total
cross-protocol exposure to Stream, spread across Euler, Silo, Morpho and
Gearbox, through named curators including TelosC, Elixir, MEV Capital and
Varlamore.

Two things make this case useful to my thesis even without my own numbers:

1. **It's the counterexample in kind.** KelpDAO and Resolv showed near-zero
   shared collateral among top wallet holders. Stream shows meaningful
   cross-protocol exposure did exist, but it was routed through curators and
   vault infrastructure, which is exactly the contract-typed population that
   naive top-holder analysis misreads as individuals. The exposure was real;
   it just lives one layer above wallets.

2. **It adds the third response mechanism.** After the depeg, Morpho, Euler
   and Elixir deliberately hardcoded the xUSD oracle price to $1.00 to stop
   cascading liquidations. That's an intentional oracle override by protocols
   as a defensive move, distinct from KelpDAO's market freeze and Resolv's
   issuer-level response. Note the mirror image at Resolv, where hardcoded $1
   pricing existed BEFORE the incident and amplified the damage instead. See
   the taxonomy in [methodology.md](../methodology.md).

## Limitations specific to this case

- No independent backtest (the whole point of the banner above).
- Block heights are estimates.
- Exposure figures are cited from external research.
- Fluid not examined (consistent with the other two cases, unfortunately).
