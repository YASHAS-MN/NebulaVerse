# CodeMarket Blockchain Prototype

## Project Snapshot
This repository is a **work-in-progress** prototype for a decentralized software marketplace.

Current structure:
- `app.py`: Flask API + web entrypoint
- `backend.py`: blockchain/block logic (currently incomplete)
- `wallet.py`: RSA wallet identity + transaction signing
- `templates/index.html`: React-based frontend UI rendered by Flask

## What Has Been Built So Far
- Flask server bootstrapped in `app.py` on port `5000`.
- Frontend route `/` renders `templates/index.html`.
- Blockchain object is instantiated globally as `market_chain`.
- API endpoints implemented in `app.py`:
  - `GET /api/chain`: returns chain data
  - `POST /api/buy`: queues a transaction into pending list
  - `GET /api/market_state`: returns current ownership state map
  - `GET /api/mine`: mines pending transactions
- Wallet support added in `wallet.py`:
  - RSA keypair generation
  - `identity` (public key export in hex)
  - `sign_transaction(...)`
- Block model + PoW mining loop added in `backend.py`:
  - hash computation with SHA-256
  - nonce-based difficulty mining
  - basic state update flow after mining

## Current Issues / Incomplete Areas
`backend.py` appears partially refactored and is currently missing required methods/functions used by `app.py`:
- `Blockchain.create_genesis_block(...)` is called but not defined.
- `Blockchain.get_latest_block(...)` is used but not defined.
- `Blockchain.add_transaction(...)` is used but not defined.
- `verify_signature(...)` is imported/called but not defined.

Because of the above, the app is expected to fail at runtime until these are implemented.

## Recommended Next Steps
1. Complete missing blockchain methods/functions in `backend.py`.
2. Add startup/runtime smoke test for Flask app.
3. Add a small `requirements.txt` and setup/run instructions.
4. Add tests for:
   - signature verification
   - transaction add + mine flow
   - state updates after mining

## Quick Run Goal (after fixes)
```powershell
python app.py
```
Then open:
- `http://127.0.0.1:5000/`

## Notes
This README is a "current status" summary based on present code in the repository.

## Requirements
- Python 3.10+
- Pillow              → pip install Pillow
- Visual C++ Runtime  → https://aka.ms/vs/17/release/vc_redist.x64.exe  (for ffprobe/video/audio verification)
- ffprobe.exe + ffmpeg.exe in project root (download from ffmpeg.org)