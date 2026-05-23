import hashlib
import os

def calculate_directory_hash(directory_path):
    """
    Creates a unique fingerprint for an entire directory.
    If even one space is changed in any file, this hash will change.
    """
    sha256_hash = hashlib.sha256()
    
    # We walk through all files in alphabetical order to ensure consistency
    for root, dirs, files in os.walk(directory_path):
        for names in sorted(files):
            filepath = os.path.join(root, names)
            with open(filepath, "rb") as f:
                # Read files in chunks for efficiency
                while byte_block := f.read(4096):
                    sha256_hash.update(byte_block)
                    
    return sha256_hash.hexdigest()