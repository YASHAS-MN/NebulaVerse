# tests/adversarial_samples/resource_exhaustion.py
import time

def trigger_ram_spike():
    print("[!] Attempting to exhaust system memory...")
    data = []
    try:
        while True:
            # Rapidly allocate memory
            data.append(" " * 10**7) 
    except MemoryError:
        print("[v] Sandbox successfully triggered MemoryError!")

if __name__ == "__main__":
    trigger_ram_spike()