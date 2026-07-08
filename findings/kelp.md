# Case study 1: KelpDAO / rsETH (April 18, 2026)

Treatment: **quantitative**. This is my own on-chain backtest against an
archive node.

## The incident

- Token: rsETH, `0xA1290d69c65A6Fe4DF752f95823fae25cB99e5A7`
- 116,500 rsETH (~$292M, roughly 18% of circulating supply) minted through a
  forged LayerZero cross-chain message. Root cause was a 1-of-1 DVN
  configuration on the bridge path, so a single compromised verifier was
  enough.
- Exploit block: 24,908,285
  (tx `0x1ae232da212c45f35c1525f851e4c41d529bf18af862d9ce9fd40bf709db4222`)
- T-7 snapshot block: 24,857,472 (T-0 minus 50,813 blocks)

## Checking my pipeline before trusting it

The attacker wallet `0x1F4C1c2e610f089D6914c4448E6F21Cb0db3adeF` returned
53,000.000000003 rsETH from my script, which matches the Innora.ai forensic
report to nine decimal places. Only after that did I run the real sample.

## The CPSE backtest

Sample: top 50 EOA rsETH holders at T-7, built from a 73-address Etherscan
export after removing 23 contracts (31.5% of the list, see
[contamination.md](contamination.md)). File: `data/kelp/eoa_master.csv`.

**Aave v3** (full bitmap position enumeration): exactly **2 wallets held
rsETH as collateral** at T-7:

- `0xf7462251...` with 75,522 rsETH. I checked this one against the
  post-incident state too: 75,522 at T-7 vs 75,774 after, nearly identical,
  so this was a long-standing position, not incident-driven flow.
- `0x1a515961...` with 65 rsETH.

The enumeration also surfaced a WETH position for `0x267ed5f7...` and, after
the decimals fix described in methodology.md, a **$646,170 USDC position**
for `0x084caf1b...` that the old hardcoded-18-decimals bug had crushed to
`6.46e-07` and silently dropped as dust. Those rows are in
`data/kelp/aave_t7_full.csv` for completeness. To be precise: **5 rows, 4
wallets, 2 rsETH positions.** (An earlier draft said "4 rows, 3 wallets" —
that was correct against the code at the time, but the decimals fix changed
the actual output on re-run, so the count is updated here rather than
silently left stale.) None of this changes the CPSE result: USDC isn't the
asset under test, so this wallet still doesn't contribute a cross-protocol
rsETH signal.

**Morpho Blue**: 5 rsETH markets found via Dune, only 1 of them meaningfully
active at T-7 (545.7 rsETH total supply). Result: **0 of the 50 wallets** had
a position. File: `data/kelp/morpho_t7.csv` (empty on purpose, that IS the
result).

**Euler v2**: not checked. The rsETH vault is no longer visible in the Euler
UI (probably delisted after the incident). Documented limitation.

**Fluid**: not checked (time). Documented limitation.

**CPSE result: 0.** No top-50 EOA rsETH holder had a cross-protocol
(Aave + Morpho) rsETH position at T-7.

## Where the contagion actually went

This is the part that reframed the project for me. The real cross-protocol
damage at KelpDAO didn't come from legitimate holders with shared collateral.
It came from two other places:

**1. The attacker's own freshly minted collateral.** The attacker deposited
the forged rsETH on Aave and borrowed roughly 82,600 WETH (about $195M)
against it, leaving Aave with an estimated $177M of bad debt. A T-7 wallet
snapshot cannot see this channel even in principle: the collateral did not
exist yet. So on top of the sampling bias issue (see methodology), there's a
whole contagion class that pre-incident wallet-level scans are structurally
blind to. My null result and Aave's very real loss are both true at the same
time, and that's the point.

**2. Market freezes.** Aave, SparkLend and Fluid froze their rsETH markets
within hours, spreading the disruption to every rsETH holder on those venues
regardless of what the exploit itself touched.

## Bonus finding: the pause that doesn't match the press

I located the emergency pause directly on-chain:

- Pause tx: `0x4f52256ab6c8ab95d30cf994e0264f1de27e089764bb011824d5ddd47d9a1698`,
  block 24,908,516, which is 231 blocks after the exploit, so **46.2 minutes**
  (231 x ~12s). This matches the press timeline exactly.
- The sender is a plain EOA, `0xFCc1C98F887C93C38Deb5e38A6Fb820AD3fB9DFD`,
  calling LRTConfig (`0xb6AbB489aCA4583833230F10B3A7670114D09559`) directly.
  It is NOT a Safe execTransaction call.

That contradicts basically every news write-up (KuCoin, CoinDesk, The Block,
Messari), which all describe an "emergency pauser multisig".

I tried to resolve who this EOA is authorized by:

- LRTConfig doesn't implement AccessControlEnumerable, so
  getRoleMemberCount / getRoleMember revert (that attempt is in
  `src/find_pause.py`).
- An eth_getLogs sweep for RoleGranted events died on my RPC provider's
  block-range limit (roughly 200-300 blocks per call, so millions of blocks
  back is not realistic on my tier).

So the signer identity stays **unresolved**, and I'm leaving it that way as an
open finding rather than pretending otherwise. The fact that a motivated
person with an archive node cannot cheaply answer "who held the pause key" is
itself evidence for the visibility thesis. A month later, Aave rotated its
Emergency Guardian to 4/7 and stopped naming the signers publicly, citing
attack surface against individuals
([governance post, May 20, 2026](https://governance.aave.com/t/aave-emergency-guardian-protocol-signer-rotation/24944)),
which reads like independent confirmation of the same trend.

## What I take from this case

1. Shared-collateral contagion among top holders: not observed (CPSE = 0).
2. The actual contagion ran through attacker-injected collateral (invisible
   at T-7 by definition) and market freezes, not through pre-existing shared
   positions.
3. The public story about who executed the freeze doesn't match the chain,
   and the chain alone can't currently resolve it.
