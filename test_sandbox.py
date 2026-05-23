from sandbox import verify_asset
import os

test_file = "sandbox_temp/dummy_test.py"
os.makedirs("sandbox_temp", exist_ok=True)
with open(test_file, "w") as f:
    f.write('print("Hello from the Decentralized Space! Engine running.")\n')

print("Executing test inside Sandbox...")
res = verify_asset(os.path.abspath(test_file))
if res["status"] == "PASS":
    print("✓ VERIFIED")
    print("Output Log: ", res.get("checks", {}).get("docker_execution", {}).get("details", {}).get("output_log", "").strip())
else:
    print("✗ FAILED")
    print(res)
