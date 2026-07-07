# Data files

What each file is and where it came from. Raw inputs stay raw on purpose;
filtering happens in the scripts so the process is reproducible.

## kelp/ (KelpDAO / rsETH, T-7 block 24,857,472)

- **rseth_holders_etherscan.csv** - raw Etherscan holder export for rsETH
  (23k+ rows). Input. Contains contracts, tags, formatted balances, the works.
- **eoa_master.csv** - the top 50 EOA candidates after the is_contract()
  filter. Built by src/snapshot.py from the export above (it scanned 73 rows
  to find 50 real wallets, 23 were contracts). This list is the source of
  truth for who was checked on every venue.
- **aave_t7_full.csv** - full Aave v3 collateral positions for the 50 wallets
  at T-7. 5 rows, 4 wallets: 2 rsETH positions, 2 WETH positions, and 1 USDC
  position ($646,170) that only appeared after the decimals fix in
  src/snapshot.py - the old hardcoded-18-decimals version silently dropped
  it as dust.
- **aave_t7_test.csv** - pipeline validation run, includes the attacker
  wallet (53,000.000000003 rsETH, matches Innora.ai to 9 decimals). Not part
  of the sample, kept as evidence of the validation step.
- **morpho_t7.csv** - Morpho Blue rsETH positions for the same 50 wallets.
  Empty except the header. That's the result, not a bug: 0 of 50.

## resolv/ (Resolv / USR, T-7 block 24,659,218)

- **morpho_usr_raw.csv** - RAW candidate list of 101 addresses with Morpho
  USR positions, found via Dune. Intentionally unfiltered: it still contains
  contracts, including the Euler USR vault address and the 0x14faa112 curator
  vault that briefly looked like the project's biggest finding (see
  findings/contamination.md). The scripts filter it; the file documents what
  the unfiltered world looks like.
- **euler_t7.csv** - Euler v2 USR vault positions for those candidates at
  T-7, after the contract filter. 34 wallets, all dust (1.09 to 217.78 USR).

## Not in this repo

The Resolv Aave check (top 34 EOA USR holders, zero positions) was run as a
spot check with src/snapshot.py's single-asset mode and returned no rows;
there was nothing to save beyond the empty result, which is reported in
findings/resolv.md.
