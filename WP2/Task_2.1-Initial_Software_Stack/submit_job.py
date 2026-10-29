#!/usr/bin/env python3
"""
LUMI-IQ Automated Slurm Job Submitter with Queue-Aware Lifetime Enforcement:

1. Obtains/loads the LEXIS OAuth access token at ~/.lumi-iq/token (mode 0600).
2. Decodes JWT expiration (exp claim) to determine exact remaining token lifetime.
4. Accounts for BOTH:
   - Execution walltime on the compute node (--time)
   - Wait time spent pending in the Slurm queue (--deadline)
5. Enforces the invariant:
   [Queue Wait Time] + [Execution Walltime] <= [Token Validity] - [Safety Margin]
   => Slurm --deadline is set to (Token Expiry - Safety Margin).
6. Creates a dedicated, isolated execution directory on $SCRATCH:
   - Slurm stdout/stderr logs are stored in the scratch directory.
   - Circuit measurement outputs (results.json) are stored in the scratch directory.
   - The git repository remains completely clean.
   - Creates a local symlink 'latest_run' pointing to the scratch run folder.
"""

import os
import sys
import time
import datetime
import argparse
import subprocess
import shutil
import jwt

TOKEN_DIR = os.path.expanduser("~/.lumi-iq")
TOKEN_FILE = os.path.join(TOKEN_DIR, "token")

from config import LUMI_PROJECT, LEXIS_PROJECT, LEXIS_RESOURCE
PROJECT = LEXIS_PROJECT


def get_token_validity(token_str: str) -> tuple[int, int]:
    """Returns (exp_timestamp, remaining_seconds) from JWT exp claim."""
    try:
        payload = jwt.decode(token_str, options={"verify_signature": False})
        exp = payload.get("exp", 0)
        rem = exp - int(time.time())
        return exp, rem
    except Exception:
        return 0, 0


def save_secure_file(path: str, content: str):
    """Saves string content to file with strict 0600 permissions."""
    os.makedirs(os.path.dirname(path), mode=0o700, exist_ok=True)
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with open(fd, "w") as f:
        f.write(content.strip())
    os.chmod(path, 0o600)


def obtain_or_load_token(min_required_sec: int) -> tuple[str, int, int]:
    """
    Loads existing token or initiates fresh Device Code Flow authentication.
    Ensures remaining lifetime is at least min_required_sec.
    """
    token = os.getenv("LEXIS_TOKEN")

    # 1. Try reading existing access token from ~/.lumi-iq/token
    if not token and os.path.exists(TOKEN_FILE):
        try:
            with open(TOKEN_FILE, "r") as f:
                candidate = f.read().strip()
            exp, rem = get_token_validity(candidate)
            if rem >= min_required_sec:
                print(f"Loaded existing token from {TOKEN_FILE}")
                print(f"Token is valid for: {rem}s ({rem // 60}m {rem % 60}s).")
                return candidate, exp, rem
            else:
                print(f"Saved token has expired or has only {rem}s remaining (need >= {min_required_sec}s).")
                print("Initiating re-authentication...")
        except Exception as e:
            print(f"Notice: Could not read {TOKEN_FILE}: {e}")

    # 2. Interactive OAuth 2.0 Device Code Flow (fresh re-auth)
    print("\n=== Initiating LEXIS Authentication (OAuth Device Code Flow) ===")
    from qaas.client import QProvider

    provider = QProvider(lexis_project=PROJECT)
    token = provider._token

    if not token:
        print("ERROR: Authentication failed to obtain token.")
        sys.exit(1)

    save_secure_file(TOKEN_FILE, token)
    print(f"Fresh token securely saved to {TOKEN_FILE} (permissions: 0600).")

    exp, rem = get_token_validity(token)
    return token, exp, rem


def parse_time_to_seconds(time_str: str) -> int:
    """Parses [[HH:]MM:]SS or MM:SS to seconds."""
    parts = list(map(int, time_str.split(":")))
    if len(parts) == 3:
        return parts[0] * 3600 + parts[1] * 60 + parts[2]
    elif len(parts) == 2:
        return parts[0] * 60 + parts[1]
    elif len(parts) == 1:
        return parts[0]
    raise ValueError(f"Invalid time format: {time_str}")


def resolve_scratch_base(custom_dir: str | None = None, account: str | None = None) -> str:
    """Resolves LUMI scratch directory for job runs."""
    if custom_dir:
        return os.path.abspath(custom_dir)
    account = account or LUMI_PROJECT or os.getenv("LUMI_PROJECT", "")
    user = os.environ.get("USER", os.getenv("LOGNAME", "user"))
    scratch = os.environ.get("SCRATCH")
    if scratch and os.path.exists(scratch):
        if user not in scratch:
            return os.path.join(scratch, user, "lumi-iq-jobs")
        return os.path.join(scratch, "lumi-iq-jobs")
    for candidate in [
        f"/scratch/{account}/{user}/lumi-iq-jobs",
        f"/scratch/{account}/lumi-iq-jobs",
        os.path.expanduser("~/scratch/lumi-iq-jobs"),
    ]:
        if os.path.exists(os.path.dirname(candidate)):
            return candidate
    return os.path.expanduser("~/lumi-iq-jobs")


def main():
    parser = argparse.ArgumentParser(
        description="LUMI-IQ Slurm Submitter with Queue-Aware Lifetime Enforcement & Scratch Execution"
    )
    parser.add_argument(
        "--account",
        default=LUMI_PROJECT,
        help=f"LUMI Slurm project account (default: {LUMI_PROJECT})",
    )
    parser.add_argument(
        "--use-case",
        choices=["1", "2", "3", "4", "5", "all", "bell"],
        default="bell",
        help="Target use case to run as Slurm HPC job (1, 2, 3, 4, 5, all, or bell; default: bell)",
    )
    parser.add_argument(
        "--backend",
        choices=["VLQ", "SIM"],
        default=os.getenv("LUMI_IQ_BACKEND", "VLQ"),
        help="Execution target backend: 'VLQ' (real QPU offload) or 'SIM' (simulation on compute node; default from module or VLQ)",
    )
    parser.add_argument(
        "--script",
        default=None,
        help="Custom Python script to execute inside the Slurm HPC job",
    )
    parser.add_argument(
        "--walltime",
        default=None,
        help="Job execution walltime limit HH:MM:SS (default depends on use case: 00:05:00 to 00:30:00)",
    )
    parser.add_argument(
        "--margin",
        type=int,
        default=60,
        help="Safety margin in seconds before token expiry (default: 60)",
    )
    parser.add_argument(
        "--scratch-dir",
        default=None,
        help="Base scratch directory for job outputs (default: $SCRATCH/$USER/lumi-iq-jobs)",
    )
    args = parser.parse_args()

    # Map use cases to scripts and arguments
    script_dir = os.path.dirname(os.path.abspath(__file__))
    use_case_map = {
        "bell": (os.path.join(script_dir, "vlq_bell_state.py"), "", "00:05:00"),
        "1": (os.path.join(script_dir, "use_cases/01_car_manufacturing/run_car_manufacturing.py"), f"--backend {args.backend}", "00:15:00"),
        "2": (os.path.join(script_dir, "use_cases/02_health_life_science/run_health_vqe.py"), f"--backend {args.backend}", "00:20:00"),
        "3": (os.path.join(script_dir, "use_cases/03_terrestrial_network/run_terrestrial_network.py"), f"--backend {args.backend}", "00:10:00"),
        "4": (os.path.join(script_dir, "use_cases/04_qml_time_series/run_time_series_forecasting.py"), f"--backend {args.backend}", "00:15:00"),
        "5": (os.path.join(script_dir, "use_cases/05_small_scale_qec/run_small_scale_qec.py"), f"--backend {args.backend}", "00:10:00"),
        "all": (os.path.join(script_dir, "run_all_tests.py"), f"--backend {args.backend}", "00:30:00"),
    }

    if args.script:
        target_script = os.path.abspath(args.script)
        target_args = f"--backend {args.backend}"
        default_walltime = "00:15:00"
    else:
        target_script, target_args, default_walltime = use_case_map[args.use_case]

    walltime_str = args.walltime if args.walltime else default_walltime
    walltime_sec = parse_time_to_seconds(walltime_str)
    min_required_sec = walltime_sec + args.margin

    print("=== LUMI-IQ Slurm Job Submitter ===")
    print(f"Target Workload : {'Use Case ' + args.use_case if args.use_case != 'all' else 'All Tests'} ({os.path.basename(target_script)})")
    print(f"Target Backend  : {args.backend}")
    token, exp, rem = obtain_or_load_token(min_required_sec=min_required_sec)

    now = int(time.time())
    if exp - args.margin <= now + walltime_sec:
        print(f"ERROR: Token expires too soon ({rem}s left) to guarantee {args.walltime} execution.")
        print("Please re-run to obtain a fresh token.")
        sys.exit(1)

    deadline_sec = exp - args.margin
    max_queue_sec = deadline_sec - now - walltime_sec
    deadline_dt = datetime.datetime.fromtimestamp(deadline_sec)
    deadline_iso = deadline_dt.strftime("%Y-%m-%dT%H:%M:%S")

    # Format walltime as HH:MM:SS
    m, s = divmod(walltime_sec, 60)
    h, m = divmod(m, 60)
    slurm_time_str = f"{h:02d}:{m:02d}:{s:02d}"

    # Setup dedicated execution run directory on SCRATCH
    script_dir = os.path.dirname(os.path.abspath(__file__))
    scratch_base = resolve_scratch_base(args.scratch_dir, account=args.account)
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = os.path.join(scratch_base, f"run_{timestamp}")
    os.makedirs(run_dir, exist_ok=True)

    # Copy scripts into run_dir for reproducibility and direct execution
    shutil.copy(os.path.join(script_dir, "vlq_bell_state.py"), run_dir)
    shutil.copy(os.path.join(script_dir, "config.py"), run_dir)

    # Clean up any leftover symlink in repo so git workspace stays 100% clean
    repo_link = os.path.join(script_dir, "latest_run")
    if os.path.islink(repo_link) or os.path.exists(repo_link):
        try:
            os.remove(repo_link)
        except Exception:
            pass

    # Create 'latest' symlink strictly on $SCRATCH
    scratch_latest = os.path.join(scratch_base, "latest")
    try:
        if os.path.islink(scratch_latest) or os.path.exists(scratch_latest):
            os.remove(scratch_latest)
        os.symlink(run_dir, scratch_latest)
    except Exception:
        pass

    print("\n" + "=" * 68)
    print("SLURM QUEUE WAIT & EXECUTION TIME BUDGET ENFORCEMENT")
    print("=" * 68)
    print(f"LUMI Slurm Account         : {args.account}")
    print(f"Token Expiration Timestamp : {datetime.datetime.fromtimestamp(exp).strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Total Remaining Lifetime   : {rem}s ({rem // 60}m {rem % 60}s)")
    print(f"Configured Walltime (--time): {slurm_time_str} ({walltime_sec}s)")
    print(f"Safety Margin              : {args.margin}s")
    print(f"Max Allowed Queue Delay    : {max_queue_sec}s ({max_queue_sec // 60}m {max_queue_sec % 60}s)")
    print(f"Calculated Slurm --deadline: {deadline_iso}")
    print(f"Run Directory on Scratch   : {run_dir}")
    print("-" * 68)
    print("Invariant enforced by Slurm scheduler:")
    print("  [Queue Wait Time] + [Job Execution Time] <= [Token Lifetime - Margin]")
    print(f"  If the job waits > {max_queue_sec // 60}m {max_queue_sec % 60}s in queue, Slurm automatically drops it.")
    print("=" * 68 + "\n")

    sbatch_script = os.path.join(script_dir, "submit_lumi.sbatch")
    cmd = [
        "sbatch",
        f"--account={args.account}",
        f"--chdir={run_dir}",
        f"--output={run_dir}/lumi_iq_%j.out",
        f"--error={run_dir}/lumi_iq_%j.err",
        f"--time={slurm_time_str}",
        f"--deadline={deadline_iso}",
        f"--export=ALL,TARGET_SCRIPT={target_script},TARGET_ARGS={target_args}",
        sbatch_script,
    ]

    print(f"Executing: {' '.join(cmd)}")
    res = subprocess.run(cmd, capture_output=True, text=True)

    if res.returncode == 0:
        stdout = res.stdout.strip()
        print(f"\n[SUCCESS] {stdout}")
        job_id = stdout.split()[-1]
        print(f"Job is queued on partition 'small'.")
        print(f"All files isolated to scratch: {run_dir}")
        print(f"Check status with            : squeue -j {job_id}")
        print(f"Inspect stdout               : cat {run_dir}/lumi_iq_{job_id}.out")
        print(f"Inspect stderr               : cat {run_dir}/lumi_iq_{job_id}.err")
        print(f"Results JSON (when done)     : {run_dir}/results.json")
        print(f"Scratch latest run symlink   : {scratch_latest}")
        print(f"  (e.g.: cat {scratch_latest}/lumi_iq_{job_id}.out)")
    else:
        print(f"\n[ERROR] Slurm submission failed:")
        print(res.stderr)
        sys.exit(res.returncode)


if __name__ == "__main__":
    main()
