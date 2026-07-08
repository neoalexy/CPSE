# How this project actually went

The findings changed shape three times. Each turn was forced either by data or
by literature, and I think the turns are more informative than the final
numbers, so here's the honest sequence.

## 1. I started with a falsifiable hypothesis

"Shadow contagion" is a phenomenon PeckShield named but nobody had quantified
at wallet level. I wrote H1 down before pulling any data, together with what I
was NOT claiming (no causality, no generalization, no significance at n=2),
and defined CPSE up front so that a null result would count as a result and
not as an excuse to move the goalposts.

## 2. I validated the pipeline before believing it

Before running the real sample I checked my script against independent
forensics: the KelpDAO attacker wallet came back 53,000.000000003 rsETH, which
matches the Innora.ai report to nine decimals. Only then did the top-holder
scans start.

## 3. I made two mistakes that would have manufactured my best finding

- A metric definition error (counting Morpho sub-markets as protocols)
  inflated the Resolv CPSE values.
- A contamination error made a curator vault contract look like the biggest
  individual finding of the project (65.7M).

Both errors pointed toward the most exciting possible result. Both were
caught by mechanical checks (the market() activity check and is_contract()).
I kept them in the writeup instead of silently fixing them, and the
contamination check itself became a finding: 20.1% across 174 candidates.

There was also a quieter bug: the Aave script hardcoded 18 decimals. It
happened not to matter (rsETH and WETH are both 18), but it made the "full
enumeration" claim bigger than the code deserved, so it's fixed and disclosed
in methodology.md.

## 4. I accepted the null result and asked what my method could even see

CPSE came back 0 (KelpDAO) and effectively null (Resolv). Instead of widening
the net until something showed up, I asked what the sampling frame was blind
to, and found two answers. First, rank-by-size sampling structurally excludes
the population most likely to diversify. Second, and this one I only
understood after checking press coverage against the chain: at KelpDAO the
dominant cross-protocol loss went through the attacker depositing freshly
minted rsETH on Aave and borrowing ~$195M against it. That collateral did not
exist at T-7, so no pre-incident wallet snapshot can see that channel, ever.
My null result and Aave's ~$177M bad debt are both true, which is exactly the
visibility point.

## 5. I let the literature set boundaries

Before extending into neighboring directions I checked what already exists:
Elem & Talmon (arXiv:2602.12260) on override efficiency across 705 incidents,
and arXiv:2206.00716 on upgradeability centralization. Where something was
covered, I dropped it instead of replicating it. Several citations suggested
by AI tools during this search turned out to be fabricated; each was checked
against arXiv directly before use, and the fakes were thrown out.

## 6. I scoped down when verification failed

For Stream/xUSD I couldn't verify the Euler vault or the Morpho market IDs
after two search rounds. The options were: compute on unverified addresses,
or downgrade the case to qualitative with cited external figures. I chose the
downgrade and labeled it loudly. A smaller honest case beats a bigger
unverifiable one.

## 7. I followed an anomaly instead of the plan

I located KelpDAO's pause transaction on-chain mostly to validate the press
timeline. The timing checked out (46.2 minutes), but the sender was a bare
EOA, not the "emergency pauser multisig" every outlet described. Chasing the
signer's authorization hit real limits (non-enumerable access control, RPC
block-range caps), so the discrepancy is published as an open finding. A
month later Aave rotated its Emergency Guardian to 4/7 and stopped naming the
signers, citing attack surface against individuals. The anomaly generalized.

## What I want this to show

Not that H1 was confirmed. It wasn't. What I care about is that the
measurement became trustworthy: contaminated inputs got quantified, a
seductive false positive got caught and disclosed, scope got cut where
verification failed, and a null result got converted into a precise statement
about what today's public data can and cannot show.
