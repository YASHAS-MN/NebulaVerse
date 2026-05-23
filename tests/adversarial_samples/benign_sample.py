# tests/adversarial_samples/benign_sample.py
import math

def calculate_pi():
    print("[+] Running benign math calculation...")
    result = sum(1/i**2 for i in range(1, 10000))
    print(f"[v] Calculation complete: {result}")

if __name__ == "__main__":
    calculate_pi()