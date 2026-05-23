# tests/adversarial_samples/network_jailbreak.py
import urllib.request

def attempt_exfiltration():
    print("[!] Attempting to connect to unauthorized external IP...")
    try:
        # Replace with a safe test URL
        response = urllib.request.urlopen("http://google.com", timeout=5)
        print("[X] FAILURE: Connection established. Sandbox is leaky!")
    except Exception as e:
        print(f"[v] SUCCESS: Connection blocked. Sandbox isolated correctly: {e}")

if __name__ == "__main__":
    attempt_exfiltration()