H1: Wallets/positions that share the same collateral asset across 2+ lending
protocols show a measurably higher Cross-Protocol Shared Exposure Score (CPSE)immediately before confirmed shadow-contagion events, compared to that protocol's baseline over the preceding 30-60 days.

H0 (null): CPSE does not differ meaningfully between the pre-incident window
and the baseline period. If true, this would mean shared-collateral exposure
has no predictive signal, and shadow contagion is not visible in advance
from collateral structure alone.

What this project does NOT claim:

- Causality. Even if CPSE is higher before an incident, this does not mean shared collateral CAUSES contagion - it may just be a symptom of the same underlying growth in DeFi composability. Correlation, not causation.

- Generalization. Two case studies (KelpDAO, Resolv) are not enough to claim
  this pattern holds for "DeFi in general." This is hypothesis-generating
  work, not a validated predictive model.

- Statistical significance. With n=2 events, no p-value or confidence interval is meaningful. Any comparison here is descriptive, not inferential statistics.

CPSE (Cross-Protocol Shared Exposure Score) for wallet w:

CPSE(w) = sum over each collateral asset a held by w:value(w, a) * (n_protocols(a, w) - 1)
where:
  value(w, a) = USD value of asset a that wallet w holds as collateral
  n_protocols(a, w) = number of protocols (from our set of 4) where w uses asset a as collateral

PPSE(protocol_A, protocol_B) = sum over all assets a:
    total_value_of_a_on(protocol_A)_that_overlaps_with(protocol_B)

Note on KelpDAO mechanism: the attacker's own wallet had zero pre-existing
exposure (the collateral was fraudulently minted at the moment of the
exploit, not accumulated beforehand). The T-7 CPSE test therefore targets
EXISTING, legitimate rsETH holders with cross-protocol positions - not the
attacker - since these are the wallets that bore the contagion once rsETH
markets froze. This actually broadens H1: CPSE aims to predict who is
exposed to cascade risk when a shared asset is disrupted, regardless of
whether the disruption is an exploit, a depeg, or a liquidity shock.
# Things That Didn't Work (or Didn't Work As Expected)

## KelpDAO: first pass at the Aave check used an incomplete sample - corrected

**What happened:** an early pass at this check used a partial candidate
list (10 hand-copied holders, only 8 of them EOAs) and concluded that
"only one wallet had any Aave collateral, and it was WETH not rsETH."
That conclusion was wrong - it was an artifact of the small sample, not a
real result. Once the full pipeline (`build_eoa_candidate_list`, scanning
all 73 Etherscan-export rows to find the true top-50 EOAs) was run
instead, wallet `0xf7462251...` showed up with 75,522 rsETH on Aave - one
of the largest single positions in the whole dataset, and confirmed to
have already existed at T-7 (see kelp.md).

**Lesson kept from this:** a "no signal found" result is only trustworthy
if the sample that produced it was actually complete. This is why
`build_eoa_candidate_list` keeps scanning until it has a real top_n of
EOAs (skipping contracts) rather than stopping at the first N raw rows -
see snapshot.py.

## Resolv: CPSE definition bug inflated the headline number - corrected

An earlier pass computed "CPSE" using the number of Morpho **sub-markets**
a wallet was active in, not the number of protocols. That's not the same
thing (Morpho Blue markets are isolated from each other by design), and
it produced a large, wrong, exciting-looking result - including flagging
a contract (`0x14faa112...`, likely a curator vault) as the project's
biggest individual finding. Both errors are written up properly in
findings/resolv.md and findings/contamination.md;
this note just records that the mistake happened and how it was caught
(market()-activity check for the sampling issue, is_contract() for the
contract-as-wallet issue).