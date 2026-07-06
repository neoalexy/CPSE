import os
import csv
from web3 import Web3
from dotenv import load_dotenv

load_dotenv()
w3 = Web3(Web3.HTTPProvider(os.getenv("ANKR_RPC_URL")))

AAVE_POOL = "0x87870Bca3F3fd6335C3F4ce8392D69350B4fA4E2"

# min token units to keep -filters dust positions
DUST_THRESHOLD = 0.01

POOL_ABI = [
    {
        "inputs": [{"name": "asset", "type": "address"}],
        "name": "getReserveData",
        "outputs": [{"components": [
            {"name": "configuration", "type": "tuple", "components": [{"name": "data", "type": "uint256"}]},
            {"name": "liquidityIndex", "type": "uint128"},
            {"name": "currentLiquidityRate", "type": "uint128"},
            {"name": "variableBorrowIndex", "type": "uint128"},
            {"name": "currentVariableBorrowRate", "type": "uint128"},
            {"name": "currentStableBorrowRate", "type": "uint128"},
            {"name": "lastUpdateTimestamp", "type": "uint40"},
            {"name": "id", "type": "uint16"},
            {"name": "aTokenAddress", "type": "address"},
            {"name": "stableDebtTokenAddress", "type": "address"},
            {"name": "variableDebtTokenAddress", "type": "address"},
            {"name": "interestRateStrategyAddress", "type": "address"},
            {"name": "accruedToTreasury", "type": "uint128"},
            {"name": "unbacked", "type": "uint128"},
            {"name": "isolationModeTotalDebt", "type": "uint128"},
        ], "name": "", "type": "tuple"}],
        "stateMutability": "view", "type": "function"
    },
    {
        "inputs": [],
        "name": "getReservesList",
        "outputs": [{"name": "", "type": "address[]"}],
        "stateMutability": "view", "type": "function"
    },
    {
        "inputs": [{"name": "user", "type": "address"}],
        "name": "getUserConfiguration",
        "outputs": [{"components": [{"name": "data", "type": "uint256"}], "name": "", "type": "tuple"}],
        "stateMutability": "view", "type": "function"
    },
]

ERC20_ABI = [
    {
        "constant": True,
        "inputs": [{"name": "account", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "", "type": "uint256"}],
        "stateMutability": "view", "type": "function"
    },
    {
        "constant": True, "inputs": [], "name": "decimals",
        "outputs": [{"name": "", "type": "uint8"}],
        "stateMutability": "view", "type": "function"
    },
    {
        "constant": True, "inputs": [], "name": "symbol",
        "outputs": [{"name": "", "type": "string"}],
        "stateMutability": "view", "type": "function"
    },
]

pool = w3.eth.contract(address=Web3.to_checksum_address(AAVE_POOL), abi=POOL_ABI)

# known infra contracts (aTokens, escrows, etc.) - always excluded
KNOWN_CONTRACTS = {
    "0x2d62109243b87c4ba3ee7ba1d91b0dd0a074d7b1",  # aEthrsETH (Aave aToken for rsETH)
    "0x85d456b2dff1fd8245387c0bfb64dfb700e98ef3",  # KelpDAO rsETH OFT Adapter (bridge escrow)
}

_atoken_cache = {}
_is_contract_cache = {}
_decimals_cache = {}


def atoken_for(asset, block):
    key = (asset, block)
    if key not in _atoken_cache:
        data = pool.functions.getReserveData(Web3.to_checksum_address(asset)).call(block_identifier=block)
        _atoken_cache[key] = data[8]
    return _atoken_cache[key]


def decimals_for(asset):
    # NOTE: earlier version of this script hardcoded /10**18 which silently
    # crushed any non-18-decimal asset (USDC is 6, WBTC is 8) below the dust
    # threshold. didn't affect the KelpDAO numbers because rsETH and WETH are
    # both 18 decimals, but it was still wrong. fixed to ask the token itself.
    if asset not in _decimals_cache:
        try:
            token = w3.eth.contract(address=Web3.to_checksum_address(asset), abi=ERC20_ABI)
            _decimals_cache[asset] = token.functions.decimals().call()
        except Exception:
            _decimals_cache[asset] = 18  # fallback, but log it so I notice
            print(f"  warning: decimals() failed for {asset}, assuming 18")
    return _decimals_cache[asset]


def collateral(wallet, asset, block):
    a_token = atoken_for(asset, block)
    contract = w3.eth.contract(address=a_token, abi=ERC20_ABI)
    raw = contract.functions.balanceOf(Web3.to_checksum_address(wallet)).call(block_identifier=block)
    return raw / 10 ** decimals_for(asset)


def is_contract(address, block):
    # bytecode present = contract, not a real wallet
    key = (address, block)
    if key not in _is_contract_cache:
        code = w3.eth.get_code(Web3.to_checksum_address(address), block_identifier=block)
        _is_contract_cache[key] = len(code) > 0
    return _is_contract_cache[key]


def wallet_collateral_assets(wallet, block):
    # every collateral position for a wallet, dust filtered
    reserves = pool.functions.getReservesList().call(block_identifier=block)
    config = pool.functions.getUserConfiguration(Web3.to_checksum_address(wallet)).call(block_identifier=block)
    bitmap = config[0]

    results = []
    for i, asset in enumerate(reserves):
        # Aave v3 packs 2 bits per reserve: bit 2i = borrowing, bit 2i+1 = used as collateral
        is_collateral = (bitmap >> (2 * i + 1)) & 1
        if is_collateral:
            bal = collateral(wallet, asset, block)
            if bal > DUST_THRESHOLD:
                try:
                    symbol = w3.eth.contract(
                        address=Web3.to_checksum_address(asset), abi=ERC20_ABI
                    ).functions.symbol().call()
                except Exception:
                    symbol = "?"
                results.append((asset, symbol, bal))
    return results


def build_eoa_candidate_list(candidates_csv, block, top_n=50):
    # keeps reading rows past contracts until it actually has top_n real wallets
    eoa_wallets = []
    rows_scanned = 0

    with open(candidates_csv, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if len(eoa_wallets) >= top_n:
                break
            rows_scanned += 1
            addr = row["HolderAddress"].strip().lower()

            if addr in KNOWN_CONTRACTS:
                continue
            if is_contract(addr, block):
                continue

            eoa_wallets.append(addr)

    print(f"scanned {rows_scanned} candidates to find {len(eoa_wallets)} EOA wallets")
    return eoa_wallets


def save_wallet_list(wallets, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["wallet"])
        writer.writerows([[w] for w in wallets])
    print(f"saved {len(wallets)} EOA wallets to {path}")


def snapshot(wallets, asset, block, label):
    # single asset, quick check - not the real pipeline, just for spot checks
    rows = []
    for w in wallets:
        try:
            bal = collateral(w, asset, block)
            print(f"{w[:10]}... -> {bal}")
            rows.append({"wallet": w, "asset": asset, "block": block, "collateral": bal})
        except Exception as e:
            print(f"{w[:10]}... FAILED: {e}")

    os.makedirs("data/kelp", exist_ok=True)
    out_path = f"data/kelp/aave_{label}.csv"
    with open(out_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["wallet", "asset", "block", "collateral"])
        writer.writeheader()
        writer.writerows(rows)
    print(f"saved to {out_path}")


def snapshot_full(wallets, block, label):
    # no rows for a wallet just means no position - the master list is the
    # source of truth for who was actually checked
    rows = []
    for w in wallets:
        try:
            positions = wallet_collateral_assets(w, block)
            for asset, symbol, bal in positions:
                print(f"{w[:10]}... {symbol}: {bal}")
                rows.append({"wallet": w, "asset": asset, "symbol": symbol, "block": block, "collateral": bal})
        except Exception as e:
            print(f"{w[:10]}... FAILED: {e}")

    os.makedirs("data/kelp", exist_ok=True)
    out_path = f"data/kelp/aave_{label}.csv"
    with open(out_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["wallet", "asset", "symbol", "block", "collateral"])
        writer.writeheader()
        writer.writerows(rows)
    print(f"saved to {out_path}")


if __name__ == "__main__":
    RSETH = "0xA1290d69c65A6Fe4DF752f95823fae25cB99e5A7"
    BLOCK = 24857472  # T-7 block for KelpDAO (7 days before exploit block 24,908,285)

    # this becomes the master list, reused for the Morpho and Euler checks
    eoa_wallets = build_eoa_candidate_list(
        "data/kelp/rseth_holders_etherscan.csv",
        BLOCK,
        top_n=50,
    )
    save_wallet_list(eoa_wallets, "data/kelp/eoa_master.csv")

    print("\n--- Aave collateral for all 50 EOA candidates (full positions) ---")
    snapshot_full(eoa_wallets, BLOCK, "t7_full")
