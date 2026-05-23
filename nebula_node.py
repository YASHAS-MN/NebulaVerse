import socket
import threading
import json
from backend import Blockchain, Block

# Hardcoded SEED NODES for P2P network discovery inside a LAN
SEED_NODES = [
    # Format: ("192.168.1.106", 6000), ("192.168.1.107", 6000)
    # Add peer IPs manually here for the local network test
]
PORT = 6000

class NebulaNode:
    def __init__(self, host='0.0.0.0', port=PORT):
        self.host = host
        self.port = port
        self.blockchain = Blockchain()
        self.peers = set(SEED_NODES)

        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.host, self.port))

        # Start listening in a background thread
        threading.Thread(target=self.listen_for_peers, daemon=True).start()
        print(f"[*] Nebula Node P2P Server initialized. Bound to {self.host}:{self.port}")

    def listen_for_peers(self):
        self.server_socket.listen(5)

        while True:
            client, address = self.server_socket.accept()
            threading.Thread(target=self.handle_client, args=(client, address), daemon=True).start()

    def handle_client(self, client_socket, address):
        try:
            # Read the full TCP payload so larger blocks are not truncated mid-transfer.
            chunks = []
            while True:
                chunk = client_socket.recv(65536)
                if not chunk:
                    break
                chunks.append(chunk)

            if chunks:
                buffer = b"".join(chunks).decode('utf-8')
                message = json.loads(buffer)
                self.process_message(message, address)

        except Exception as e:
            print(f"\n[P2P ERROR] Failed to parse incoming data from {address}: {e}")
        finally:
            client_socket.close()

    def process_message(self, message, address):
        msg_type = message.get("type")

        if msg_type == "NEW_BLOCK":
            block_data = message.get("block")
            new_block = Block(
                index=block_data["index"],
                transactions=block_data["transactions"],
                previous_hash=block_data["previous_hash"],
                nonce=block_data["nonce"],
                timestamp=block_data["timestamp"],
                verification_seal=block_data.get("verification_seal")
            )
            new_block.hash = block_data["hash"]

            latest = self.blockchain.get_latest_block()
            if self.blockchain.is_valid_block(new_block, latest):
                self.blockchain.chain.append(new_block)
                self.blockchain.update_state(new_block.transactions)
                
                # Mempool Clearance: Match by unique attributes since the Miner mutates the tx payload locally
                def tx_fingerprint(t): return f"{t.get('sender')}:{t.get('asset_name')}:{t.get('timestamp')}"
                mined_fingerprints = {tx_fingerprint(t) for t in new_block.transactions}
                
                self.blockchain.pending_transactions = [
                    tx for tx in self.blockchain.pending_transactions
                    if tx_fingerprint(tx) not in mined_fingerprints
                ]
                
                print(f"[*] Appended valid P2P block #{new_block.index} from {address[0]}")
            else:
                print(f"[*] Rejected invalid block #{new_block.index} from {address[0]}")

        elif msg_type == "NEW_TRANSACTION":
            tx = message.get("transaction")
            if tx not in self.blockchain.pending_transactions:
                self.blockchain.pending_transactions.append(tx)
                print(f"[*] Added P2P transaction to mempool: {tx.get('tx_type')}")

    def broadcast(self, message: dict):
        data = json.dumps(message).encode('utf-8')
        disconnected = set()

        for peer in list(self.peers):
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(2.0)
                s.connect((peer[0], peer[1]))
                s.sendall(data)
                s.close()
            except Exception:
                disconnected.add(peer)

        # self.peers.difference_update(disconnected) # Optional: Remove unreachable peers

    def broadcast_new_block(self, block: Block):
        message = {
            "type": "NEW_BLOCK",
            "block": {
                "index": block.index,
                "transactions": block.transactions,
                "previous_hash": block.previous_hash,
                "nonce": block.nonce,
                "timestamp": block.timestamp,
                "hash": block.hash,
                "verification_seal": block.verification_seal
            }
        }
        self.broadcast(message)

    def broadcast_transaction(self, tx: dict):
        message = {
            "type": "NEW_TRANSACTION",
            "transaction": tx
        }
        self.broadcast(message)
