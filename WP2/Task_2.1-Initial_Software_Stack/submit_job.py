#!/usr/bin/env python3
"""
LUMI-IQ Automated Slurm Job Submitter:
1. Obtains/verifies the LEXIS OAuth token and stores it at ~/.lumi-iq/token (mode 0600).
2. Decodes JWT expiration (exp claim) to find exact remaining token validity.
3. Dynamically calculates Slurm walltime strictly less than token validity (< validity).
4. Submits the batch job to LUMI Slurm via `sbatch --time=... submit_lumi.sbatch`.
"""

import os
import sys
import time
import subprocess
import jwt
from qaas.client import QProvider

TOKEN_DIR = os.path.expanduser("~/.lumi-iq")
TOKEN_FILE = os.path.join(TOKEN_DIR, "token")
PROJECT = os.getenv("LEXIS_PROJECT", "vlq_demo_project")

def get_token_validity(token_str: str) -> int:
    """Returns remaining lifetime in seconds from JWT exp claim."""
    try:
        payload = jwt.decode(token_str, options={"verify_signature": False})
        exp = payload.get("exp", 0)
        return exp - int(time.time())
    except Exception:
        return 0

def obtain_or_load_token() -> tuple[str, int]:
    """Loads existing token from ~/.lumi-iq/token or initiates OAuth Device Flow."""
    token = os.getenv("LEXIS_TOKEN")
    
    # 1. Try reading from ~/.lumi-iq/token
    if not token and os.path.exists(TOKEN_FILE):
        try:
            with open(TOKEN_FILE, "r") as f:
                candidate = f.read().strip()
            rem = get_token_validity(candidate)
            if rem > 120:  # Has at least 2 minutes left
                print(f"Loaded existing token from {TOKEN_FILE}")
                print(f"Token is valid for: {rem} seconds ({rem // 60}m {rem % 60}s).")
                return candidate, rem
            else:
                print(f"Token in {TOKEN_FILE} is near expiry ({rem}s left). Re-authenticating...")
        except Exception as e:
            print(f"Notice: Could not read {TOKEN_FILE}: {e}")

    # 2. Authenticate interactively via OAuth Device Code Flow
    print("\n=== Initiating LEXIS Authentication (OAuth Device Code Flow) ===")
    provider = QProvider(lexis_project=PROJECT)
    token = provider._token

    if not token:
        print("ERROR: Authentication failed to obtain token.")
        sys.exit(1)

    # 3. Securely persist token with chmod 600
    os.makedirs(TOKEN_DIR, mode=0o700, exist_ok=True)
    fd = os.open(TOKEN_FILE, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with open(fd, "w") as f:
        f.write(token)
    os.chmod(TOKEN_FILE, 0o600)
    print(f"Token securely saved to {TOKEN_FILE} (permissions: 0600).")

    rem = get_token_validity(token)
    return token, rem

def main():
    print("=== LUMI-IQ Slurm Job Submitter ===")
    token, remaining_sec = obtain_or_load_token()

    if remaining_sec < 60:
        print(f"ERROR: Token validity is too short ({remaining_sec}s). Please re-run.")
        sys.exit(1)

    # Calculate safe Slurm walltime strictly less than token lifetime:
    # Subtract 60 seconds safety margin so the job completes before token expires
    safe_walltime_sec = max(60, remaining_sec - 60)
    
    # Format as HH:MM:SS for Slurm
    m, s = divmod(safe_walltime_sec, 60)
    h, m = divmod(m, 60)
    slurm_time_str = f"{h:02d}:{m:02d}:{s:02d}"

    print("\n--- Slurm Walltime Configuration ---")
    print(f"Remaining token validity: {remaining_sec}s ({remaining_sec // 60}m {remaining_sec % 60}s)")
    print(f"Configured Slurm --time : {slurm_time_str} (< token validity)")

    # Path to submit_lumi.sbatch
    script_dir = os.path.dirname(os.path.abspath(__file__))
    sbatch_script = os.path.join(script_dir, "submit_lumi.sbatch")

    cmd = [
        "sbatch",
        f"--time={slurm_time_str}",
        sbatch_script,
    ]

    print(f"\nExecuting: {' '.join(cmd)}")
    res = subprocess.run(cmd, capture_output=True, text=True)

    if res.returncode == 0:
        stdout = res.stdout.strip()
        print(f"\n[SUCCESS] {stdout}")
        job_id = stdout.split()[-1]
        print(f"Job is queued on partition 'small'.")
        print(f"Check status with: squeue -j {job_id}")
        print(f"Output log: lumi_iq_{job_id}.out")
        print(f"Error log:  lumi_iq_{job_id}.err")
    else:
        print(f"\n[ERROR] Slurm submission failed:")
        print(res.stderr)
        sys.exit(res.returncode)

if __name__ == "__main__":
    main()
