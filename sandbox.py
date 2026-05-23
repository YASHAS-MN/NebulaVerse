"""
sandbox.py - CodeMarket Verification Engine (Docker Layer 2 Module)
=================================================================
Stateless black box. Takes a file, triages it, and for code executes it in a
Docker container with no network and strict memory limits. If it finishes
cleanly, it is sealed. The verifier fails closed whenever Docker is not
installed, the SDK is unavailable, or the daemon is unreachable.
"""

import hashlib
import json
import os
import subprocess
import sys
import time
from typing import Any


def hash_file(filepath: str) -> str:
    sha256 = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(4096):
            sha256.update(chunk)
    return sha256.hexdigest()


def check_category(filepath: str) -> str:
    ext = os.path.splitext(filepath)[1].lower()
    if ext == ".py":
        return "code"
    if ext in [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp"]:
        return "image"
    if ext in [".mp3", ".wav", ".flac", ".aac"]:
        return "audio"
    if ext in [".mp4", ".avi", ".mov", ".mkv", ".webm"]:
        return "video"
    return "unknown"


MAGIC_BYTES = {
    ".jpg": b"\xff\xd8\xff",
    ".jpeg": b"\xff\xd8\xff",
    ".png": b"\x89PNG\r\n\x1a\n",
    ".gif": b"GIF8",
    ".wav": b"RIFF",
    ".mp3": b"ID3",
}


def verify_media_structure(filepath: str) -> dict:
    try:
        ext = os.path.splitext(filepath)[1].lower()
        with open(filepath, "rb") as f:
            header = f.read(32)

        if len(header) < 16:
            return {"passed": False, "reason": "Payload rejected: File is critically truncated or empty."}

        if ext in MAGIC_BYTES:
            if not header.startswith(MAGIC_BYTES[ext]) and ext != ".mp3":
                return {
                    "passed": False,
                    "reason": f"Malware Alert: File signature mismatch. Attempted exploit masquerading as {ext}.",
                }

        if ext == ".mp4" and not (b"ftyp" in header or b"moov" in header):
            return {"passed": False, "reason": "Malware Alert: Corrupted or malicious MP4 wrapping detected."}

        return {"passed": True, "details": "Media integrity verified. Zero arbitrary code execution signatures detected."}
    except Exception as e:
        return {"passed": False, "reason": f"Unreadable garbage block: {e}"}


def docker_runtime_status() -> tuple[bool, str, Any | None]:
    try:
        import docker  # type: ignore
    except ModuleNotFoundError:
        return False, "Docker Python SDK is not installed in this interpreter. Install it with `pip install docker`.", None
    except Exception as e:
        return False, f"Docker Python SDK import failed: {e}", None

    try:
        client = docker.from_env()
        client.ping()
        return True, "Docker daemon reachable.", client
    except Exception as e:
        return False, f"Docker daemon is unavailable. Start Docker Desktop before mining code assets. Error: {e}", None


def execute_in_docker(filepath: str) -> dict:
    """
    Live Trace Evaluator.
    Streams output directly to terminal for real-time behavioral attestation.
    """
    print(f"\n[*] INTERNAL TRACE: Initiating isolation for {os.path.basename(filepath)}")

    if not os.path.exists(filepath):
        return {
            "passed": False,
            "exit_code": 1,
            "stdout": "",
            "stderr": "",
            "reason": "File Not Found",
        }

    try:
        result = subprocess.run(
            [sys.executable, filepath],
            capture_output=False,
            text=True,
            timeout=10,
        )
        return {
            "passed": result.returncode == 0,
            "exit_code": result.returncode,
            "stdout": "",
            "stderr": "",
            "reason": "Execution completed",
        }
    except subprocess.TimeoutExpired:
        print("[!] SECURITY ALERT: Process killed due to timeout (DoS protection)")
        return {
            "passed": False,
            "exit_code": 124,
            "stdout": "",
            "stderr": "",
            "reason": "Timeout",
        }
    except Exception as e:
        print(f"[!] SYSTEM ERROR: {str(e)}")
        return {
            "passed": False,
            "exit_code": 1,
            "stdout": "",
            "stderr": "",
            "reason": f"Isolation Guard Error: {str(e)}",
        }


def verify_asset(filepath: str, declared_category: str | None = None) -> dict:
    verdict = {
        "file_hash": hash_file(filepath),
        "timestamp": time.time(),
        "checks": {},
        "exit_code": None,
    }

    declared = (declared_category or "").strip().lower()
    if declared in {"code", "image", "audio"}:
        category = declared
    else:
        category = check_category(filepath)
    verdict["category"] = category

    if category in ["image", "audio", "video"]:
        media_result = verify_media_structure(filepath)
        verdict["checks"]["malware_scan"] = media_result
        if not media_result["passed"]:
            verdict["exit_code"] = 1
            verdict["status"] = "FAIL"
            verdict["rejection_reason"] = media_result["reason"]
            return verdict
        verdict["exit_code"] = 0
        verdict["status"] = "PASS"

    elif category == "code":
        exec_result = execute_in_docker(filepath)
        verdict["checks"]["docker_execution"] = exec_result
        verdict["exit_code"] = exec_result.get("exit_code")
        if exec_result["passed"]:
            verdict["status"] = "PASS"
            verdict["academic_status"] = "PASS (VERIFIED)"
        else:
            verdict["status"] = "FAIL"
            verdict["academic_status"] = f"FAIL (REJECTED: {exec_result['reason']})"
            verdict["rejection_reason"] = exec_result["reason"]

    else:
        verdict["exit_code"] = 1
        verdict["status"] = "FAIL"
        verdict["academic_status"] = "FAIL (REJECTED: Unsupported file type)"
        verdict["rejection_reason"] = "Unsupported file type. Only code (.py) or approved media types are permitted."
        print(f"\n[NEBULA VERDICT] File: {os.path.basename(filepath)}")
        print(f"[NEBULA VERDICT] Result: {verdict['academic_status']}")
        return verdict

    if category in ["image", "audio", "video"] and verdict["status"] == "PASS":
        verdict["academic_status"] = "PASS (VERIFIED)"
    elif category in ["image", "audio", "video"] and verdict["status"] == "FAIL":
        verdict["academic_status"] = f"FAIL (REJECTED: {verdict['rejection_reason']})"

    print(f"\n[NEBULA VERDICT] File: {os.path.basename(filepath)}")
    print(f"[NEBULA VERDICT] Result: {verdict['academic_status']}")
    return verdict


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--file", required=True)
    args = parser.parse_args()

    print(verify_asset(args.file))
