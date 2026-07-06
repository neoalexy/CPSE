import os
import csv
from web3 import Web3
from dotenv import load_dotenv

load_dotenv()
w3 = Web3(Web3.HTTPProvider(os.getenv("ANKR_RPC_URL")))

MORPHO_BLUE = "0xBBBBBbbBBb9cC5e90e3b3Af64bdAF62C37EEFFCb"

# Ethereum mainnet markets with rsETH as DIRECT collateral (not wrsETH, not PT-wrapped)
RSETH_MARKETS = [
    "0xeeabdcb98e9f7ec216d259a2c026bbb701971efae0b44eec79a86053f9b128b6",  # rsETH/WETH 86.0%
    "0xb7aaedc202cc26f4d714507605efdd2d03cf9f4994a814cb19bb49a513a506a8",  # rsETH/WETH 86.0%
    "0xba761af4134efb0855adfba638945f454f0a704af11fc93439e20c7c5ebab942",  # rsETH/WETH 94.5%
    "0x0188775134d3541a13801c090658734743bcfe54662b045644f8e19d31958dfa",  # rsETH/wstETH 94.5%
    "0xa72f4af2570dca1b356aa6c1e6a804d0d3df5b23bb092189776d0dc652feabb4",  # rsETH/USDA 77.0%
]

MORPHO_ABI = [
    {
        "inputs": [
            {"name": "id", "type": "bytes32"},
            {"name": "user", "type": "address"}
        ],
        "name": "position",
        "outputs": [
            {"name": "supplyShares", "type": "uint256"},
            {"name": "borrowShares", "type": "uint128"},
            {"name": "collateral", "type": "uint128"},
        ],
        "stateMutability": "view", "type": "function"
    },
    {
        "inputs": [{"name": "id", "type": "bytes32"}],
        "name": "market",
        "outputs": [
            {"name": "totalSupplyAssets", "type": "uint128"},
            {"name": "totalSupplyShares", "type": "uint128"},
            {"name": "totalBorrowAssets", "type": "uint128"},
            {"name": "totalBorrowShares", "type": "uint128"},
            {"name": "lastUpdate", "type": "uint128"},
            {"name": "fee", "type": "uint128"},
        ],
        "stateMutability": "view", "type": "function"
    },
]

morpho = w3.eth.contract(address=Web3.to_checksum_address(MORPHO_BLUE), abi=MORPHO_ABI)


def check_markets_active(block):
    # don't trust a zero position result until we know the market wasn't just empty
    print(f"\n--- market activity check at block {block} ---")
    for market_id in RSETH_MARKETS:
        try:
            data = morpho.functions.market(market_id).call(block_identifier=block)
            total_supply = data[0] / 10**18
            total_borrow = data[2] / 10**18
            print(f"{market_id[:10]}...  supply={total_supply:.4f}  borrow={total_borrow:.4f}")
        except Exception as e:
            print(f"{market_id[:10]}... FAILED: {e}")


def morpho_rseth_collateral(wallet, block):
    results = []
    for market_id in RSETH_MARKETS:
        try:
            _, _, collateral_raw = morpho.functions.position(
                market_id, Web3.to_checksum_address(wallet)
            ).call(block_identifier=block)
            if collateral_raw > 0:
                collateral = collateral_raw / 10**18
                results.append((market_id, collateral))
        except Exception as e:
            print(f"  market {market_id[:10]}... FAILED: {e}")
    return results


def snapshot_morpho(wallets, block, label):
    rows = []
    for w in wallets:
        positions = morpho_rseth_collateral(w, block)
        for market_id, bal in positions:
            print(f"{w[:10]}... market {market_id[:10]}...: {bal} rsETH")
            rows.append({"wallet": w, "market_id": market_id, "block": block, "collateral": bal})

    os.makedirs("data/kelp", exist_ok=True)
    out_path = f"data/kelp/morpho_{label}.csv"
    with open(out_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["wallet", "market_id", "block", "collateral"])
        writer.writeheader()
        writer.writerows(rows)
    print(f"saved to {out_path}")


if __name__ == "__main__":
    BLOCK = 24857472  # T-7 block for KelpDAO (same as snapshot.py)

    check_markets_active(BLOCK)

    # load the master EOA wallet list built in snapshot.py
    wallets = []
    with open("data/kelp/eoa_master.csv", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            wallets.append(row["wallet"])

    print(f"\nloaded {len(wallets)} EOA wallets from master list")
    print("--- rsETH collateral on Morpho (T-7) ---")
    snapshot_morpho(wallets, BLOCK, "t7")