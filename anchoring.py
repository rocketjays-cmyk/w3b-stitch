import os, json
from web3 import Web3
from dotenv import load_dotenv

load_dotenv()

L2_RPC_URL = os.getenv("L2_RPC_URL")
L1_RPC_URL = os.getenv("L1_RPC_URL", L2_RPC_URL)
PRIVATE_KEY = os.getenv("PRIVATE_KEY")
ACCOUNT_ADDRESS = os.getenv("ACCOUNT_ADDRESS")

def _w3(url: str) -> Web3:
    if not url:
        raise RuntimeError("Missing RPC URL. Set L2_RPC_URL (and L1_RPC_URL) in .env")
    w3 = Web3(Web3.HTTPProvider(url))
    if not w3.is_connected():
        raise RuntimeError(f"Web3 provider not connected: {url}")
    return w3

def _send_tx(w3: Web3, payload: dict) -> str:
    if not PRIVATE_KEY or not ACCOUNT_ADDRESS:
        raise RuntimeError("Missing PRIVATE_KEY or ACCOUNT_ADDRESS in .env")
    nonce = w3.eth.get_transaction_count(ACCOUNT_ADDRESS)
    chain_id = w3.eth.chain_id
    gas_price = w3.eth.gas_price
    tx = {
        "to": ACCOUNT_ADDRESS,
        "value": 0,
        "nonce": nonce,
        "chainId": chain_id,
        "gas": 200000,
        "gasPrice": gas_price,
        "data": w3.to_hex(text=json.dumps(payload, sort_keys=True, separators=(",", ":")))
    }
    signed = w3.eth.account.sign_transaction(tx, private_key=PRIVATE_KEY)
    tx_hash = w3.eth.send_raw_transaction(signed.rawTransaction)
    return w3.to_hex(tx_hash)

def anchor_to_l2(data: dict) -> str:
    return _send_tx(_w3(L2_RPC_URL), data)

def anchor_to_l1(data: dict) -> str:
    return _send_tx(_w3(L1_RPC_URL), data)
