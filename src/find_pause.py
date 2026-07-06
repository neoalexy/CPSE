import os
from web3 import Web3
from dotenv import load_dotenv

load_dotenv()
w3 = Web3(Web3.HTTPProvider(os.getenv("ANKR_RPC_URL")))

LRT_CONFIG = "0xb6AbB489aCA4583833230F10B3A7670114D09559"
BLOCK = 24908285  # exploit block

ENUMERABLE_ABI = [
    {
        "constant": True,
        "inputs": [{"name": "role", "type": "bytes32"}],
        "name": "getRoleMemberCount",
        "outputs": [{"name": "", "type": "uint256"}],
        "stateMutability": "view", "type": "function"
    },
    {
        "constant": True,
        "inputs": [{"name": "role", "type": "bytes32"}, {"name": "index", "type": "uint256"}],
        "name": "getRoleMember",
        "outputs": [{"name": "", "type": "address"}],
        "stateMutability": "view", "type": "function"
    },
]

contract = w3.eth.contract(address=Web3.to_checksum_address(LRT_CONFIG), abi=ENUMERABLE_ABI)

ROLES = {
    "DEFAULT_ADMIN_ROLE": b"\x00" * 32,
    "MANAGER_ROLE": Web3.keccak(text="MANAGER_ROLE"),
    "ADMIN_ROLE": Web3.keccak(text="ADMIN_ROLE"),
    "OPERATOR_ROLE": Web3.keccak(text="OPERATOR_ROLE"),
    "PAUSER_ROLE": Web3.keccak(text="PAUSER_ROLE"),
    "MINTER_ROLE": Web3.keccak(text="MINTER_ROLE"),
}

found_anything = False
for name, role in ROLES.items():
    try:
        count = contract.functions.getRoleMemberCount(role).call(block_identifier=BLOCK)
        found_anything = True
        print(f"{name}: {count} member(s)")
        for i in range(count):
            print(f"  [{i}]", contract.functions.getRoleMember(role, i).call(block_identifier=BLOCK))
    except Exception as e:
        print(f"{name}: reverted ({e})")

if not found_anything:
    print("\nnot Enumerable, can't list role members this way. see findings/kelp.md")
