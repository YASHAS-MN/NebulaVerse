import time
from nebula_node import NebulaNode
from wallet import Wallet
from sandbox import docker_runtime_status


class MinerDashboard:
    def __init__(self, target_ip="127.0.0.1"):
        self.target_ip = target_ip
        self.node = NebulaNode(port=6001)
        self.gateway_peer = (target_ip, 6000)
        self.node.peers.add(self.gateway_peer)
        self.wallet = Wallet()
        docker_ready, docker_message, _ = docker_runtime_status()
        self.docker_ready = docker_ready
        self.docker_message = docker_message
        print("\n" + "=" * 60)
        print("          NEBULA BLOCKCHAIN: MINER PROTOCOL (L2)         ")
        print("=" * 60)
        print(f"Miner Identity : {self.wallet.identity}")
        print(f"Network Bound  : 0.0.0.0:6001")
        print(f"Gateway Peer   : {self.gateway_peer[0]}:{self.gateway_peer[1]}")
        print(f"Docker Status  : {'READY' if self.docker_ready else 'BLOCKED'}")
        print("=" * 60)
        print(self.docker_message)
        print("=" * 60 + "\n")

    def refresh_docker_status(self):
        docker_ready, docker_message, _ = docker_runtime_status()
        self.docker_ready = docker_ready
        self.docker_message = docker_message
        return docker_ready

    def run(self):
        print("[System] Online. Press [ENTER] at any time to explicitly command the Miner to sweep the Mempool and execute Sandboxing...")
        try:
            while True:
                input("\n[P2P] Press ENTER to Execute Mine sequence -> ")
                pending = len(self.node.blockchain.pending_transactions)
                if pending > 0:
                    print(f"\n[MINER] Sweeping {pending} pending transaction(s) into the execution environment...")

                    if not self.refresh_docker_status():
                        print(f"\n[MINER] Mining aborted. {self.docker_message}")
                        continue

                    success = self.node.blockchain.mine_pending_transactions(
                        self.wallet.identity,
                        miner_private_key=self.wallet.private_key,
                        miner_public_key=self.wallet.public_key_pem,
                        miner_wallet=self.wallet,
                    )

                    if success:
                        mined_block = self.node.blockchain.get_latest_block()
                        print(
                            f"[P2P] Broadcasting block #{mined_block.index} "
                            f"to Gateway {self.gateway_peer[0]}:{self.gateway_peer[1]}..."
                        )
                        self.node.broadcast_new_block(mined_block)
                        print("\n[System] Block sealed and broadcasted to Peer Network.")
                else:
                    print("\n[System] Mempool is totally empty. Nothing to mine.")
        except KeyboardInterrupt:
            print("\n[System] Miner gracefully shutting down.")


if __name__ == "__main__":
    import sys
    target_ip = sys.argv[1] if len(sys.argv) > 1 else "127.0.0.1"
    miner = MinerDashboard(target_ip)
    miner.run()
