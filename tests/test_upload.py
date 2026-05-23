import os
import sys
import hashlib

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from backend import Blockchain

def get_directory_fingerprint(directory_path):
    # SECURITY CHECK: Does the directory exist?
    if not os.path.exists(directory_path):
        raise FileNotFoundError(f"🚨 ALERT: Directory '{directory_path}' not found!")
        
    master_hash = hashlib.sha256()
    files_hashed = 0
    
    for root, dirs, files in os.walk(directory_path):
        for names in sorted(files):
            filepath = os.path.join(root, names)
            with open(filepath, "rb") as f:
                while chunk := f.read(4096):
                    master_hash.update(chunk)
            files_hashed += 1
            
    # SECURITY CHECK: Is the directory empty?
    if files_hashed == 0:
        raise ValueError(f"🚨 ALERT: Directory '{directory_path}' is completely empty!")
        
    return master_hash.hexdigest()

# --- SIMULATION ---
market = Blockchain()
folder_path = os.path.join(PROJECT_ROOT, "tests")

print(f"Scanning folder: {folder_path}...")
fingerprint = get_directory_fingerprint(folder_path)

print(f"Generated Integrity Seal: {fingerprint}")

# Alice registers the asset on the blockchain
market.add_transaction(
    sender="Alice_ID_999", 
    receiver="MARKET_LISTING", 
    asset_name="N-Body Simulation", 
    price=25.0
)

# We store the fingerprint in the 'State' so Bob can verify it later
market.state["N-Body Simulation"] = {
    "owner": "Alice_ID_999",
    "integrity_seal": fingerprint
}

print("\nAsset Registered Successfully!")
print(f"Current Market State: {market.state['N-Body Simulation']}")
