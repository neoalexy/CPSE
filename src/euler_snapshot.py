import os
import csv
from web3 import Web3
from dotenv import load_dotenv

load_dotenv()
w3 = Web3(Web3.HTTPProvider(os.getenv("ANKR_RPC_URL")))
EULER_USR_VAULT = "0x3A8992754E2EF51D8F90620d2766278af5C59b90"

# min USR to count as a real position
DUST_THRESHOLD = 1.0

EVAULT_ABI = [
    {
        "constant": True,
        "inputs": [{"name": "account", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "", "type": "uint256"}],
        "stateMutability": "view", "type": "function"
    },
    {
        "constant": True,
        "inputs": [{"name": "shares", "type": "uint256"}],
        "name": "convertToAssets",
        "outputs": [{"name": "", "type": "uint256"}],
        "stateMutability": "view", "type": "function"
    },
]

vault = w3.eth.contract(address=Web3.to_checksum_address(EULER_USR_VAULT), abi=EVAULT_ABI)

_is_contract_cache = {}

def is_contract(address, block):
    key = (address, block)
    if key not in _is_contract_cache:
        code = w3.eth.get_code(Web3.to_checksum_address(address), block_identifier=block)
        _is_contract_cache[key] = len(code) > 0
    return _is_contract_cache[key]


def euler_usr_collateral(wallet, block):
    # vault shares, not raw USR
    shares = vault.functions.balanceOf(Web3.to_checksum_address(wallet)).call(block_identifier=block)
    if shares == 0:
        return 0.0
    assets = vault.functions.convertToAssets(shares).call(block_identifier=block)
    result = assets / 10**18
    return result if result > DUST_THRESHOLD else 0.0


def load_wallets(path):
    wallets = []
    with open(path, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            wallets.append(row["wallet"])
    return wallets


def snapshot_euler(wallets, block, label):
    # flag contracts instead of silently counting them
    rows = []
    flagged_contracts = []
    for w in wallets:
        try:
            if is_contract(w, block):
                flagged_contracts.append(w)
                continue
            bal = euler_usr_collateral(w, block)
            if bal > 0:
                print(f"{w[:10]}... {bal} USR")
                rows.append({"wallet": w, "block": block, "collateral": bal})
        except Exception as e:
            print(f"{w[:10]}... FAILED: {e}")

    os.makedirs("data/resolv", exist_ok=True)
    out_path = f"data/resolv/euler_{label}.csv"
    with open(out_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["wallet", "block", "collateral"])
        writer.writeheader()
        writer.writerows(rows)
    print(f"\nsaved {len(rows)} positions to {out_path}")

    if flagged_contracts:
        print(f"{len(flagged_contracts)} candidate(s) were contracts, excluded:")
        for c in flagged_contracts:
            print(f"  {c}")


if __name__ == "__main__":
    BLOCK = 24659218  # T-7 block for Resolv

    # same wallets checked on Morpho - checking them on Euler is the actual test, not a fresh top-holder pull
    morpho_wallets = load_wallets("data/resolv/morpho_usr_raw.csv")

    print(f"checking {len(morpho_wallets)} Morpho USR holders against Euler USR vault (T-7)...")
    print("--- USR collateral on Euler ---")
    snapshot_euler(morpho_wallets, BLOCK, "t7")
