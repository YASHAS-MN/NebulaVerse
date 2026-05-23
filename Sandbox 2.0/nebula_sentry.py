import subprocess
import sys

# Define behaviors that cause an immediate "MALICIOUS" verdict
BLACKLIST_FILES = ["/etc/shadow", ".ssh", "/root", "wallet.dat"]

def monitor_heartbeat(container_name):
    print(f"[*] Nebula Sentry monitoring: {container_name}")
    # Run strace on the container and look for 'open' syscalls
    cmd = f"docker logs {container_name} 2>&1"
    
    try:
        output = subprocess.check_output(cmd, shell=True).decode()
        for line in output.split('\n'):
            for forbidden in BLACKLIST_FILES:
                if forbidden in line and "open" in line:
                    print(f"!!! SECURITY VIOLATION: Attempted access to {forbidden} !!!")
                    return "MALICIOUS"
        return "SAFE"
    except Exception as e:
        return f"ERROR: {str(e)}"

if __name__ == "__main__":
    # We will pass the container ID/name to this script
    verdict = monitor_heartbeat(sys.argv[1])
    print(f"[!] FINAL VERDICT: {verdict}")
