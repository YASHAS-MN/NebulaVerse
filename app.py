from flask import Flask, jsonify, request, send_file, send_from_directory
from flask_cors import CORS
from nebula_node import NebulaNode
import os
import base64
import hashlib
from backend import verify_signature

app = Flask(__name__)
CORS(
    app,
    resources={
        r"/api/*": {
            "origins": [
                "http://localhost:3000",
                "http://127.0.0.1:3000",
                "http://localhost:5173",
                "http://127.0.0.1:5173",
                "http://localhost:5000",
                "http://127.0.0.1:5000",
            ]
        }
    }
)

core_node = NebulaNode(port=6000)
core_node.peers.add(("127.0.0.1", 6001))
market_chain = core_node.blockchain

UNVERIFIED_POOL = os.path.join('ipfs_storage', 'unverified')
VERIFIED_POOL = os.path.join('ipfs_storage', 'verified')
os.makedirs(UNVERIFIED_POOL, exist_ok=True)
os.makedirs(VERIFIED_POOL, exist_ok=True)

FRONTEND_DIST = os.path.join(app.root_path, 'frontend', 'out')


def derive_nebula_id(public_key_pem: str) -> str:
    normalized_pem = public_key_pem.replace('\r\n', '\n').strip()
    return f"nebula_{hashlib.sha256(normalized_pem.encode('utf-8')).hexdigest()[:12]}"


def serialize_block(block):
    return {
        "index": block.index,
        "previous_hash": block.previous_hash,
        "transactions": block.transactions,
        "timestamp": block.timestamp,
        "nonce": block.nonce,
        "hash": block.hash,
        "verification_seal": block.verification_seal,
    }


@app.route('/api/faucet', methods=['POST'])
def faucet():
    data = request.get_json()
    wallet_id = data.get('wallet_id')
    res = market_chain.claim_faucet(wallet_id)
    return jsonify(res), 200 if res["success"] else 409


@app.route('/api/balance/<wallet_id>', methods=['GET'])
def get_balance(wallet_id):
    return jsonify({"wallet_id": wallet_id, "balance": market_chain.get_balance(wallet_id)})


@app.route('/api/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"error": "No file"}), 400

    file = request.files['file']
    seller_id = (request.form.get('seller_id') or '').strip()
    asset_name = (request.form.get('asset_name') or '').strip()
    public_key_pem = request.form.get('public_key') or ''
    client_file_hash = (request.form.get('file_hash') or '').strip().lower()
    signature_hex = (request.form.get('signature') or '').strip().lower()
    declared_category = (request.form.get('category') or '').strip().lower()

    if not seller_id or not asset_name or not public_key_pem or not client_file_hash or not signature_hex:
        return jsonify({"error": "Signed upload metadata is incomplete."}), 400

    try:
        price = float(request.form.get('price'))
    except (TypeError, ValueError):
        return jsonify({"error": "Invalid price provided."}), 400

    original_filename = file.filename or asset_name
    content_type = file.content_type or 'application/octet-stream'

    file_bytes = file.read()
    actual_file_hash = hashlib.sha256(file_bytes).hexdigest()
    if actual_file_hash != client_file_hash:
        return jsonify({"error": "Identity Theft Attempt: file hash mismatch."}), 403

    derived_wallet = derive_nebula_id(public_key_pem)
    if derived_wallet != seller_id:
        return jsonify({"error": "Identity Theft Attempt: public key does not match claimed Nebula ID."}), 403

    try:
        verify_signature(public_key_pem, client_file_hash, signature_hex)
    except Exception:
        return jsonify({"error": "Security Alert: Invalid Transaction Signature."}), 403

    encoded_payload = base64.b64encode(file_bytes).decode('utf-8')

    tx_result = market_chain.add_transaction(
        sender=seller_id,
        receiver=seller_id,
        asset_name=asset_name,
        price=price,
        tx_type="mint",
        unverified_file_path="PAYLOAD",
        file_payload=encoded_payload,
        category=declared_category,
        original_filename=original_filename,
        content_type=content_type
    )
    if tx_result["success"]:
        core_node.broadcast_transaction(tx_result["tx"])

    return jsonify({"message": "Signed payload injected into Mempool. Awaiting Miner Validation."}), 200


@app.route('/api/buy', methods=['POST'])
def buy_asset():
    data = request.get_json()
    asset_name = (data.get('asset_name') or '').strip()
    buyer_id = (data.get('buyer_id') or '').strip()
    seller_id = (data.get('seller_id') or '').strip()

    try:
        price = float(data.get('price', 0))
    except (TypeError, ValueError):
        return jsonify({"error": "Invalid purchase price."}), 400

    if not asset_name or not buyer_id or not seller_id:
        return jsonify({"error": "Purchase request is incomplete."}), 400

    if asset_name not in market_chain.state:
        return jsonify({"error": "Asset not found on chain"}), 404

    asset_state = market_chain.state[asset_name]
    if asset_state.get('owner') == buyer_id:
        return jsonify({"error": "Transaction already in progress."}), 409

    if buyer_id == seller_id:
        return jsonify({"error": "You already own this asset."}), 409

    for tx in market_chain.pending_transactions:
        if tx.get("tx_type") == "purchase" and tx.get("asset_name") == asset_name and tx.get("sender") == buyer_id:
            return jsonify({"error": "Transaction already in progress."}), 409

    result = market_chain.add_transaction(
        sender=buyer_id,
        receiver=asset_state.get('owner', seller_id),
        asset_name=asset_name,
        price=price,
        tx_type="purchase"
    )
    if not result["success"]:
        return jsonify({
            "error": result.get("reason", "Purchase escrow could not be queued."),
            "reason": result.get("reason"),
            "balance": result.get("balance", 0),
            "required": price,
        }), 402

    core_node.broadcast_transaction(result["tx"])
    print(f"[GATEWAY] Queued purchase for '{asset_name}' from {buyer_id} to {seller_id} at {price} VC")
    return jsonify({"message": "Purchase escrow queued. Awaiting Miner settlement."}), 200


@app.route('/api/market_state', methods=['GET'])
def get_market_state():
    return jsonify(core_node.blockchain.state)


@app.route('/api/user_orders/<wallet_id>', methods=['GET'])
def get_user_orders(wallet_id):
    wallet_id = wallet_id.strip()
    if not wallet_id:
        return jsonify({"error": "Wallet identity is required."}), 400

    pending_orders = []
    for tx in market_chain.pending_transactions:
        if tx.get("tx_type") == "purchase" and tx.get("sender") == wallet_id:
            pending_orders.append({
                "asset_name": tx.get("asset_name"),
                "buyer_id": tx.get("sender"),
                "seller_id": tx.get("receiver"),
                "price": tx.get("price"),
                "status": "pending",
                "timestamp": tx.get("timestamp"),
                "asset": market_chain.state.get(tx.get("asset_name"), {}),
            })

    completed_orders = []
    for asset_name, asset in market_chain.state.items():
        if asset.get("owner") == wallet_id:
            completed_orders.append({
                "asset_name": asset_name,
                "owner_id": asset.get("owner"),
                "price": asset.get("price"),
                "status": "completed",
                "asset": asset,
            })

    return jsonify({
        "wallet_id": wallet_id,
        "pending_orders": pending_orders,
        "completed_orders": completed_orders,
    })


@app.route('/api/mempool', methods=['GET'])
def get_mempool():
    return jsonify({"count": len(market_chain.pending_transactions), "trades": market_chain.pending_transactions})


@app.route('/api/chain', methods=['GET'])
def get_chain():
    return jsonify({
        "length": len(market_chain.chain),
        "chain": [serialize_block(block) for block in market_chain.chain],
        "valid": market_chain.is_chain_valid(),
    })


@app.route('/api/download/<asset_name>', methods=['GET'])
def download_asset(asset_name):
    buyer_id = request.args.get('buyer_id', '').strip()

    if asset_name not in market_chain.state:
        return jsonify({"error": "Asset not found"}), 404

    asset_data = market_chain.state[asset_name]
    if not buyer_id:
        return jsonify({"error": "Wallet identity is required to download this asset."}), 401

    ledger_owner = None
    for block in reversed(market_chain.chain):
        for tx in reversed(block.transactions):
            if tx.get("asset_name") == asset_name:
                if tx.get("tx_type") in ("purchase", "mint"):
                    ledger_owner = tx.get("sender")
                    break
        if ledger_owner:
            break

    if ledger_owner != buyer_id:
        return jsonify({"error": "Only the current owner can download this verified asset."}), 403

    file_hash = asset_data['integrity_hash']
    verified_path = os.path.join(VERIFIED_POOL, file_hash)

    if not os.path.exists(verified_path):
        return jsonify({"error": "File missing from decentralized storage"}), 404

    download_name = asset_data.get('original_filename') or asset_name
    mimetype = asset_data.get('content_type') or 'application/octet-stream'
    return send_file(verified_path, as_attachment=True, download_name=download_name, mimetype=mimetype)


@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def frontend(path):
    if path.startswith('api/'):
        return jsonify({"error": "API route not found"}), 404

    if not os.path.isdir(FRONTEND_DIST):
        return jsonify({
            "error": "Frontend build not found",
            "message": "Build the Next.js frontend with `npm run build` inside the frontend directory."
        }), 503

    requested_path = os.path.join(FRONTEND_DIST, path)
    if path:
        if os.path.exists(requested_path) and os.path.isfile(requested_path):
            return send_from_directory(FRONTEND_DIST, path)

        # Handle Next.js static asset routes cleanly matching standard '.html' extensions
        html_path = requested_path + '.html'
        if os.path.exists(html_path) and os.path.isfile(html_path):
            return send_from_directory(FRONTEND_DIST, path + '.html')

        # Fallback to localized folder index handling correctly
        index_path = os.path.join(requested_path, 'index.html')
        if os.path.exists(index_path) and os.path.isfile(index_path):
            return send_from_directory(requested_path, 'index.html')

    return send_file(os.path.join(FRONTEND_DIST, 'index.html'))


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
