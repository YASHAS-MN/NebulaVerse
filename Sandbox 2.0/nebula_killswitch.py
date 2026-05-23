import subprocess
import sys
import time

# Add .env and wallet.dat to the blacklist
BLACKLIST = ["/etc/shadow", ".ssh", "/root", ".env", "wallet.dat"]

def active_protection(container_name):
    print(f"[*] Shield Active: Monitoring {container_name} in real-time...")
    
    # Use 'docker logs --follow' to stream syscalls as they happen
    proc = subprocess.Popen(
        [f"docker logs --follow {container_name}"], 
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True
    )

    for line in iter(proc.stdout.readline, b''):
        decoded_line = line.decode().lower()
        for forbidden in BLACKLIST:
            if forbidden in decoded_line and "open" in decoded_line:
                print(f"!!! CRITICAL VIOLATION: {forbidden} accessed !!!")
                print(f"[!] INITIATING EMERGENCY SHUTDOWN...")
                subprocess.run(f"docker rm -f {container_name}", shell=True)
                print(f"[X] Container {container_name} VAPORIZED. Machine is safe.")
                return "MALICIOUS (TERMINATED)"
    return "FINISHED"

if __name__ == "__main__":
    active_protection(sys.argv[1])
