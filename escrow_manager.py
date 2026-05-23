import json
from eth_account import Account
from eth_account.messages import encode_defunct

class SmartEscrow:
    def __init__(self):
        # --- THE ISOMORPHIC LEDGER ---
        # In a real L2, this is the blockchain state. Here, it's our RAM db.
        self.balances = {}  # Wallet Address -> NDC Tokens
        self.vaults = {}    # Asset Hash -> Vault Data
        
        # System parameters
        self.MINER_FEE_PERCENT = 0.05
        self.LISTING_STAKE = 5.0 # Fixed NDC stake to prevent Alice from uploading spam/malware

    def fund_test_wallet(self, address, amount):
        """Helper for Victus Phase: Mints initial NDC tokens for testing."""
        self.balances[address] = self.balances.get(address, 0) + amount

    def _verify_signature(self, payload_dict, signature_hex, expected_address):
        """THE GATEKEEPER: Fails the transaction if the math doesn't match."""
        # We sort keys to guarantee the JSON string hashes perfectly every time
        payload_str = json.dumps(payload_dict, sort_keys=True)
        message = encode_defunct(text=payload_str)
        
        try:
            recovered_address = Account.recover_message(message, signature=signature_hex)
            if recovered_address.lower() != expected_address.lower():
                raise PermissionError("Signature Verification Failed: Forged Identity.")
            return True
        except Exception as e:
            raise PermissionError(f"Cryptographic Error: {str(e)}")

    def list_asset(self, seller_addr, asset_hash, price, signature_hex):
        """Alice lists her file and locks her 5 NDC stake."""
        payload = {"action": "LIST", "asset_hash": asset_hash, "price": price}
        self._verify_signature(payload, signature_hex, seller_addr)

        if self.balances.get(seller_addr, 0) < self.LISTING_STAKE:
            raise ValueError("Seller has insufficient funds for the Listing Stake.")

        # Deduct stake and create vault
        self.balances[seller_addr] -= self.LISTING_STAKE
        self.vaults[asset_hash] = {
            "state": "LISTED",
            "seller": seller_addr,
            "price": price,
            "seller_stake": self.LISTING_STAKE,
            "buyer": None,
            "miner": None
        }
        print(f"[ESCROW] Asset {asset_hash[:8]}... LISTED. Stake Locked.")

    def buy_asset(self, buyer_addr, asset_hash, signature_hex):
        """Bob locks his NDC tokens into the contract."""
        vault = self.vaults.get(asset_hash)
        if not vault or vault["state"] != "LISTED":
            raise ValueError("Asset not available for purchase.")

        payload = {"action": "BUY", "asset_hash": asset_hash}
        self._verify_signature(payload, signature_hex, buyer_addr)

        if self.balances.get(buyer_addr, 0) < vault["price"]:
            raise ValueError("Buyer has insufficient NDC.")

        # Deduct Bob's money and lock the state
        self.balances[buyer_addr] -= vault["price"]
        vault["buyer"] = buyer_addr
        vault["state"] = "AWAITING_MINER"
        print(f"[ESCROW] Purchase locked by {buyer_addr[:8]}... Triggering Miner.")

    def process_crypto_seal(self, miner_addr, asset_hash, verdict, signature_hex):
        """Charlie executes the sandbox and submits the Oracle Verdict."""
        vault = self.vaults.get(asset_hash)
        if not vault or vault["state"] != "AWAITING_MINER":
            raise ValueError("Vault is not awaiting verification.")

        payload = {"action": "SEAL", "asset_hash": asset_hash, "verdict": verdict}
        self._verify_signature(payload, signature_hex, miner_addr)

        vault["miner"] = miner_addr

        if verdict == "MALICIOUS":
            # --- THE SLASHING PROTOCOL ---
            print(f"[ESCROW] ALERT! Malicious code detected by Miner {miner_addr[:8]}...")
            # 1. Refund Bob
            self.balances[vault["buyer"]] += vault["price"]
            # 2. Slash Alice's stake and give it to Charlie (The Miner)
            self.balances[miner_addr] = self.balances.get(miner_addr, 0) + vault["seller_stake"]
            vault["seller_stake"] = 0
            vault["state"] = "TERMINATED_MALICIOUS"
            print("[ESCROW] Buyer Refunded. Seller Staked Slashed and Paid to Miner.")
            
        elif verdict == "SAFE":
            vault["state"] = "AWAITING_DELIVERY"
            print(f"[ESCROW] Seal Verified. Asset is SAFE. Awaiting P2P Delivery Receipt.")

    def settle_trade(self, buyer_addr, asset_hash, signature_hex):
        """Bob's browser confirms the incoming P2P hash matches. Release the funds."""
        vault = self.vaults.get(asset_hash)
        if not vault or vault["state"] != "AWAITING_DELIVERY":
            raise ValueError("Vault is not ready for settlement.")

        payload = {"action": "RECEIPT", "asset_hash": asset_hash}
        self._verify_signature(payload, signature_hex, buyer_addr)

        # Calculate splits
        miner_fee = vault["price"] * self.MINER_FEE_PERCENT
        seller_payout = vault["price"] - miner_fee

        # Pay Alice (Purchase Price + Return her initial Stake)
        self.balances[vault["seller"]] += (seller_payout + vault["seller_stake"])
        
        # Pay Charlie
        self.balances[vault["miner"]] = self.balances.get(vault["miner"], 0) + miner_fee

        vault["state"] = "SETTLED"
        print(f"[ESCROW] Delivery Confirmed. Funds Distributed. Trade SETTLED.")


# ==========================================
# 🧪 ISOLATED TEST BED (Run this file directly)
# ==========================================
if __name__ == "__main__":
    print("--- NEBULAVERSE ESCROW SIMULATION ---")
    
    # 1. Generate real ECDSA Crypto Keys for our actors
    alice = Account.create()
    bob = Account.create()
    charlie = Account.create()

    # 2. Initialize Escrow and Mint Test Tokens
    escrow = SmartEscrow()
    escrow.fund_test_wallet(alice.address, 10.0)   # Alice has 10 NDC
    escrow.fund_test_wallet(bob.address, 100.0)    # Bob has 100 NDC
    
    asset_hash = "0x8F9a...MockHash...42B"
    price = 50.0

    print(f"\n[INITIAL BALANCES]")
    print(f"Alice (Seller): {escrow.balances[alice.address]} NDC")
    print(f"Bob (Buyer): {escrow.balances[bob.address]} NDC")
    print(f"Charlie (Miner): {escrow.balances.get(charlie.address, 0)} NDC\n")

    # --- STEP 1: ALICE LISTS ASSET ---
    list_payload = {"action": "LIST", "asset_hash": asset_hash, "price": price}
    list_sig = Account.sign_message(encode_defunct(text=json.dumps(list_payload, sort_keys=True)), alice.key).signature.hex()
    escrow.list_asset(alice.address, asset_hash, price, list_sig)

    # --- STEP 2: BOB BUYS ASSET ---
    buy_payload = {"action": "BUY", "asset_hash": asset_hash}
    buy_sig = Account.sign_message(encode_defunct(text=json.dumps(buy_payload, sort_keys=True)), bob.key).signature.hex()
    escrow.buy_asset(bob.address, asset_hash, buy_sig)

    # --- STEP 3: CHARLIE MINES THE ASSET ---
    # Try changing "SAFE" to "MALICIOUS" below to test the Slashing Game Theory!
    seal_payload = {"action": "SEAL", "asset_hash": asset_hash, "verdict": "SAFE"}
    seal_sig = Account.sign_message(encode_defunct(text=json.dumps(seal_payload, sort_keys=True)), charlie.key).signature.hex()
    escrow.process_crypto_seal(charlie.address, asset_hash, "SAFE", seal_sig)

    # --- STEP 4: BOB CONFIRMS DELIVERY ---
    receipt_payload = {"action": "RECEIPT", "asset_hash": asset_hash}
    receipt_sig = Account.sign_message(encode_defunct(text=json.dumps(receipt_payload, sort_keys=True)), bob.key).signature.hex()
    escrow.settle_trade(bob.address, asset_hash, receipt_sig)

    print(f"\n[FINAL BALANCES - SAFE VERDICT]")
    print(f"Alice (Seller): {escrow.balances[alice.address]} NDC (Earned {price * 0.95})")
    print(f"Bob (Buyer): {escrow.balances[bob.address]} NDC (Spent {price})")
    print(f"Charlie (Miner): {escrow.balances[charlie.address]} NDC (Earned {price * 0.05})")