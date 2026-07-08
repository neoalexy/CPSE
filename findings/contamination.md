# Finding: 20.1% of "top holder" candidates are infrastructure, not people

## The claim

Across the two quantitative case studies, **35 of 174 (20.1%)** candidate
addresses from public token holder exports turned out to be smart contracts
presenting as individual holders: aTokens, bridge escrows, protocol
singletons, curator vaults. All caught with a single bytecode check
(eth_getCode) before any exposure math ran.

| Holder list | Candidates scanned | Contracts | Contamination |
|---|---:|---:|---:|
| rsETH (KelpDAO) | 73 | 23 | 31.5% |
| USR (Resolv) | 101 | 12 | 11.9% |
| combined | 174 | 35 | **20.1%** |

## Why I think this matters beyond my project

Holder-derived metrics (concentration, top-10 share, "whale" counts,
decentralization scores) get consumed directly by exchange listing and risk
pipelines and by protocol analytics. If about one in five candidate addresses
is infrastructure rather than an economic actor, every metric built on the
raw export inherits the error. And the direction of the error depends on the
contract type: a curator vault hides thousands of users behind one address
(real concentration is lower than it looks), while an escrow or a singleton
represents no user at all (real concentration is higher than it looks).

## Why the check stays in the pipeline

`is_contract()` is a one-line, single-RPC-call check. There's nothing clever
about it. The reason it's worth mentioning at all is what it caught: in an
earlier pass on Resolv, wallet `0x14faa112a14b70328d2ca17102aafe398f0c369c`
looked like the largest CPSE finding in the project (65.7M). It's a contract,
most likely a MetaMorpho-style curator vault, not a person. Once excluded,
that number disappeared. The check itself is trivial; skipping it is what's
costly.

## Method

For each candidate address from a holder export:

1. eth_getCode(address) at the snapshot block.
2. Non-empty bytecode: classified as a contract, excluded from the EOA
   sample, counted in the contamination tally.
3. Empty bytecode: kept as an EOA candidate.

This is deliberately the cheapest possible filter, one RPC call per address.
That's kind of the point: the contamination is trivially detectable, and
apparently still not routinely detected upstream.

Small caveat for completeness: empty bytecode at the snapshot block doesn't
strictly guarantee an EOA (counterfactual addresses exist), but that error is
rare and conservative for this analysis.

## About the data files

`data/kelp/rseth_holders_etherscan.csv` is the raw Etherscan export (23k+
rows). The script scans it top-down, skipping contracts, until it has 50 real
EOAs; those land in `data/kelp/eoa_master.csv`.

`data/resolv/morpho_usr_raw.csv` is the raw Morpho candidate list (101
addresses) and it INTENTIONALLY still contains contracts, including the Euler
USR vault address and the 0x14faa112 curator vault mentioned above. Filtering
happens in the scripts, not in the export, so the raw file stays as evidence
of what the unfiltered list looks like. The contamination table above counts
all 101 candidates in that file.

## Who should care

Anyone consuming holder data: exchange risk teams, asset listing processes,
analytics dashboards. The filter costs one archive RPC call per address.
