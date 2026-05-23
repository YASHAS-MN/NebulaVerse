import hashlib
import time
import json
import os
import shutil
import binascii
from sandbox import verify_asset
import base64
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding

# Use the existing filesystem as simulated IPFS
STORAGE_POOL = "ipfs_storage"
UNVERIFIED_POOL = os.path.join(STORAGE_POOL, "unverified")
VERIFIED_POOL = os.path.join(STORAGE_POOL, "verified")

os.makedirs(UNVERIFIED_POOL, exist_ok=True)
os.makedirs(VERIFIED_POOL, exist_ok=True)

def verify_signature(public_key_pem, message_hash, signature_hex):
    try:
        public_key = serialization.load_pem_public_key(public_key_pem.encode("utf-8"))
        signature = bytes.fromhex(signature_hex)
        public_key.verify(
            signature,
            message_hash.encode("utf-8"),
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=32,
            ),
            hashes.SHA256(),
        )
    except (InvalidSignature, ValueError, TypeError):
        return False
    return True


def derive_nebula_id(public_key_pem):
    normalized_pem = public_key_pem.replace('\r\n', '\n').strip()
    return f"nebula_{hashlib.sha256(normalized_pem.encode('utf-8')).hexdigest()[:12]}"


def create_verdict_record(asset_name, verdict):
    return {
        "asset_name": asset_name,
        "file_hash": verdict.get("file_hash"),
        "category": verdict.get("category"),
        "exit_code": verdict.get("exit_code"),
        "status": verdict.get("status"),
    }


def serialize_verification_manifest(verdicts):
    normalized = sorted(
        verdicts,
        key=lambda verdict: (
            verdict.get("asset_name", ""),
            verdict.get("file_hash", ""),
        ),
    )
    return json.dumps(normalized, sort_keys=True, separators=(",", ":"))


def sign_verification_manifest(miner_private_key, verdicts):
    payload = serialize_verification_manifest(verdicts).encode("utf-8")
    signature = miner_private_key.sign(
        payload,
        padding.PSS(
            mgf=padding.MGF1(hashes.SHA256()),
            salt_length=32,
        ),
        hashes.SHA256(),
    )
    return signature.hex()

class Block:
    def __init__(self, index, previous_hash, transactions, timestamp=None, nonce=0, verification_seal=None):
        self.index = index
        self.previous_hash = previous_hash
        self.transactions = transactions
        self.timestamp = timestamp or time.time()
        self.nonce = nonce
        self.verification_seal = verification_seal
        self.hash = self.calculate_hash()

    def calculate_hash(self):
        block_string = json.dumps({
            "index": self.index,
            "previous_hash": self.previous_hash,
            "transactions": self.transactions,
            "timestamp": self.timestamp,
            "nonce": self.nonce,
            "verification_seal": self.verification_seal
        }, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()

class Blockchain:
    def __init__(self):
        self.chain = [self.create_genesis_block()]
        self.pending_transactions = []
        self.difficulty = 3
        # State ledger map: mapping asset_name -> data
        self.state = {}
        # Balance ledger map
        self.balances = {}

    def create_genesis_block(self):
        return Block(0, "0", [], 1600000000, 0)

    def get_latest_block(self):
        return self.chain[-1]

    def get_balance(self, wallet_id):
        return self.balances.get(wallet_id, 0.0)

    def claim_faucet(self, wallet_id):
        if self.balances.get(wallet_id, 0) == 0:
            self.balances[wallet_id] = 1000.0
            return {"success": True, "message": "1000 VC minted from Developer Faucet."}
        return {"success": False, "message": "Faucet exhausted for wallet."}

    def add_transaction(
        self,
        sender,
        receiver,
        asset_name,
        price,
        tx_type="purchase",
        unverified_file_path=None,
        file_payload=None,
        category=None,
        original_filename=None,
        content_type=None,
        signature=None,
        public_key=None,
        message_hash=None
    ):
        if signature is not None:
            if not public_key or not message_hash:
                raise ValueError("Invalid Signature")
            if derive_nebula_id(public_key) != sender:
                raise ValueError("Invalid Signature")
            if not verify_signature(public_key, message_hash, signature):
                raise ValueError("Invalid Signature")

        tx = {
            "sender": sender,
            "receiver": receiver,
            "asset_name": asset_name,
            "price": price,
            "tx_type": tx_type,
            "file_payload": file_payload,
            "category": category,
            "original_filename": original_filename,
            "content_type": content_type,
            "public_key": public_key,
            "message_hash": message_hash,
            "signature": signature,
            "timestamp": time.time()
        }

        if tx_type == "purchase":
            if self.get_balance(sender) < price:
                return {"success": False, "reason": "Insufficient VC funds for Escrow", "balance": self.get_balance(sender)}
            self.balances[sender] -= price

        self.pending_transactions.append(tx)
        return {"success": True, "tx": tx, "balance": self.get_balance(sender)}

    def update_state(self, transactions):
        for tx in transactions:
            tx_type = tx.get("tx_type")

            if tx_type == "coinbase":
                miner_address = tx.get("receiver")
                reward = float(tx.get("reward", 0))
                self.balances[miner_address] = self.balances.get(miner_address, 0.0) + reward
                continue

            if tx_type == "mint":
                asset_name = tx.get("asset_name")
                integrity_hash = tx.get("integrity_hash")
                verification_seal = tx.get("verification_seal")
                if not asset_name or not integrity_hash or not verification_seal:
                    continue

                self.state[asset_name] = {
                    "owner": tx.get("sender"),
                    "integrity_hash": integrity_hash,
                    "price": float(tx.get("price", 0)),
                    "verified": True,
                    "verification_seal": verification_seal,
                    "category": tx.get("category", "software"),
                    "original_filename": tx.get("original_filename") or asset_name,
                    "content_type": tx.get("content_type") or "application/octet-stream"
                }
                continue

            if tx_type == "purchase":
                asset_name = tx.get("asset_name")
                if asset_name not in self.state:
                    continue

                seller = tx.get("receiver")
                buyer = tx.get("sender")
                price = float(tx.get("price", 0))

                self.balances[seller] = self.balances.get(seller, 0.0) + price
                self.state[asset_name]["owner"] = buyer
                self.state[asset_name]["price"] = price

    def is_valid_block(self, block, previous_block):
        if previous_block.index + 1 != block.index:
            return False
        if previous_block.hash != block.previous_hash:
            return False
        if block.hash != block.calculate_hash():
            return False
        if block.hash[:self.difficulty] != "0" * self.difficulty:
            return False
            
        if not self.verify_block_authenticity(block):
            return False
            
        return True

    def verify_block_authenticity(self, block, miner_public_key=None):
        mint_transactions = [tx for tx in block.transactions if tx.get("tx_type") == "mint"]
        if not mint_transactions:
            return True

        if not block.verification_seal:
            return False

        if not miner_public_key:
            coinbase_tx = next((tx for tx in block.transactions if tx.get("tx_type") == "coinbase"), None)
            if not coinbase_tx:
                return False

            miner_hex_identity = coinbase_tx.get("receiver")
            try:
                miner_public_key = binascii.unhexlify(miner_hex_identity).decode("utf-8")
            except Exception:
                return False

        verdicts = []
        for tx in mint_transactions:
            tx_seal = tx.get("verification_seal")
            if tx_seal != block.verification_seal:
                return False

            verdict = {
                "asset_name": tx.get("asset_name"),
                "file_hash": tx.get("integrity_hash"),
                "category": tx.get("category"),
                "exit_code": tx.get("sandbox_exit_code"),
                "status": tx.get("sandbox_status"),
            }

            if not verdict["asset_name"] or not verdict["file_hash"] or verdict["exit_code"] is None or not verdict["status"]:
                return False

            verdicts.append(verdict)

        manifest = serialize_verification_manifest(verdicts)
        return verify_signature(miner_public_key, manifest, block.verification_seal)

    def is_chain_valid(self):
        for index in range(1, len(self.chain)):
            current = self.chain[index]
            previous = self.chain[index - 1]
            if not self.is_valid_block(current, previous):
                return False
        return True

    def mine_pending_transactions(self, miner_address, miner_private_key=None, miner_public_key=None, miner_wallet=None):
        """
        The absolute core of Layer 2. The miner verifies logic.
        """
        valid_transactions = []
        rejected_transactions = []
        verdicts = []

        coinbase = {
            "sender": "0x0000_NETWORK",
            "receiver": miner_address,
            "asset_name": "BLOCK_REWARD",
            "price": 0,
            "tx_type": "coinbase",
            "reward": 10.0
        }
        valid_transactions.append(coinbase)

        for tx in self.pending_transactions:
            if tx['tx_type'] == 'mint':
                payload = tx.get('file_payload')
                if not payload:
                    tx['miner_verdict'] = "MALFORMED_REJECTED"
                    rejected_transactions.append(tx)
                    continue

                original_filename = tx.get('original_filename') or tx['asset_name']
                _, extension = os.path.splitext(original_filename)
                if not extension:
                    extension = '.bin'

                print(f"[MINER] Decoding payload for '{tx['asset_name']}'...")
                temp_filepath = os.path.join(UNVERIFIED_POOL, f"temp_{tx['asset_name']}{extension}")
                with open(temp_filepath, "wb") as f:
                    f.write(base64.b64decode(payload))

                print(f"[MINER] Sandboxing asset '{tx['asset_name']}'...")
                asset_path = tx.get('file_path') or temp_filepath
                verdict = verify_asset(asset_path, tx.get('category'))
                tx['verification_status'] = verdict.get('academic_status', verdict.get('status'))
                tx['exit_code'] = verdict.get('exit_code')

                if verdict['status'] == 'PASS':
                    print(f"[MINER] Passed! Sealing asset.")
                    tx['integrity_hash'] = verdict['file_hash']
                    tx['category'] = verdict['category']
                    tx['sandbox_exit_code'] = verdict.get('exit_code')
                    tx['sandbox_status'] = verdict.get('status')
                    tx['miner_verdict'] = "VERIFIED_ACCEPTED"

                    verdicts.append(create_verdict_record(tx['asset_name'], verdict))

                    verified_path = os.path.join(VERIFIED_POOL, tx['integrity_hash'])
                    shutil.move(temp_filepath, verified_path)

                    tx['file_payload'] = "STORED_IN_VERIFIED_POOL"
                    valid_transactions.append(tx)
                else:
                    print(f"[SECURITY] Blocking malicious asset from ledger: {tx['asset_name']}")
                    print(f"[MINER] Rejected Asset: {verdict['rejection_reason']}")
                    tx['miner_verdict'] = "MALICIOUS_REJECTED"
                    if os.path.exists(temp_filepath):
                        os.remove(temp_filepath)
                    rejected_transactions.append(tx)

            elif tx['tx_type'] == 'purchase':
                valid_transactions.append(tx)

        if len(valid_transactions) == 1:
            print("[MINER] No actionable transactions to mine. Mempool is empty/rejected.")
            self.pending_transactions = []
            return False

        if miner_wallet is not None and miner_private_key is None:
            miner_private_key = miner_wallet.private_key
        if miner_wallet is not None and miner_public_key is None:
            miner_public_key = miner_wallet.public_key_pem

        verification_seal = (
            sign_verification_manifest(miner_private_key, verdicts)
            if miner_private_key is not None and verdicts
            else None
        )
        
        for tx in valid_transactions:
            if tx.get('tx_type') == 'mint':
                tx['verification_seal'] = verification_seal

        latest = self.get_latest_block()
        new_block = Block(latest.index + 1, latest.hash, valid_transactions, verification_seal=verification_seal)

        print("[MINER] Commencing Proof of Work...")
        while new_block.hash[:self.difficulty] != "0" * self.difficulty:
            new_block.nonce += 1
            new_block.hash = new_block.calculate_hash()

        print(f"[MINER] Block Mined! Hash: {new_block.hash}")
        self.chain.append(new_block)
        self.update_state(valid_transactions)

        self.pending_transactions = []
        return True
